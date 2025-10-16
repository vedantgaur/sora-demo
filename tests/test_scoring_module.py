"""Tests for the Scoring Module."""
import pytest
from pathlib import Path
import tempfile

from src.scoring_module import VideoScorer, score_video


@pytest.fixture
def video_scorer():
    """Create a VideoScorer instance in mock mode."""
    return VideoScorer(use_mock=True)


@pytest.fixture
def temp_video():
    """Create a temporary video file for testing."""
    temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    temp_path = Path(temp_file.name)
    temp_file.write(b'mock video data')
    temp_file.close()
    yield temp_path
    temp_path.unlink()


def test_score_video_returns_all_metrics(video_scorer, temp_video):
    """Test that score_video returns all expected metrics."""
    scores = video_scorer.score_video(temp_video)
    
    expected_metrics = [
        'identity_persistence',
        'path_realism',
        'physics_plausibility',
        'visual_quality',
        'motion_smoothness',
        'temporal_coherence',
        'overall'
    ]
    
    for metric in expected_metrics:
        assert metric in scores
        assert 0.0 <= scores[metric] <= 1.0


def test_score_video_with_nonexistent_file(video_scorer):
    """Test scoring with a nonexistent file."""
    fake_path = Path('/nonexistent/video.mp4')
    scores = video_scorer.score_video(fake_path)
    
    # Should return default scores
    assert scores['overall'] == 0.5


def test_score_consistency(video_scorer, temp_video):
    """Test that scoring the same video gives consistent results."""
    scores1 = video_scorer.score_video(temp_video)
    scores2 = video_scorer.score_video(temp_video)
    
    assert scores1 == scores2


def test_rank_videos(video_scorer):
    """Test video ranking functionality."""
    video_scores = [
        {'video_path': 'video1.mp4', 'scores': {'overall': 0.85}},
        {'video_path': 'video2.mp4', 'scores': {'overall': 0.92}},
        {'video_path': 'video3.mp4', 'scores': {'overall': 0.78}},
    ]
    
    ranked = video_scorer.rank_videos(video_scores)
    
    assert ranked[0]['scores']['overall'] == 0.92
    assert ranked[1]['scores']['overall'] == 0.85
    assert ranked[2]['scores']['overall'] == 0.78


def test_convenience_function(temp_video):
    """Test the convenience score_video function."""
    scores = score_video(temp_video)
    assert 'overall' in scores
    assert 0.0 <= scores['overall'] <= 1.0

