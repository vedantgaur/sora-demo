# Video-Gaussian Splatting Integration Guide

## Overview

This document outlines the path to implementing full video-Gaussian splatting reconstruction for the Sora Director project. This will replace the current GPT-4 Vision code generation with actual 3D reconstruction from video.

## Current Implementation

**Status:** Foundation in place
**Method:** GPT-4 Vision generates Three.js code from video keyframes
**Quality:** Good for demonstrations, limited by code generation accuracy
**Files:** `src/reconstruction_module.py` has depth extraction and point cloud generation stubs

## Target Implementation

**Goal:** Actual 3D reconstruction using Gaussian Splatting or NeRF
**Method:** Video frames → Depth estimation → Point cloud → Gaussian Splats
**Quality:** Photo-realistic 3D reconstruction
**Output:** .splat, .ply, or .glb files viewable in Three.js

## Implementation Roadmap

### Phase 1: Depth Estimation (2-3 days)

**Integrate MiDaS or ZoeDepth for monocular depth estimation**

1. Install depth estimation model:
```bash
pip install torch torchvision
pip install timm
```

2. Download MiDaS weights:
```python
import torch
model_type = "DPT_Large"
midas = torch.hub.load("intel-isl/MiDaS", model_type)
```

3. Update `_estimate_depth` in `reconstruction_module.py`:
```python
def _estimate_depth(self, frame):
    import torch
    import cv2
    
    # Load MiDaS model
    if not hasattr(self, 'depth_model'):
        self.depth_model = torch.hub.load("intel-isl/MiDaS", "DPT_Large")
        self.depth_model.eval()
        
        if torch.cuda.is_available():
            self.depth_model.cuda()
    
    # Preprocess
    midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
    transform = midas_transforms.dpt_transform
    
    input_batch = transform(frame).unsqueeze(0)
    
    if torch.cuda.is_available():
        input_batch = input_batch.cuda()
    
    # Predict depth
    with torch.no_grad():
        prediction = self.depth_model(input_batch)
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=frame.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()
    
    depth = prediction.cpu().numpy()
    return depth
```

**Alternative:** Use commercial API like Luma AI for instant depth estimation

### Phase 2: Point Cloud Generation (3-5 days)

**Convert depth maps + camera poses to 3D point clouds**

1. Install Open3D:
```bash
pip install open3d
```

2. Implement depth to point cloud conversion:
```python
def _depth_to_pointcloud(self, depth_maps: list, output_path: Path):
    import cv2
    import numpy as np
    import open3d as o3d
    
    all_points = []
    all_colors = []
    
    for depth_path in depth_maps:
        # Load depth map
        depth = cv2.imread(str(depth_path), cv2.IMREAD_UNCHANGED)
        
        # Load corresponding RGB frame
        rgb_path = depth_path.parent.parent / "frames" / depth_path.name
        rgb = cv2.imread(str(rgb_path))
        rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
        
        # Create point cloud
        h, w = depth.shape
        fx = fy = w  # Approximate focal length
        cx, cy = w / 2, h / 2
        
        # Create meshgrid
        x, y = np.meshgrid(np.arange(w), np.arange(h))
        
        # Backproject to 3D
        z = depth.astype(np.float32)
        x3d = (x - cx) * z / fx
        y3d = (y - cy) * z / fy
        z3d = z
        
        # Stack coordinates
        points = np.stack([x3d, y3d, z3d], axis=-1).reshape(-1, 3)
        colors = rgb.reshape(-1, 3) / 255.0
        
        # Filter invalid points
        valid = z.reshape(-1) > 0
        points = points[valid]
        colors = colors[valid]
        
        all_points.append(points)
        all_colors.append(colors)
    
    # Merge all point clouds
    merged_points = np.vstack(all_points)
    merged_colors = np.vstack(all_colors)
    
    # Create Open3D point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(merged_points)
    pcd.colors = o3d.utility.Vector3dVector(merged_colors)
    
    # Estimate normals
    pcd.estimate_normals()
    
    # Save
    o3d.io.write_point_cloud(str(output_path), pcd)
```

### Phase 3: Gaussian Splatting Training (5-7 days)

**Train Gaussian Splatting representation from point cloud**

1. Install Gaussian Splatting:
```bash
git clone https://github.com/graphdeco-inria/gaussian-splatting.git
cd gaussian-splatting
pip install -r requirements.txt
```

2. Integrate training pipeline:
```python
def gaussian_splatting_reconstruction(self, video_path: Path, output_path: Path) -> Path:
    # Extract frames
    frames_dir = output_path.parent / "frames"
    self._extract_frames(video_path, frames_dir)
    
    # Extract depth maps
    depth_dir = output_path.parent / "depth_maps"
    depth_maps = self.extract_depth_maps(video_path, depth_dir)
    
    # Estimate camera poses (COLMAP or manual)
    poses = self._estimate_camera_poses(frames_dir)
    
    # Generate initial point cloud
    point_cloud_path = output_path.parent / "point_cloud.ply"
    self._depth_to_pointcloud(depth_maps, point_cloud_path)
    
    # Run Gaussian Splatting training
    splat_path = self._train_gaussian_splatting(
        point_cloud_path,
        frames_dir,
        poses,
        output_path
    )
    
    return splat_path

def _train_gaussian_splatting(self, pcd_path, images_dir, poses, output_path):
    import subprocess
    
    # Convert to Gaussian Splatting format
    gs_workspace = output_path.parent / "gaussian_splatting"
    gs_workspace.mkdir(exist_ok=True)
    
    # Run training
    cmd = [
        "python", "train.py",
        "-s", str(gs_workspace),
        "-m", str(output_path.parent),
        "--iterations", "7000",
        "--test_iterations", "7000",
        "--save_iterations", "7000",
        "--checkpoint_iterations", "7000"
    ]
    
    subprocess.run(cmd, cwd="gaussian-splatting", check=True)
    
    # Export to .splat format
    splat_path = output_path.parent / "scene.splat"
    self._export_splat(output_path.parent / "point_cloud.ply", splat_path)
    
    return splat_path
```

### Phase 4: Viewer Integration (2-3 days)

**Display Gaussian Splats in Three.js viewer**

1. Install Gaussian Splat viewer:
```html
<script src="https://cdn.jsdelivr.net/npm/gsplat@latest/dist/gsplat.min.js"></script>
```

2. Update `viewer3d.js`:
```javascript
async loadGaussianSplat(splatPath) {
    const loader = new GaussianSplatLoader();
    const splat = await loader.loadAsync(splatPath);
    
    this.scene.add(splat);
    
    // Set up renderer for Gaussian Splatting
    this.renderer.sortObjects = false;
    this.renderer.outputEncoding = THREE.sRGBEncoding;
    
    console.log('Gaussian Splat loaded:', splatPath);
}
```

3. Alternative: Use Luma AI Gaussian Splat viewer:
```javascript
import { LumaSplatsThree } from '@lumaai/luma-web';

const splat = new LumaSplatsThree({
    source: splatPath,
    enableThreeShaderIntegration: true
});

this.scene.add(splat);
```

## Alternative Approaches

### Option 1: Commercial APIs (Fastest)

**Luma AI:**
```python
import requests

def reconstruct_with_luma(video_path):
    api_key = os.getenv('LUMA_API_KEY')
    
    # Upload video
    with open(video_path, 'rb') as f:
        response = requests.post(
            'https://api.luma.ai/v1/captures',
            headers={'Authorization': f'Bearer {api_key}'},
            files={'video': f}
        )
    
    capture_id = response.json()['id']
    
    # Poll for completion
    while True:
        status = requests.get(
            f'https://api.luma.ai/v1/captures/{capture_id}',
            headers={'Authorization': f'Bearer {api_key}'}
        ).json()
        
        if status['status'] == 'completed':
            return status['download_url']
        
        time.sleep(5)
```

**Polycam API:**
Similar approach, upload video and receive processed 3D model.

### Option 2: NeRF-based Reconstruction

**Nerfstudio:**
```bash
pip install nerfstudio
ns-train nerfacto --data video.mp4
ns-export splat --load-config outputs/video/config.yml --output-dir exports/
```

### Option 3: COLMAP + Gaussian Splatting

Classic photogrammetry pipeline:
1. Extract frames from video
2. Run COLMAP for Structure-from-Motion
3. Generate dense point cloud
4. Train Gaussian Splatting on point cloud

## Integration with Current System

### Backend Changes

1. Add reconstruction method parameter:
```python
@app.route('/api/reconstruct', methods=['POST'])
def reconstruct_3d():
    data = request.get_json()
    method = data.get('method', 'gpt_vision')  # or 'gaussian_splatting'
    
    if method == 'gaussian_splatting':
        result = reconstruction_module.gaussian_splatting_reconstruction(
            video_path, output_path
        )
    else:
        result = generate_scene_with_gpt4(video_path, prompt, frame_count)
```

2. Add format support for .splat files:
```python
@app.route('/data/reconstructions/<path:filepath>')
def serve_reconstruction(filepath):
    file_path = Config.DATA_ROOT / 'reconstructions' / filepath
    
    if file_path.suffix == '.splat':
        return send_file(file_path, mimetype='application/octet-stream')
    # ... other formats
```

### Frontend Changes

1. Add reconstruction method selector:
```html
<select id="reconstructionMethod">
    <option value="gpt_vision">GPT-4 Vision (Fast)</option>
    <option value="gaussian_splatting">Gaussian Splatting (High Quality)</option>
</select>
```

2. Update viewer to handle different formats:
```javascript
async createWorldFromVideo(videoPath, prompt, method = 'gpt_vision') {
    const response = await fetch('/api/generate_scene', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_path: videoPath, prompt, method })
    });
    
    const data = await response.json();
    
    if (method === 'gaussian_splatting') {
        await this.loadGaussianSplat(data.splat_path);
    } else {
        this.executeGeneratedCode(data.scene.code);
    }
}
```

## Performance Considerations

### GPU Requirements
- Depth estimation: 4GB VRAM minimum
- Gaussian Splatting training: 8GB VRAM recommended
- Inference: 2GB VRAM sufficient

### Processing Time
- Depth extraction: ~1 sec per frame
- Point cloud generation: ~5-10 sec
- Gaussian Splatting training: 5-30 min depending on quality
- Total: 10-40 min per video

### Optimization Strategies
1. Precompute depth maps in parallel
2. Use smaller Gaussian Splatting models (DPT_Small vs DPT_Large)
3. Limit frame count for faster processing
4. Cache reconstructions aggressively
5. Use commercial APIs for production deployments

## Testing Plan

1. Test depth estimation accuracy on sample videos
2. Validate point cloud quality visually
3. Compare Gaussian Splatting vs GPT-4 Vision quality
4. Benchmark processing times
5. Test viewer performance with .splat files
6. Verify collision detection works with splats

## Cost Analysis

### Self-hosted (GPU server)
- Development time: 2-3 weeks
- GPU costs: $0.50-2.00 per reconstruction
- Maintenance: Ongoing

### Commercial API (Luma AI, Polycam)
- Integration time: 1-2 days
- API costs: $0.10-1.00 per reconstruction
- No maintenance

**Recommendation:** Start with commercial API for MVP, migrate to self-hosted for scale.

## Next Steps

1. Prototype depth estimation with MiDaS
2. Integrate Luma AI API as interim solution
3. Test Gaussian Splat viewer in Three.js
4. Benchmark quality vs current GPT-4 Vision approach
5. Implement full pipeline if quality justifies complexity

## Resources

- MiDaS: https://github.com/isl-org/MiDaS
- Gaussian Splatting: https://github.com/graphdeco-inria/gaussian-splatting
- Nerfstudio: https://docs.nerf.studio/
- Luma AI API: https://lumalabs.ai/api
- Three.js Gaussian Splat: https://github.com/mkkellogg/GaussianSplats3D
- Open3D: http://www.open3d.org/

## Current Status

**Phase:** Foundation implemented
**Next:** Integrate MiDaS depth estimation
**Timeline:** 2-3 weeks for full implementation
**Priority:** Medium (GPT-4 Vision works well enough for MVP)

