"""
Main Flask application for the Sora Director.
Orchestrates the entire video-to-world pipeline.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import traceback
import json

from src.config import Config
from src.utils.logger import setup_logger, app_logger
from src.utils.file_manager import (
    generate_prompt_hash,
    create_generation_directory,
    create_reconstruction_directory,
    get_relative_url,
    save_prompt_metadata
)
from src.sora_handler import get_sora_handler
from src.scoring_module import get_video_scorer
from src.reconstruction_module import get_reconstruction_module
from src.agent_module import get_agent_module
from src.prompt_reviser import get_prompt_reviser

# Initialize Flask app
app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Enable CORS
CORS(app)

# Initialize logger
logger = setup_logger(__name__)

# Global progress tracking for video generations
# Format: {prompt_hash: {'status': 'queued|in_progress|completed|failed', 'progress': 0-100, 'message': '...'}}
generation_progress = {}

# Initialize modules
sora_handler = get_sora_handler()
video_scorer = get_video_scorer()
reconstruction_module = get_reconstruction_module()
agent_module = get_agent_module()
prompt_reviser = get_prompt_reviser()


@app.route('/')
def index():
    """Serve the main web UI."""
    return render_template('index.html', config=Config.get_info())


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'mode': 'MOCK' if Config.USE_MOCK else 'PRODUCTION',
        'version': '1.0.0'
    })


@app.route('/api/progress/<prompt_hash>')
def get_progress(prompt_hash):
    """
    Get generation progress for a specific prompt hash.
    
    Response JSON:
        {
            "status": "queued|in_progress|completed|failed",
            "progress": 0-100,
            "message": "Status message"
        }
    """
    if prompt_hash in generation_progress:
        return jsonify(generation_progress[prompt_hash])
    else:
        return jsonify({
            'status': 'not_found',
            'progress': 0,
            'message': 'Generation not found'
        }), 404


@app.route('/api/cached_prompts')
def get_cached_prompts():
    """
    Get list of all cached prompts for quick reuse.
    Returns prompts sorted by most recent first.
    """
    try:
        cache_dir = Config.DATA_ROOT / 'cache'
        
        if not cache_dir.exists():
            return jsonify({'prompts': []})
        
        prompts = []
        for cache_file in cache_dir.glob('*.json'):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    
                if data.get('success') and data.get('prompt'):
                    prompts.append({
                        'prompt': data['prompt'],
                        'hash': data['prompt_hash'],
                        'timestamp': cache_file.stat().st_mtime,
                        'mode': data.get('mode', 'UNKNOWN')
                    })
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")
                continue
        
        # Sort by timestamp (most recent first)
        prompts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        logger.info(f"Found {len(prompts)} cached prompts")
        return jsonify({'prompts': prompts, 'count': len(prompts)})
        
    except Exception as e:
        logger.error(f"Failed to get cached prompts: {e}")
        return jsonify({'error': str(e), 'prompts': []}), 500


@app.route('/api/generate', methods=['POST'])
def generate_videos():
    """
    Generate multiple video takes from a text prompt.
    
    Request JSON:
        {
            "prompt": "A robot walks down a hallway",
            "num_takes": 3  // optional
        }
    
    Response JSON:
        {
            "prompt_hash": "abc123...",
            "prompt": "A robot walks down a hallway",
            "takes": [
                {
                    "take_id": 1,
                    "video_url": "/data/generations/abc123/take_1.mp4",
                    "scores": { ... },
                    "rank": 1
                },
                ...
            ]
        }
    """
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        num_takes = data.get('num_takes', Config.NUM_TAKES_PER_GENERATION)
        use_real_api = data.get('use_real_api', False)
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        logger.info(f"Received generation request: '{prompt}' (use_real_api={use_real_api})")
        
        # Generate unique hash for this prompt
        prompt_hash = generate_prompt_hash(prompt)
        
        # Check if we have a cached generation for this prompt
        cache_file = Config.DATA_ROOT / 'cache' / f'{prompt_hash}.json'
        if cache_file.exists() and use_real_api:
            logger.info(f"✨ Found cached generation for prompt: '{prompt}'")
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    
                # Verify cached videos still exist
                all_exist = all(
                    Path(take['video_path']).exists() 
                    for take in cached_data['takes']
                )
                
                if all_exist:
                    logger.info(f"✅ Returning cached generation with {len(cached_data['takes'])} videos")
                    return jsonify({
                        **cached_data,
                        'cached': True,
                        'success': True
                    })
                else:
                    logger.warning("⚠️  Some cached videos missing, regenerating...")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load cache: {e}")
        
        # Initialize progress tracking
        generation_progress[prompt_hash] = {
            'status': 'queued',
            'progress': 0,
            'message': 'Initializing generation...'
        }
        
        # Create output directory
        output_dir = create_generation_directory(prompt_hash)
        
        # Ensure cache directory exists
        cache_dir = Config.DATA_ROOT / 'cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        save_prompt_metadata(prompt_hash, prompt, {
            'num_takes': num_takes,
            'mode': 'MOCK' if Config.USE_MOCK else 'PRODUCTION'
        })
        
        # Update progress
        generation_progress[prompt_hash] = {
            'status': 'in_progress',
            'progress': 10,
            'message': 'Starting video generation...'
        }
        
        # Generate videos (use specific handler for real/mock mode)
        if use_real_api:
            from src.sora_handler import SoraHandler
            
            # Create progress callback
            def update_progress(status, progress, message):
                generation_progress[prompt_hash] = {
                    'status': status,
                    'progress': progress,
                    'message': message
                }
            
            temp_handler = SoraHandler(use_mock=False, progress_callback=update_progress)
            video_paths = temp_handler.generate_n_takes(
                prompt=prompt,
                num_takes=num_takes,
                output_dir=output_dir
            )
        else:
            video_paths = sora_handler.generate_n_takes(
                prompt=prompt,
                num_takes=num_takes,
                output_dir=output_dir
            )
            # Mock mode completes instantly
            generation_progress[prompt_hash] = {
                'status': 'in_progress',
                'progress': 90,
                'message': 'Scoring videos...'
            }
        
        # Score each video
        takes = []
        for i, video_path in enumerate(video_paths, start=1):
            scores = video_scorer.score_video(video_path)
            
            takes.append({
                'take_id': i,
                'video_url': get_relative_url(video_path),
                'video_path': str(video_path),
                'scores': scores
            })
        
        # Rank by overall score
        takes_sorted = sorted(takes, key=lambda x: x['scores']['overall'], reverse=True)
        
        # Add rank
        for rank, take in enumerate(takes_sorted, start=1):
            take['rank'] = rank
        
        # Determine if mock was used
        actual_mode = 'REAL' if use_real_api else 'MOCK'
        # Check if any video fallback to mock by checking file size or metadata
        if use_real_api and video_paths:
            # If the first video is very small, it's likely a mock fallback
            first_video = Path(video_paths[0])
            if first_video.exists() and first_video.stat().st_size < 100000:  # Less than 100KB is likely mock
                actual_mode = 'MOCK'
        
        # Mark generation as completed
        generation_progress[prompt_hash] = {
            'status': 'completed',
            'progress': 100,
            'message': 'Generation complete!'
        }
        
        response = {
            'prompt_hash': prompt_hash,
            'prompt': prompt,
            'takes': takes_sorted,
            'mode': actual_mode,
            'success': True
        }
        
        # Save to cache if real API was used successfully
        if use_real_api and actual_mode == 'REAL':
            try:
                cache_file = Config.DATA_ROOT / 'cache' / f'{prompt_hash}.json'
                with open(cache_file, 'w') as f:
                    json.dump(response, f, indent=2)
                logger.info(f"💾 Saved generation to cache: {cache_file}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to save cache: {e}")
        
        logger.info(f"Generation complete: {len(takes)} takes created (mode: {actual_mode})")
        return jsonify(response)
    
    except Exception as e:
        # Mark generation as failed
        prompt_hash = locals().get('prompt_hash')
        if prompt_hash:
            generation_progress[prompt_hash] = {
                'status': 'failed',
                'progress': 0,
                'message': f'Generation failed: {str(e)}'
            }
        
        logger.error(f"Error in generate_videos: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/reconstruct', methods=['POST'])
def reconstruct_3d():
    """
    Reconstruct a 3D world from a video.
    
    Request JSON:
        {
            "prompt_hash": "abc123...",
            "video_path": "/path/to/video.mp4"
        }
    
    Response JSON:
        {
            "asset_url": "/data/reconstructions/abc123/output.splat",
            "asset_path": "/full/path/to/output.splat",
            "success": true
        }
    """
    try:
        data = request.get_json()
        prompt_hash = data.get('prompt_hash', '')
        video_path_str = data.get('video_path', '')
        
        if not prompt_hash or not video_path_str:
            return jsonify({'error': 'prompt_hash and video_path are required'}), 400
        
        # Handle different path formats
        # Check for web URL paths FIRST (before absolute path check)
        if video_path_str.startswith('/data/'):
            # Web URL path - strip leading slash and resolve relative to project root
            video_path = Config.DATA_ROOT.parent / video_path_str.lstrip('/')
        else:
            video_path = Path(video_path_str)
            # If it's already an absolute path, use it as-is
            if not video_path.is_absolute():
                # Relative path, resolve relative to project root
                video_path = Config.DATA_ROOT.parent / video_path_str
        
        if not video_path.exists():
            logger.error(f"Video file not found: {video_path} (original: {data.get('video_path')})")
            return jsonify({'error': f'Video file not found: {video_path}'}), 404
        
        logger.info(f"Received reconstruction request for: {video_path}")
        
        # Create reconstruction output directory
        output_dir = create_reconstruction_directory(prompt_hash)
        
        # Run reconstruction
        asset_path = reconstruction_module.run_reconstruction(
            video_path=video_path,
            output_dir=output_dir,
            format='splat'
        )
        
        response = {
            'asset_url': get_relative_url(asset_path),
            'asset_path': str(asset_path),
            'format': 'splat',
            'success': True
        }
        
        logger.info(f"Reconstruction complete: {asset_path}")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in reconstruct_3d: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/run_agent', methods=['POST'])
def run_agent_test():
    """
    Run agent testing on a 3D world.
    
    Request JSON:
        {
            "asset_path": "/path/to/asset.splat",
            "prompt": "original prompt text"
        }
    
    Response JSON:
        {
            "violations": [...],
            "metrics": {...},
            "revised_prompt": "improved prompt",
            "explanation": "Why the prompt was revised",
            "success": true
        }
    """
    try:
        data = request.get_json()
        asset_path_str = data.get('asset_path', '')
        original_prompt = data.get('prompt', '')
        
        if not asset_path_str:
            return jsonify({'error': 'asset_path is required'}), 400
        
        asset_path = Path(asset_path_str)
        
        if not asset_path.exists():
            return jsonify({'error': f'Asset file not found: {asset_path}'}), 404
        
        logger.info(f"Received agent test request for: {asset_path}")
        
        # Run agent testing
        test_results = agent_module.test_world(asset_path)
        
        violations = test_results.get('violations', [])
        metrics = test_results.get('metrics', {})
        
        # Revise prompt based on violations
        revised_prompt = original_prompt
        explanation = "No issues detected."
        
        if violations:
            revised_prompt = prompt_reviser.revise_prompt(
                original_prompt=original_prompt,
                violations=violations
            )
            
            explanation = prompt_reviser.create_revision_explanation(
                original_prompt=original_prompt,
                revised_prompt=revised_prompt,
                violations=violations
            )
        
        response = {
            'violations': violations,
            'metrics': metrics,
            'test_duration': test_results.get('test_duration', 0),
            'revised_prompt': revised_prompt,
            'explanation': explanation,
            'success': True
        }
        
        logger.info(f"Agent testing complete: {len(violations)} violations found")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in run_agent_test: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/analyze_prompt', methods=['POST'])
def analyze_prompt():
    """
    Analyze a prompt for quality and completeness.
    
    Request JSON:
        {
            "prompt": "A robot walks"
        }
    
    Response JSON:
        {
            "analysis": {...},
            "suggestions": [...],
            "success": true
        }
    """
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        analysis = prompt_reviser.analyze_prompt_quality(prompt)
        
        return jsonify({
            'analysis': analysis,
            'success': True
        })
    
    except Exception as e:
        logger.error(f"Error in analyze_prompt: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/data/<path:filepath>')
def serve_data(filepath):
    """Serve generated data files (videos, 3D assets)."""
    try:
        return send_from_directory(Config.DATA_ROOT, filepath)
    except Exception as e:
        logger.error(f"Error serving file {filepath}: {e}")
        return jsonify({'error': 'File not found'}), 404


@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    """
    Handle video file uploads for mock mode testing.
    Allows users to upload their own videos to test 3D reconstruction.
    """
    logger.info("Received video upload request")
    
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Import secure_filename
        from werkzeug.utils import secure_filename
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_dir = Config.DATA_ROOT / 'uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = upload_dir / filename
        file.save(str(filepath))
        
        logger.info(f"Video uploaded successfully: {filename}")
        
        # Return file info
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': str(filepath),
            'url': f'/files/uploads/{filename}'
        })
        
    except Exception as e:
        logger.error(f"Video upload failed: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate_scene_depth', methods=['POST'])
def generate_scene_with_depth():
    """
    Generate 3D point cloud from video using depth estimation (MiDaS).
    Lightweight alternative to GPT-4 Vision code generation.
    """
    try:
        data = request.get_json()
        video_path = data.get('video_path')
        max_points = data.get('max_points', 10000)  # Limit for performance
        
        logger.info("=" * 60)
        logger.info("3D DEPTH RECONSTRUCTION")
        logger.info("=" * 60)
        logger.info(f"Video: {video_path}")
        logger.info(f"Max points: {max_points}")
        
        # Generate point cloud from depth
        point_cloud = generate_point_cloud_from_video(video_path, max_points)
        
        logger.info(f"Generated {len(point_cloud)} points")
        logger.info("Depth reconstruction complete")
        logger.info("=" * 60)
        
        return jsonify({
            'success': True,
            'points': point_cloud,
            'source': 'depth_estimation',
            'count': len(point_cloud)
        })
        
    except Exception as e:
        logger.error(f"Depth reconstruction failed: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'points': []
        }), 500


@app.route('/api/generate_scene', methods=['POST'])
def generate_scene():
    """
    Use GPT-4 Vision to analyze video frames and generate a 3D scene.
    Extracts frames, analyzes them, and creates scene code.
    """
    logger.info("=" * 60)
    logger.info("🎬 STARTING 3D SCENE GENERATION")
    logger.info("=" * 60)
    
    try:
        data = request.get_json()
        video_path = data.get('video_path', '')
        prompt = data.get('prompt', '')
        frame_count = data.get('frame_count', 3)
        
        logger.info(f"📹 Video path: {video_path}")
        logger.info(f"🎯 Prompt: {prompt}")
        logger.info(f"🖼️  Frame count: {frame_count}")
        
        if not video_path:
            logger.error("❌ No video path provided")
            return jsonify({'error': 'No video path provided'}), 400
        
        # Check if OpenAI API key is available
        if not Config.SORA_API_KEY:
            logger.warning("⚠️  OpenAI API key not set")
            logger.warning("⚠️  Using default hardcoded scene (ball + cubes)")
            logger.warning("⚠️  To use GPT-4 Vision: Set OPENAI_API_KEY environment variable")
            logger.info("🔧 Returning default scene...")
            return jsonify({
                'success': True,
                'scene': get_default_scene(),
                'source': 'default'
            })
        
        # Extract keyframes from video
        logger.info(f"🔍 Extracting {frame_count} keyframes from video...")
        frames = extract_video_keyframes(video_path, frame_count)
        
        if not frames:
            logger.error("❌ Failed to extract frames from video")
            logger.warning("⚠️  Falling back to default scene")
            return jsonify({
                'success': True,
                'scene': get_default_scene(),
                'source': 'default_fallback'
            })
        
        logger.info(f"✅ Extracted {len(frames)} frames successfully")
        
        # Use GPT-4 Vision to analyze frames and generate scene
        logger.info("🤖 Calling GPT-4 Vision API...")
        import openai
        openai.api_key = Config.SORA_API_KEY
        
        # Prepare frame data for GPT-4 Vision
        frame_messages = []
        for i, frame_b64 in enumerate(frames):
            logger.info(f"  📸 Frame {i+1}/{len(frames)}: {len(frame_b64)} bytes")
            frame_messages.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{frame_b64}",
                    "detail": "high"
                }
            })
        
        logger.info(f"🚀 Sending {len(frames)} frames to GPT-4 Vision for analysis...")
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are a 3D scene reconstruction expert. Analyze video frames and generate THREE.JS CODE that recreates ANY scene type - natural environments, mechanical objects (catapults, vehicles), creatures, buildings, abstract forms, etc.

CRITICAL REQUIREMENTS:
1. Include ALL objects from the video with accurate object types and geometries
2. Use NATURAL, ORGANIC placement with random offsets and clustering (NO systematic grids)
3. Separate STATIC objects (environment) from ANIMATED objects (moving entities)
4. Support ANY object: vehicles (composite geometries), catapults (Box+Cylinder), creatures (articulated groups), buildings, etc.
5. Match real-world scale: humans ~1.8 units, trees 3-8 units, vehicles 2-4 units

Your response must be ONLY valid JSON in this exact format:
{
  "analysis": "Brief description of the scene, ALL objects/characters, and their movement",
  "code": "Complete Three.js code. Return as string with \\n for newlines."
}

The code MUST return an object with TWO properties:
{
  staticObjects: [],   // Objects that NEVER move (created once)
  updateFunction: function(time) { return []; }  // Returns animated objects with updated positions
}

CODE TEMPLATE:
// STATIC OBJECTS (created once, never change)
const staticObjects = [];

// Ground
const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(30, 30),
  new THREE.MeshStandardMaterial({ color: 0x8B7355 })
);
ground.rotation.x = -Math.PI / 2;
staticObjects.push(ground);

// Trees/Objects (NATURAL placement with random offsets and clustering)
// Example: For a forest, distribute trees naturally
const treePositions = [
  [-6, 0, -3], [-4.5, 0, -5], [-7, 0, -7], [-3, 0, -4.5], [-8, 0, -2],
  [5, 0, -4], [6.5, 0, -6], [4, 0, -3], [7, 0, -5.5], [3.5, 0, -7]
];
treePositions.forEach(([x, y, z]) => {
  const tree = new THREE.Group();
  const trunk = new THREE.Mesh(
    new THREE.CylinderGeometry(0.2 + Math.random() * 0.1, 0.3, 2.5 + Math.random()),
    new THREE.MeshStandardMaterial({ color: 0x4a3520 })
  );
  trunk.position.y = 1.5;
  tree.add(trunk);
  const leaves = new THREE.Mesh(
    new THREE.SphereGeometry(1.2 + Math.random() * 0.6),
    new THREE.MeshStandardMaterial({ color: 0x2d5016 })
  );
  leaves.position.y = 3 + Math.random();
  tree.add(leaves);
  tree.position.set(x + (Math.random() - 0.5) * 0.5, y, z + (Math.random() - 0.5) * 0.5);
  tree.rotation.y = Math.random() * Math.PI * 2;
  staticObjects.push(tree);
});

// UPDATE FUNCTION (called every frame for animations)
function updateFunction(time) {
  const animatedObjects = [];
  
  // Walking person (only update position, don't recreate)
  const person = new THREE.Group();
  const body = new THREE.Mesh(
    new THREE.BoxGeometry(0.5, 1.5, 0.3),
    new THREE.MeshStandardMaterial({ color: 0x333333 })
  );
  body.position.y = 0.75;
  person.add(body);
  
  // ANIMATE: smooth walking motion
  person.position.x = -10 + (time * 1.5) % 20;  // Walk across scene
  person.position.z = 0;
  animatedObjects.push(person);
  
  return animatedObjects;
}

return { staticObjects, updateFunction };"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Original prompt: '{prompt}'

Analyze these {len(frames)} video frames and reconstruct the 3D scene:

SPATIAL ANALYSIS:
1. Identify ALL object types (natural: trees/rocks, mechanical: catapults/vehicles, creatures: animals/people, structures: buildings)
2. Note SPATIAL DISTRIBUTION - are objects clustered naturally or spread out? On both sides or one side?
3. Observe MOVEMENT PATTERNS - paths, trajectories, speeds, directions
4. Study DEPTH and LAYERING - foreground, midground, background elements
5. Match SCALE and PROPORTIONS

PLACEMENT RULES:
- Natural objects: Random clustering with organic variation in size/rotation
- Mechanical objects: Use composite geometries (catapult = base + arm + counterweight)
- Creatures: Articulated groups with realistic body proportions
- Use scattered positions with slight random offsets for organic feel
- NO GRIDS or systematic patterns - distribute naturally based on what you see

Generate code that recreates this specific scene:"""
                        },
                        *frame_messages
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content
        logger.info("✅ Received response from GPT-4 Vision")
        logger.info(f"📝 Response preview: {result[:200]}...")
        
        # Parse the response
        import json
        import re
        
        # Try to extract JSON from response
        logger.info("🔧 Parsing JSON response...")
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            scene_data = json.loads(json_match.group())
        else:
            scene_data = json.loads(result)
        
        logger.info("✅ Successfully parsed scene data")
        logger.info(f"📊 Analysis: {scene_data.get('analysis', 'N/A')[:100]}...")
        logger.info(f"💻 Code length: {len(scene_data.get('code', ''))} characters")
        logger.info("🎉 Scene generation complete - returning to client")
        logger.info("=" * 60)
        
        return jsonify({
            'success': True,
            'scene': scene_data,
            'source': 'gpt4_vision'
        })
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ Scene generation failed: {e}")
        logger.error(traceback.format_exc())
        # Fall back to default scene
        return jsonify({
            'success': True,
            'scene': get_default_scene(),
            'source': 'default_fallback'
        })


def generate_point_cloud_from_video(video_path, max_points=10000):
    """
    Generate 3D point cloud from video using depth estimation.
    Uses MiDaS for lightweight depth estimation (POC/MVP quality).
    
    Args:
        video_path: Path to video file
        max_points: Maximum number of points to return (for performance)
    
    Returns:
        List of points: [{'x': float, 'y': float, 'z': float, 'r': int, 'g': int, 'b': int}, ...]
    """
    try:
        import cv2
        import numpy as np
        from pathlib import Path
        
        # Try to use MiDaS for depth estimation
        use_midas = False
        try:
            import torch
            use_midas = True
            logger.info("MiDaS available - using depth estimation")
        except ImportError:
            logger.warning("PyTorch not available - using simple depth approximation")
        
        # Handle path resolution
        video_path_obj = Path(video_path)
        if video_path_obj.is_absolute() and video_path_obj.exists():
            video_path = video_path_obj
        elif isinstance(video_path, str) and video_path.startswith('/data/'):
            video_path = Config.DATA_ROOT.parent / video_path.lstrip('/')
        else:
            video_path = Config.DATA_ROOT.parent / str(video_path)
        
        logger.info(f"Loading video: {video_path}")
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Extract middle frame for depth estimation
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        middle_frame = total_frames // 2
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise ValueError("Could not read frame from video")
        
        # Resize for performance
        target_width = 640
        h, w = frame.shape[:2]
        scale = target_width / w
        frame = cv2.resize(frame, (target_width, int(h * scale)))
        
        # Estimate depth
        if use_midas:
            depth = estimate_depth_midas(frame)
        else:
            depth = estimate_depth_simple(frame)
        
        # Convert depth to point cloud
        points = depth_to_pointcloud(frame, depth, max_points)
        
        logger.info(f"Created point cloud with {len(points)} points")
        return points
        
    except Exception as e:
        logger.error(f"Point cloud generation failed: {e}")
        traceback.print_exc()
        # Return empty point cloud
        return []


def estimate_depth_midas(frame):
    """
    Estimate depth using MiDaS (lightweight POC version).
    Uses MiDaS Small model for speed.
    """
    import torch
    import cv2
    import numpy as np
    
    # Load MiDaS model (cached after first load)
    if not hasattr(estimate_depth_midas, 'model'):
        logger.info("Loading MiDaS Small model...")
        model_type = "MiDaS_small"  # Lightweight for POC
        estimate_depth_midas.model = torch.hub.load("intel-isl/MiDaS", model_type, trust_repo=True)
        estimate_depth_midas.model.eval()
        
        midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
        if model_type == "MiDaS_small":
            estimate_depth_midas.transform = midas_transforms.small_transform
        else:
            estimate_depth_midas.transform = midas_transforms.dpt_transform
        
        logger.info("MiDaS model loaded")
    
    # Prepare input
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    input_batch = estimate_depth_midas.transform(img_rgb)
    
    # Predict depth
    with torch.no_grad():
        prediction = estimate_depth_midas.model(input_batch)
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=img_rgb.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()
    
    depth = prediction.cpu().numpy()
    
    # Normalize to 0-1
    depth = (depth - depth.min()) / (depth.max() - depth.min())
    
    return depth


def estimate_depth_simple(frame):
    """
    Simple depth approximation without ML (fallback).
    Uses edge detection and blur as a rough depth proxy.
    """
    import cv2
    import numpy as np
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    depth = cv2.GaussianBlur(edges.astype(np.float32), (21, 21), 0)
    depth = depth / depth.max() if depth.max() > 0 else depth
    
    return depth


def depth_to_pointcloud(frame, depth, max_points=10000):
    """
    Convert depth map and RGB frame to 3D point cloud.
    
    Args:
        frame: RGB frame (numpy array)
        depth: Depth map (numpy array, 0-1 normalized)
        max_points: Maximum number of points to return
    
    Returns:
        List of point dictionaries with x, y, z, r, g, b
    """
    import numpy as np
    
    h, w = depth.shape
    
    # Create camera intrinsics (approximate)
    fx = fy = w  # Focal length approximation
    cx, cy = w / 2, h / 2
    
    # Sample points uniformly
    step = max(1, int(np.sqrt((h * w) / max_points)))
    
    points = []
    for y in range(0, h, step):
        for x in range(0, w, step):
            z = float(depth[y, x])
            
            # Skip points with no depth
            if z < 0.01:
                continue
            
            # Backproject to 3D
            # Invert depth so closer objects have larger z
            z_3d = (1.0 - z) * 10.0  # Scale to reasonable range
            x_3d = (x - cx) * z_3d / fx
            y_3d = (cy - y) * z_3d / fy  # Flip Y for 3D coordinates
            
            # Get color
            b, g, r = frame[y, x]
            
            points.append({
                'x': float(x_3d),
                'y': float(y_3d),
                'z': float(z_3d),
                'r': int(r),
                'g': int(g),
                'b': int(b)
            })
    
    return points


def extract_video_keyframes(video_path, frame_count=3):
    """Extract evenly distributed frames from video as base64 encoded JPEGs.
    
    Args:
        video_path: Path to video file
        frame_count: Number of frames to extract (min 2)
    """
    try:
        import cv2
        import base64
        from pathlib import Path
        
        # Handle different path formats
        video_path_obj = Path(video_path)
        
        # Check if it's already an absolute filesystem path
        if video_path_obj.is_absolute() and video_path_obj.exists():
            # Already a valid absolute path, use as-is
            video_path = video_path_obj
        elif isinstance(video_path, str) and video_path.startswith('/data/'):
            # This is a web URL path, strip leading slash and resolve relative to project root
            video_path = Config.DATA_ROOT.parent / video_path.lstrip('/')
        else:
            # Relative path, resolve relative to project root
            video_path = Config.DATA_ROOT.parent / str(video_path)
        
        logger.info(f"🎥 Reading video from: {video_path}")
        cap = cv2.VideoCapture(str(video_path))
        frames = []
        
        # Get total frame count
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames == 0:
            logger.warning("Video has no frames")
            return []
        
        # Ensure frame_count is at least 2
        frame_count = max(2, min(frame_count, total_frames))
        
        # Calculate frame indices to extract
        if frame_count == 2:
            # First and last
            frame_indices = [0, total_frames - 1]
        else:
            # Evenly distributed including first and last
            frame_indices = [int(i * (total_frames - 1) / (frame_count - 1)) for i in range(frame_count)]
        
        logger.info(f"Extracting {frame_count} frames at indices: {frame_indices}")
        
        # Extract frames
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                frames.append(base64.b64encode(buffer).decode('utf-8'))
        
        cap.release()
        logger.info(f"Successfully extracted {len(frames)} keyframes")
        return frames
        
    except Exception as e:
        logger.error(f"Failed to extract frames: {e}")
        return []


def get_default_scene():
    """Return a default scene configuration."""
    return {
        "objects": [
            {"type": "box", "position": [-3, 0.5, -3], "scale": [1, 1, 1], "color": "0xff6b6b", "name": "Red Cube"},
            {"type": "sphere", "position": [0, 1, -4], "scale": [0.8, 0.8, 0.8], "color": "0x4ecdc4", "name": "Cyan Sphere"},
            {"type": "box", "position": [3, 0.5, -3], "scale": [1, 1, 1], "color": "0xffe66d", "name": "Yellow Cube"},
            {"type": "cylinder", "position": [0, 0.5, 0], "scale": [0.5, 1, 0.5], "color": "0x95e1d3", "name": "Teal Cylinder"}
        ]
    }


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500


def main():
    """Run the Flask application."""
    app_logger.info("=" * 60)
    app_logger.info("Starting Sora Director Application")
    app_logger.info("=" * 60)
    app_logger.info(f"Mode: {'MOCK' if Config.USE_MOCK else 'PRODUCTION'}")
    app_logger.info(f"Host: {Config.HOST}:{Config.PORT}")
    app_logger.info(f"Debug: {Config.FLASK_DEBUG}")
    app_logger.info(f"Data Root: {Config.DATA_ROOT}")
    app_logger.info("=" * 60)
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.FLASK_DEBUG
    )


if __name__ == '__main__':
    main()

