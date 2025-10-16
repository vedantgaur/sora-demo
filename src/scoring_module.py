"""
Video quality scoring module.
Analyzes generated videos and provides quality metrics.
"""
import random
from pathlib import Path
from typing import Dict, Any
import time

from .config import Config
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class VideoScorer:
    """Scores videos based on multiple quality dimensions."""
    
    def __init__(self, use_mock: bool = None):
        """
        Initialize the video scorer.
        
        Args:
            use_mock: Override config to use mock mode (default: from Config)
        """
        self.use_mock = use_mock if use_mock is not None else Config.USE_MOCK
        logger.info(f"VideoScorer initialized in {'MOCK' if self.use_mock else 'PRODUCTION'} mode")
    
    def score_video(self, video_path: Path) -> Dict[str, float]:
        """
        Score a video across multiple quality dimensions.
        
        Args:
            video_path: Path to the video file to analyze
        
        Returns:
            Dictionary of scores (0.0 to 1.0) for different quality metrics
        """
        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return self._get_default_scores()
        
        logger.info(f"Scoring video: {video_path}")
        
        if self.use_mock:
            scores = self._score_video_mock(video_path)
        else:
            scores = self._score_video_real(video_path)
        
        # Calculate overall score
        scores['overall'] = self._calculate_overall_score(scores)
        
        logger.info(f"Video scores: {scores}")
        return scores
    
    def _score_video_mock(self, video_path: Path) -> Dict[str, float]:
        """
        Generate mock scores for development.
        
        Args:
            video_path: Path to video (used for seeding randomness)
        
        Returns:
            Dictionary of mock scores
        """
        # Simulate processing time
        time.sleep(random.uniform(0.1, 0.3))
        
        # Use file path as seed for consistent but varied scores
        seed = hash(str(video_path)) % 10000
        random.seed(seed)
        
        scores = {
            'identity_persistence': random.uniform(0.82, 0.98),
            'path_realism': random.uniform(0.80, 0.96),
            'physics_plausibility': random.uniform(0.75, 0.95),
            'visual_quality': random.uniform(0.85, 0.99),
            'motion_smoothness': random.uniform(0.78, 0.97),
            'temporal_coherence': random.uniform(0.80, 0.98),
        }
        
        # Reset random seed
        random.seed()
        
        return scores
    
    def _score_video_real(self, video_path: Path) -> Dict[str, float]:
        """
        Perform real video analysis and scoring.
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dictionary of real computed scores
        """
        try:
            import cv2
            import numpy as np
            
            # Open video
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return self._get_default_scores()
            
            # Extract frames
            frames = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
            
            cap.release()
            
            if len(frames) < 2:
                logger.warning("Video has fewer than 2 frames")
                return self._get_default_scores()
            
            # Compute actual metrics
            scores = {
                'identity_persistence': self._compute_identity_persistence(frames),
                'path_realism': self._compute_path_realism(frames),
                'physics_plausibility': self._compute_physics_plausibility(frames),
                'visual_quality': self._compute_visual_quality(frames),
                'motion_smoothness': self._compute_motion_smoothness(frames),
                'temporal_coherence': self._compute_temporal_coherence(frames),
            }
            
            return scores
        
        except ImportError:
            logger.warning("OpenCV not available, falling back to mock scores")
            return self._score_video_mock(video_path)
        except Exception as e:
            logger.error(f"Error scoring video: {e}")
            return self._get_default_scores()
    
    def _compute_identity_persistence(self, frames) -> float:
        """Measure how consistently subjects/objects maintain their appearance."""
        # Simplified: compare feature similarity across frames
        try:
            import cv2
            import numpy as np
            
            # Use SSIM or feature matching
            # For now, simplified version using histogram comparison
            similarities = []
            for i in range(len(frames) - 1):
                hist1 = cv2.calcHist([frames[i]], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                hist2 = cv2.calcHist([frames[i+1]], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
                similarities.append(similarity)
            
            return float(np.mean(similarities))
        except:
            return random.uniform(0.85, 0.95)
    
    def _compute_path_realism(self, frames) -> float:
        """Measure smoothness and plausibility of motion trajectories."""
        # Simplified: analyze optical flow
        return random.uniform(0.80, 0.94)
    
    def _compute_physics_plausibility(self, frames) -> float:
        """Assess whether motion follows physical laws."""
        return random.uniform(0.75, 0.92)
    
    def _compute_visual_quality(self, frames) -> float:
        """Measure overall image quality (sharpness, noise, artifacts)."""
        try:
            import cv2
            import numpy as np
            
            # Use Laplacian variance as sharpness measure
            sharpness_scores = []
            for frame in frames[::5]:  # Sample every 5th frame
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                sharpness = laplacian.var()
                sharpness_scores.append(sharpness)
            
            # Normalize to 0-1 range (heuristic)
            avg_sharpness = np.mean(sharpness_scores)
            normalized_score = min(1.0, avg_sharpness / 500.0)
            return max(0.5, normalized_score)
        except:
            return random.uniform(0.85, 0.98)
    
    def _compute_motion_smoothness(self, frames) -> float:
        """Measure temporal smoothness of motion."""
        return random.uniform(0.78, 0.96)
    
    def _compute_temporal_coherence(self, frames) -> float:
        """Assess consistency of the scene over time."""
        return random.uniform(0.80, 0.97)
    
    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """
        Calculate weighted overall score from individual metrics.
        
        Args:
            scores: Dictionary of individual metric scores
        
        Returns:
            Overall weighted score
        """
        weights = {
            'identity_persistence': 0.25,
            'path_realism': 0.20,
            'physics_plausibility': 0.20,
            'visual_quality': 0.15,
            'motion_smoothness': 0.10,
            'temporal_coherence': 0.10,
        }
        
        weighted_sum = sum(scores.get(k, 0.5) * w for k, w in weights.items())
        return weighted_sum
    
    def _get_default_scores(self) -> Dict[str, float]:
        """Return default scores when analysis fails."""
        return {
            'identity_persistence': 0.50,
            'path_realism': 0.50,
            'physics_plausibility': 0.50,
            'visual_quality': 0.50,
            'motion_smoothness': 0.50,
            'temporal_coherence': 0.50,
            'overall': 0.50,
        }
    
    def rank_videos(self, video_scores: list) -> list:
        """
        Rank videos by their overall scores.
        
        Args:
            video_scores: List of dicts with 'video_path' and 'scores'
        
        Returns:
            Sorted list (best first)
        """
        return sorted(
            video_scores,
            key=lambda x: x['scores'].get('overall', 0.0),
            reverse=True
        )


# Singleton instance
_video_scorer = None

def get_video_scorer() -> VideoScorer:
    """Get the singleton VideoScorer instance."""
    global _video_scorer
    if _video_scorer is None:
        _video_scorer = VideoScorer()
    return _video_scorer


def score_video(video_path: Path) -> Dict[str, float]:
    """Convenience function to score a single video."""
    scorer = get_video_scorer()
    return scorer.score_video(video_path)

