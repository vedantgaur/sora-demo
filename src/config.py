"""
Configuration management for the Sora Director application.
Loads settings from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration with environment variable overrides."""
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 5001))
    HOST = os.getenv('HOST', '0.0.0.0')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Mode Configuration
    USE_MOCK = os.getenv('USE_MOCK', 'true').lower() == 'true'
    
    # API Configuration
    # Check both SORA_API_KEY and OPENAI_API_KEY (OpenAI key works for Sora)
    SORA_API_KEY = os.getenv('SORA_API_KEY') or os.getenv('OPENAI_API_KEY', '')
    SORA_API_URL = os.getenv('SORA_API_URL', 'https://api.openai.com/v1/sora')
    
    # 3D Reconstruction Service
    RECONSTRUCTION_SERVICE_URL = os.getenv('RECONSTRUCTION_SERVICE_URL', 'http://localhost:8001')
    RECONSTRUCTION_TIMEOUT = int(os.getenv('RECONSTRUCTION_TIMEOUT', 300))
    
    # Agent Configuration
    AGENT_MODEL_PATH = os.getenv('AGENT_MODEL_PATH', 'models/agent_vla.pth')
    AGENT_SIMULATION_DURATION = int(os.getenv('AGENT_SIMULATION_DURATION', 30))
    
    # Data Storage
    BASE_DIR = Path(__file__).parent.parent
    DATA_ROOT = Path(os.getenv('DATA_ROOT', str(BASE_DIR / 'data')))
    GENERATIONS_DIR = Path(os.getenv('GENERATIONS_DIR', str(DATA_ROOT / 'generations')))
    RECONSTRUCTIONS_DIR = Path(os.getenv('RECONSTRUCTIONS_DIR', str(DATA_ROOT / 'reconstructions')))
    
    # Video Generation Settings
    NUM_TAKES_PER_GENERATION = int(os.getenv('NUM_TAKES_PER_GENERATION', 3))
    # Sora API only supports 4, 8, or 12 seconds
    VIDEO_DURATION_SECONDS = int(os.getenv('VIDEO_DURATION_SECONDS', 8))
    # Sora API only supports: '720x1280', '1280x720', '1024x1792', '1792x1024'
    VIDEO_RESOLUTION = os.getenv('VIDEO_RESOLUTION', '1280x720')
    VIDEO_FPS = int(os.getenv('VIDEO_FPS', 24))
    
    # Scoring Thresholds
    MIN_IDENTITY_PERSISTENCE = float(os.getenv('MIN_IDENTITY_PERSISTENCE', 0.85))
    MIN_PATH_REALISM = float(os.getenv('MIN_PATH_REALISM', 0.80))
    MIN_PHYSICS_SCORE = float(os.getenv('MIN_PHYSICS_SCORE', 0.75))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/sora_director.log')
    
    # Security
    MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', 500))
    
    # Performance
    WORKER_THREADS = int(os.getenv('WORKER_THREADS', 4))
    ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
    CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', 3600))
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist."""
        cls.DATA_ROOT.mkdir(parents=True, exist_ok=True)
        cls.GENERATIONS_DIR.mkdir(parents=True, exist_ok=True)
        cls.RECONSTRUCTIONS_DIR.mkdir(parents=True, exist_ok=True)
        Path(cls.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls):
        """Validate critical configuration."""
        if not cls.USE_MOCK:
            if not cls.SORA_API_KEY:
                raise ValueError("SORA_API_KEY must be set when USE_MOCK=false")
        
        if cls.NUM_TAKES_PER_GENERATION < 1:
            raise ValueError("NUM_TAKES_PER_GENERATION must be at least 1")
        
        if cls.VIDEO_DURATION_SECONDS not in [4, 8, 12]:
            raise ValueError("VIDEO_DURATION_SECONDS must be 4, 8, or 12 (Sora API requirement)")
    
    @classmethod
    def get_info(cls):
        """Return a dictionary of current configuration (safe for logging)."""
        return {
            'mode': 'MOCK' if cls.USE_MOCK else 'PRODUCTION',
            'port': cls.PORT,
            'host': cls.HOST,
            'num_takes': cls.NUM_TAKES_PER_GENERATION,
            'video_duration': cls.VIDEO_DURATION_SECONDS,
            'data_root': str(cls.DATA_ROOT),
        }


# Initialize configuration on import
Config.ensure_directories()
Config.validate()

