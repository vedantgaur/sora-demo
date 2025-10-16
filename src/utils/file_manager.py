"""
File management utilities for the Sora Director application.
Handles file operations, path generation, and cleanup.
"""
import hashlib
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from ..config import Config
from .logger import setup_logger

logger = setup_logger(__name__)


def generate_prompt_hash(prompt: str) -> str:
    """
    Generate a unique hash for a prompt to use as directory name.
    
    Args:
        prompt: The text prompt
    
    Returns:
        SHA256 hash (first 16 characters)
    """
    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:16]


def create_generation_directory(prompt_hash: str) -> Path:
    """
    Create a directory for storing generated videos.
    
    Args:
        prompt_hash: Unique hash for this prompt
    
    Returns:
        Path to the created directory
    """
    gen_dir = Config.GENERATIONS_DIR / prompt_hash
    gen_dir.mkdir(parents=True, exist_ok=True)
    
    # Create metadata file
    metadata_file = gen_dir / 'metadata.txt'
    if not metadata_file.exists():
        metadata_file.write_text(f"Generated: {datetime.now().isoformat()}\n")
    
    logger.info(f"Created generation directory: {gen_dir}")
    return gen_dir


def create_reconstruction_directory(prompt_hash: str) -> Path:
    """
    Create a directory for storing 3D reconstructions.
    
    Args:
        prompt_hash: Unique hash for this prompt
    
    Returns:
        Path to the created directory
    """
    recon_dir = Config.RECONSTRUCTIONS_DIR / prompt_hash
    recon_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Created reconstruction directory: {recon_dir}")
    return recon_dir


def get_video_path(prompt_hash: str, take_id: int) -> Path:
    """
    Get the full path for a video file.
    
    Args:
        prompt_hash: Unique hash for this prompt
        take_id: Take number (1-indexed)
    
    Returns:
        Path to the video file
    """
    gen_dir = Config.GENERATIONS_DIR / prompt_hash
    return gen_dir / f"take_{take_id}.mp4"


def get_reconstruction_path(prompt_hash: str, filename: str = "output.splat") -> Path:
    """
    Get the full path for a 3D reconstruction file.
    
    Args:
        prompt_hash: Unique hash for this prompt
        filename: Name of the reconstruction file
    
    Returns:
        Path to the reconstruction file
    """
    recon_dir = Config.RECONSTRUCTIONS_DIR / prompt_hash
    return recon_dir / filename


def list_generations(prompt_hash: str) -> List[Path]:
    """
    List all generated video files for a given prompt.
    
    Args:
        prompt_hash: Unique hash for this prompt
    
    Returns:
        List of video file paths
    """
    gen_dir = Config.GENERATIONS_DIR / prompt_hash
    if not gen_dir.exists():
        return []
    
    return sorted(gen_dir.glob("take_*.mp4"))


def cleanup_old_generations(days: int = 7) -> int:
    """
    Remove generation directories older than specified days.
    
    Args:
        days: Number of days to keep
    
    Returns:
        Number of directories removed
    """
    cutoff_time = datetime.now().timestamp() - (days * 86400)
    removed_count = 0
    
    for gen_dir in Config.GENERATIONS_DIR.iterdir():
        if gen_dir.is_dir() and gen_dir.stat().st_mtime < cutoff_time:
            shutil.rmtree(gen_dir)
            removed_count += 1
            logger.info(f"Removed old generation directory: {gen_dir}")
    
    for recon_dir in Config.RECONSTRUCTIONS_DIR.iterdir():
        if recon_dir.is_dir() and recon_dir.stat().st_mtime < cutoff_time:
            shutil.rmtree(recon_dir)
            removed_count += 1
            logger.info(f"Removed old reconstruction directory: {recon_dir}")
    
    logger.info(f"Cleanup complete: removed {removed_count} directories")
    return removed_count


def get_relative_url(file_path: Path) -> str:
    """
    Convert an absolute file path to a URL path relative to the data root.
    
    Args:
        file_path: Absolute path to file
    
    Returns:
        Relative URL path (e.g., "/data/generations/abc123/take_1.mp4")
    """
    try:
        relative_path = file_path.relative_to(Config.DATA_ROOT)
        return f"/data/{relative_path.as_posix()}"
    except ValueError:
        # If path is not relative to DATA_ROOT, return as-is
        logger.warning(f"Path {file_path} is not relative to {Config.DATA_ROOT}")
        return str(file_path)


def save_prompt_metadata(prompt_hash: str, prompt: str, metadata: dict):
    """
    Save metadata about a generation session.
    
    Args:
        prompt_hash: Unique hash for this prompt
        prompt: Original prompt text
        metadata: Additional metadata dictionary
    """
    gen_dir = Config.GENERATIONS_DIR / prompt_hash
    gen_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_file = gen_dir / 'metadata.txt'
    with metadata_file.open('w') as f:
        f.write(f"Prompt Hash: {prompt_hash}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Prompt: {prompt}\n")
        f.write("\nMetadata:\n")
        for key, value in metadata.items():
            f.write(f"  {key}: {value}\n")
    
    logger.info(f"Saved metadata for prompt {prompt_hash}")

