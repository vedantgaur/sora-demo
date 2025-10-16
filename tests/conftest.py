"""Pytest configuration and shared fixtures."""
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(scope='session')
def test_data_dir():
    """Create a temporary directory for test data that persists for the session."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_video_file(tmp_path):
    """Create a mock video file for testing."""
    video_path = tmp_path / "test_video.mp4"
    video_path.write_bytes(b'mock video content')
    return video_path


@pytest.fixture
def mock_asset_file(tmp_path):
    """Create a mock 3D asset file for testing."""
    asset_path = tmp_path / "test_asset.splat"
    asset_path.write_text('mock 3D asset content')
    return asset_path

