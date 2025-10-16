"""
Sora API handler for video generation.
Supports both mock mode (for development) and production mode (real API calls).
"""
import time
import random
from pathlib import Path
from typing import List, Dict, Any
import subprocess

from .config import Config
from .utils.logger import setup_logger
from .utils.file_manager import get_video_path

logger = setup_logger(__name__)


class SoraHandler:
    """Handles video generation via Sora API or mock implementation."""
    
    def __init__(self, use_mock: bool = None, progress_callback=None):
        """
        Initialize the Sora handler.
        
        Args:
            use_mock: Override config to use mock mode (default: from Config)
            progress_callback: Optional callback function(status, progress, message) for progress updates
        """
        self.use_mock = use_mock if use_mock is not None else Config.USE_MOCK
        self.api_key = Config.SORA_API_KEY
        self.api_url = Config.SORA_API_URL
        self.progress_callback = progress_callback
        
        if not self.use_mock and not self.api_key:
            logger.warning("Sora API key not set, falling back to mock mode")
            self.use_mock = True
        
        logger.info(f"SoraHandler initialized in {'MOCK' if self.use_mock else 'PRODUCTION'} mode")
    
    def generate_n_takes(
        self,
        prompt: str,
        num_takes: int,
        output_dir: Path,
        duration: int = None,
        resolution: str = None,
        fps: int = None
    ) -> List[Path]:
        """
        Generate multiple video takes from a prompt.
        
        Args:
            prompt: Text description of the video to generate
            num_takes: Number of video variations to create
            output_dir: Directory to save generated videos
            duration: Video duration in seconds (default: from Config)
            resolution: Video resolution (default: from Config)
            fps: Frames per second (default: from Config)
        
        Returns:
            List of paths to generated video files
        """
        duration = duration or Config.VIDEO_DURATION_SECONDS
        resolution = resolution or Config.VIDEO_RESOLUTION
        fps = fps or Config.VIDEO_FPS
        
        logger.info(f"Generating {num_takes} takes for prompt: '{prompt}'")
        logger.info(f"Settings: duration={duration}s, resolution={resolution}, fps={fps}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        video_paths = []
        
        for i in range(1, num_takes + 1):
            video_path = output_dir / f"take_{i}.mp4"
            
            if self.use_mock:
                self._generate_mock_video(video_path, duration, resolution, fps)
            else:
                self._generate_real_video(prompt, video_path, duration, resolution, fps, seed=i)
            
            video_paths.append(video_path)
            logger.info(f"Generated take {i}/{num_takes}: {video_path}")
        
        return video_paths
    
    def _generate_mock_video(
        self,
        output_path: Path,
        duration: int,
        resolution: str,
        fps: int
    ):
        """
        Generate a mock video file (placeholder for development).
        
        Args:
            output_path: Where to save the video
            duration: Video duration in seconds
            resolution: Video resolution (e.g., "1024x576")
            fps: Frames per second
        """
        # Simulate API delay
        time.sleep(random.uniform(0.5, 1.5))
        
        # Parse resolution
        width, height = map(int, resolution.split('x'))
        
        # Create a simple test video using ffmpeg (if available)
        # Fall back to creating an empty file if ffmpeg is not available
        try:
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'testsrc=duration={duration}:size={width}x{height}:rate={fps}',
                '-pix_fmt', 'yuv420p',
                '-y',  # Overwrite output file
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=duration + 10
            )
            
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, cmd)
            
            logger.info(f"Mock video created with ffmpeg: {output_path}")
        
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            # Fallback: create an empty file
            logger.warning(f"ffmpeg not available ({e}), creating placeholder file")
            output_path.touch()
            # Add some dummy content to make it non-empty
            output_path.write_bytes(b'MOCK_VIDEO_DATA' * 1000)
    
    def _generate_real_video(
        self,
        prompt: str,
        output_path: Path,
        duration: int,
        resolution: str,
        fps: int,
        seed: int = None
    ):
        """
        Generate a real video using OpenAI Sora API.
        
        Args:
            prompt: Text description of the video
            output_path: Where to save the video
            duration: Video duration in seconds
            resolution: Video resolution (e.g., "1280x720")
            fps: Frames per second
            seed: Random seed for reproducibility
        """
        try:
            from openai import OpenAI
            import time
            
            client = OpenAI(api_key=self.api_key)
            
            logger.info(f"Starting Sora video generation: '{prompt[:50]}...'")
            
            # Create video generation job
            video = client.videos.create(
                model="sora-2",  # Use sora-2 for speed, sora-2-pro for quality
                prompt=prompt,
                size=resolution,
                seconds=str(duration)
            )
            
            logger.info(f"Video job created: {video.id}, status: {video.status}")
            
            # Poll for completion
            max_wait = duration * 30  # Wait up to 30x the video duration
            start_time = time.time()
            
            while video.status in ("queued", "in_progress"):
                if time.time() - start_time > max_wait:
                    raise TimeoutError(f"Video generation timed out after {max_wait}s")
                
                time.sleep(5)  # Poll every 5 seconds
                video = client.videos.retrieve(video.id)
                progress = getattr(video, "progress", 0)
                logger.info(f"Video generation progress: {progress}% (status: {video.status})")
                
                # Call progress callback if provided
                if self.progress_callback:
                    self.progress_callback(
                        status=video.status,
                        progress=progress,
                        message=f"Generating video: {progress}%"
                    )
            
            if video.status == "failed":
                error_msg = getattr(getattr(video, "error", None), "message", "Unknown error")
                raise Exception(f"Video generation failed: {error_msg}")
            
            # Download the completed video
            logger.info(f"Downloading video content...")
            content = client.videos.download_content(video.id, variant="video")
            content.write_to_file(str(output_path))
            
            logger.info(f"Successfully generated video via Sora API: {output_path}")
        
        except Exception as e:
            logger.error(f"Failed to generate video via Sora API: {e}")
            logger.warning("Falling back to mock generation")
            self._generate_mock_video(output_path, duration, resolution, fps)
    
    def extend_video(
        self,
        video_path: Path,
        extension_prompt: str,
        duration: int = 5
    ) -> Path:
        """
        Extend an existing video with additional content.
        
        Args:
            video_path: Path to existing video
            extension_prompt: Prompt for the extension
            duration: Duration of extension in seconds
        
        Returns:
            Path to extended video
        """
        output_path = video_path.parent / f"{video_path.stem}_extended.mp4"
        
        logger.info(f"Extending video: {video_path}")
        
        if self.use_mock:
            # Mock: just copy the original
            import shutil
            shutil.copy(video_path, output_path)
        else:
            # Real API call would go here
            pass
        
        return output_path
    
    def remix_video(
        self,
        video_path: Path,
        remix_prompt: str
    ) -> Path:
        """
        Create a remixed version of a video with modified attributes.
        
        Args:
            video_path: Path to existing video
            remix_prompt: Prompt describing desired changes
        
        Returns:
            Path to remixed video
        """
        output_path = video_path.parent / f"{video_path.stem}_remix.mp4"
        
        logger.info(f"Remixing video: {video_path}")
        
        if self.use_mock:
            # Mock: just copy the original
            import shutil
            shutil.copy(video_path, output_path)
        else:
            # Real API call would go here
            pass
        
        return output_path


# Singleton instance
_sora_handler = None

def get_sora_handler() -> SoraHandler:
    """Get the singleton SoraHandler instance."""
    global _sora_handler
    if _sora_handler is None:
        _sora_handler = SoraHandler()
    return _sora_handler

