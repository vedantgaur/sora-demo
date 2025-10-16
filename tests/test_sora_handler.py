"""Tests for the Sora Handler module."""
import pytest
from pathlib import Path
import tempfile
import shutil

from src.sora_handler import SoraHandler


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sora_handler():
    """Create a SoraHandler instance in mock mode."""
    return SoraHandler(use_mock=True)


def test_generate_n_takes_creates_files(sora_handler, temp_dir):
    """Test that generate_n_takes creates the expected number of video files."""
    prompt = "A robot walks down a hallway"
    num_takes = 3
    
    video_paths = sora_handler.generate_n_takes(
        prompt=prompt,
        num_takes=num_takes,
        output_dir=temp_dir
    )
    
    assert len(video_paths) == num_takes
    
    for i, video_path in enumerate(video_paths, start=1):
        assert video_path.exists()
        assert video_path.name == f"take_{i}.mp4"
        assert video_path.parent == temp_dir


def test_generate_n_takes_with_custom_params(sora_handler, temp_dir):
    """Test generation with custom parameters."""
    video_paths = sora_handler.generate_n_takes(
        prompt="Test scene",
        num_takes=2,
        output_dir=temp_dir,
        duration=5,
        resolution="640x360",
        fps=30
    )
    
    assert len(video_paths) == 2
    for path in video_paths:
        assert path.exists()


def test_extend_video(sora_handler, temp_dir):
    """Test video extension functionality."""
    # First create a video
    video_paths = sora_handler.generate_n_takes(
        prompt="Test",
        num_takes=1,
        output_dir=temp_dir
    )
    
    original_video = video_paths[0]
    
    # Extend it
    extended_video = sora_handler.extend_video(
        video_path=original_video,
        extension_prompt="Continue the scene",
        duration=5
    )
    
    assert extended_video.exists()
    assert "_extended" in extended_video.stem


def test_remix_video(sora_handler, temp_dir):
    """Test video remix functionality."""
    # Create a video
    video_paths = sora_handler.generate_n_takes(
        prompt="Test",
        num_takes=1,
        output_dir=temp_dir
    )
    
    original_video = video_paths[0]
    
    # Remix it
    remixed_video = sora_handler.remix_video(
        video_path=original_video,
        remix_prompt="Make it darker"
    )
    
    assert remixed_video.exists()
    assert "_remix" in remixed_video.stem

