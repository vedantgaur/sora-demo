# Autonomous Video-to-Playable World Director

A sophisticated pipeline that transforms text prompts into playable 3D environments using OpenAI's Sora API for video generation and GPT-4 Vision for intelligent 3D scene reconstruction.

## Overview

This system implements an autonomous feedback loop for creating, testing, and refining 3D worlds:

1. **Text-to-Video Generation**: Generate videos from prompts using Sora API
2. **Intelligent 3D Reconstruction**: Analyze video frames with GPT-4 Vision to generate Three.js 3D scenes
3. **Real-time Collision Detection**: Monitor object interactions with bounding box collision detection
4. **Agent-based Testing**: Simulate physics and navigation to validate scene quality
5. **Iterative Refinement**: Automatically improve prompts based on agent feedback

## Key Features

### Video Generation
- Sora API integration with real-time progress tracking
- Intelligent caching system to avoid redundant API calls
- Mock mode for development and testing
- Support for multiple video resolutions and durations

### 3D Scene Reconstruction
- GPT-4 Vision analyzes video keyframes to understand scene layout
- Generates Three.js code for any object type:
  - Natural environments (forests, landscapes)
  - Mechanical objects (catapults, vehicles, machinery)
  - Creatures and characters (people, animals)
  - Structures (buildings, bridges)
- Natural, organic object placement with clustering and randomization
- Separates static and animated objects for performance
- Real-time animation system with smooth movement

### Collision Detection
- Bounding box collision detection between all objects
- Visual markers at collision points for debugging
- Live collision count display
- Performance-optimized checking every frame

### Agent Testing
- Simulated VLA (Vision-Language-Action) agent
- Tests for physics violations, navigation issues
- Generates quality scores and feedback
- Identifies areas for improvement

## Architecture

```
sora-demo/
├── src/
│   ├── main.py                 # Flask server and orchestrator
│   ├── config.py               # Configuration management
│   ├── sora_handler.py         # Sora API integration
│   ├── scoring_module.py       # Video quality scoring
│   ├── reconstruction_module.py # 3D reconstruction (future: Gaussian Splatting)
│   ├── agent_module.py         # VLA agent simulation
│   └── prompt_reviser.py       # Automatic prompt improvement
├── static/
│   ├── script.js               # Frontend application logic
│   ├── viewer3d.js             # Three.js 3D scene management
│   └── style.css               # Modern UI styling
├── templates/
│   └── index.html              # Main application interface
└── data/
    ├── generations/            # Generated videos (cached by prompt hash)
    ├── reconstructions/        # 3D reconstruction outputs
    ├── cache/                  # API response cache
    └── samples/                # Sample videos for testing
```

## Installation

### Prerequisites
- Python 3.8+
- Node.js (for frontend development)
- FFmpeg (for video processing)
- OpenAI API key

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd sora-demo
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install FFmpeg (if not already installed):
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

5. Set environment variables:
```bash
export OPENAI_API_KEY="your-api-key-here"
export PORT=5001  # Optional, defaults to 5001
```

6. Run the application:
```bash
python src/main.py
```

7. Open browser to `http://localhost:5001`

## Usage

### Mock Mode (Development)
Uses pre-generated sample videos and simulated 3D reconstruction for testing without API costs.

1. Toggle "Use Real Sora API" OFF
2. Select video source (Demo or Sora Generated)
3. Click "Show Video"
4. Click "Reconstruct 3D World"
5. Observe collision detection in real-time
6. Run agent test for quality assessment

### Sora Mode (Production)
Generates videos via Sora API and uses GPT-4 Vision for intelligent scene reconstruction.

1. Toggle "Use Real Sora API" ON
2. Enter descriptive prompt (e.g., "A catapult launching a projectile in a medieval field")
3. Click "Generate Video"
4. Monitor progress bar during generation
5. Click "Reconstruct 3D World" when complete
6. Explore 3D scene with mouse controls
7. Monitor collision detection
8. Run agent test for validation

### 3D Viewer Controls
- **Left-click + drag**: Rotate camera
- **Right-click + drag**: Pan camera
- **Scroll wheel**: Zoom in/out
- **Collision panel**: Shows real-time collision count

### Prompt Engineering Tips

**Effective prompts include:**
- Object type and action (e.g., "catapult launching", "car driving")
- Environment details (e.g., "through a dense forest", "across a desert")
- Camera perspective (e.g., "aerial view", "close-up")
- Lighting/atmosphere (e.g., "golden hour", "foggy morning")

**Examples:**
```
Good: "A medieval catapult launching a boulder in a grassy field with scattered rocks"
Good: "A red sports car driving along a winding coastal road at sunset"
Good: "A dragon flying over a mountain range with snow-capped peaks"

Avoid: "A thing moving" (too vague)
Avoid: "Cool video" (no specifics)
```

## Configuration

Edit `src/config.py` to customize:

- `VIDEO_DURATION_SECONDS`: Video length (4, 8, or 12 seconds - Sora API requirement)
- `VIDEO_RESOLUTION`: Resolution (720x1280, 1280x720, 1024x1792, 1792x1024)
- `VIDEO_FPS`: Frames per second (default: 24)
- `NUM_TAKES_PER_GENERATION`: Number of videos per prompt (default: 1)
- `USE_MOCK`: Enable mock mode (default: True for safety)

## API Integration

### Sora API
The system uses OpenAI's Sora API for video generation with:
- Asynchronous job polling
- Real-time progress updates
- Automatic retry logic
- Intelligent caching by prompt hash

### GPT-4 Vision
Analyzes video keyframes to:
- Identify all objects and their types
- Determine spatial layout and distribution
- Generate Three.js code for scene reconstruction
- Create natural, organic object placement
- Animate moving objects with realistic motion

## Caching System

Generated videos are cached by prompt hash to:
- Reduce API costs
- Enable instant retrieval of previous generations
- Support multi-user deployment
- Maintain generation history

Cache location: `data/cache/{prompt_hash}.json`

## Deployment

### Vercel Deployment (Recommended)

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Create `vercel.json`:
```json
{
  "builds": [
    {
      "src": "src/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "src/main.py"
    }
  ],
  "env": {
    "OPENAI_API_KEY": "@openai-api-key"
  }
}
```

3. Deploy:
```bash
vercel --prod
```

4. Add environment variable in Vercel dashboard:
   - Key: `OPENAI_API_KEY`
   - Value: Your OpenAI API key

### Docker Deployment

```bash
docker build -t sora-demo .
docker run -p 5001:5001 -e OPENAI_API_KEY="your-key" sora-demo
```

## Roadmap

### Current (v1.0)
- Sora API integration
- GPT-4 Vision scene reconstruction
- Real-time collision detection
- Agent-based testing
- Caching system

### Planned (v2.0)
- **Video-Gaussian Splatting**: Replace GPT-generated scenes with actual 3D reconstruction
  - Integrate Gaussian Splatting viewer
  - Depth estimation from video frames
  - Point cloud generation and meshing
  - NeRF-based reconstruction for complex scenes
- **Multi-agent collaboration**: Multiple agents test different aspects
- **Automated prompt refinement**: Learn from agent feedback
- **Export capabilities**: GLB, USDZ, OBJ formats
- **VR/AR support**: WebXR integration

### Future (v3.0)
- Real-time video streaming during generation
- Collaborative editing interface
- Physics engine integration (Cannon.js, Ammo.js)
- Material/texture generation
- Audio synthesis and spatial audio

## Technology Stack

**Backend:**
- Python 3.8+ (Flask)
- OpenAI SDK (Sora, GPT-4o)
- OpenCV (video frame extraction)
- NumPy (numerical processing)

**Frontend:**
- Vanilla JavaScript (ES6+)
- Three.js (3D rendering)
- OrbitControls (camera navigation)
- Modern CSS (Glassmorphism, animations)

**Infrastructure:**
- Flask development server
- Vercel serverless (deployment)
- File-based caching
- SHA256 prompt hashing

## Troubleshooting

### Video not playing
- Ensure FFmpeg is installed
- Check video codec (must be H.264 for web compatibility)
- Clear browser cache and hard refresh (Cmd+Shift+R)

### Collision count always showing 0
- Check that both static and animated worlds are populated
- Verify objects have bounding boxes
- Console log errors for Three.js issues

### GPT-4 Vision returning default scene
- Verify OPENAI_API_KEY is set correctly
- Check API rate limits
- Review console logs for API errors
- Ensure video frames are being extracted properly

### Sora API errors
- Verify video duration is 4, 8, or 12 seconds
- Check resolution is supported (720x1280, 1280x720, 1024x1792, 1792x1024)
- Monitor API quota and billing

## Performance Optimization

- **Collision detection**: Runs per-frame, optimized with early exit
- **Scene updates**: Only animated objects recreated each frame
- **Memory management**: Proper disposal of geometries and materials
- **Caching**: Prevents redundant API calls
- **Lazy loading**: Videos loaded on-demand

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- OpenAI for Sora and GPT-4 Vision APIs
- Three.js community for 3D rendering tools
- Contributors and testers

## Support

For issues, questions, or contributions:
- GitHub Issues: [repository-url]/issues
- Documentation: [repository-url]/wiki
- Email: support@example.com
