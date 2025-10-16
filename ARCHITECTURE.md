# Sora Director Architecture

This document provides a detailed overview of the Sora Director system architecture.

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Module Descriptions](#module-descriptions)
5. [API Endpoints](#api-endpoints)
6. [Extension Points](#extension-points)

## System Overview

Sora Director is an autonomous video-to-playable world system that implements a complete agentic feedback loop:

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                    (Web Browser / Client)                    │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Orchestrator                        │
│                      (src/main.py)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  REST API Endpoints                                   │  │
│  │  /api/generate | /api/reconstruct | /api/run_agent  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────┬───────────┬────────────┬──────────┬───────────────┘
          │           │            │          │
          ▼           ▼            ▼          ▼
    ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐
    │  Sora   │ │ Scoring │ │ Reconst. │ │  Agent   │
    │ Handler │ │  Module │ │  Module  │ │  Module  │
    └─────────┘ └─────────┘ └──────────┘ └──────────┘
          │           │            │          │
          └───────────┴────────────┴──────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │   Prompt     │
                  │   Reviser    │
                  └──────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ File Storage │
                  │   (data/)    │
                  └──────────────┘
```

## Component Architecture

### Frontend Layer

**Technology**: Vanilla JavaScript, HTML5, CSS3

**Responsibilities**:
- User interface rendering
- User interaction handling
- API communication
- Real-time UI updates
- Result visualization

**Files**:
- `templates/index.html` - Main UI structure
- `static/style.css` - Styling and layout
- `static/script.js` - Client-side logic

### Backend Layer

**Technology**: Flask (Python 3.9+)

**Responsibilities**:
- Request orchestration
- Module coordination
- Error handling
- File serving
- State management

**Files**:
- `src/main.py` - Main Flask application
- `src/config.py` - Configuration management

### Processing Modules

#### 1. Sora Handler (`src/sora_handler.py`)

**Purpose**: Video generation interface

**Key Functions**:
- `generate_n_takes()` - Generate multiple video variations
- `extend_video()` - Extend existing videos
- `remix_video()` - Create remixed versions

**Modes**:
- **Mock**: Uses ffmpeg to create test patterns
- **Production**: Calls real Sora API

#### 2. Scoring Module (`src/scoring_module.py`)

**Purpose**: Video quality analysis

**Metrics**:
- Identity persistence (subject consistency)
- Path realism (motion plausibility)
- Physics plausibility (physical laws)
- Visual quality (sharpness, artifacts)
- Motion smoothness (temporal coherence)
- Temporal coherence (scene consistency)

**Algorithm**:
```python
overall_score = Σ(metric_score × weight)
```

#### 3. Reconstruction Module (`src/reconstruction_module.py`)

**Purpose**: Video-to-3D conversion

**Supported Formats**:
- Gaussian Splats (.splat)
- Point Clouds (.ply)
- 3D Models (.glb)

**Workflow**:
1. Extract frames from video
2. Compute depth maps
3. Generate 3D representation
4. Optimize for performance

#### 4. Agent Module (`src/agent_module.py`)

**Purpose**: World testing and validation

**Test Scenarios**:
- Collision detection
- Path traversal
- Physics stability
- Boundary integrity
- Object persistence

**Output**: List of violations + performance metrics

#### 5. Prompt Reviser (`src/prompt_reviser.py`)

**Purpose**: Automatic prompt improvement

**Revision Rules**:
```python
violation_type → enhancement_phrase
PhysicsViolation → "with clear solid boundaries"
BoundaryViolation → "in a contained environment"
ObjectPersistence → "with consistent object appearance"
```

**Strategy**: Rule-based enhancement + quality modifiers

## Data Flow

### Complete Workflow

```
1. User Input
   ↓
   [Prompt Text] → generate_prompt_hash()
   ↓
2. Video Generation
   ↓
   prompt → SoraHandler.generate_n_takes()
   ↓
   [video_1.mp4, video_2.mp4, video_3.mp4]
   ↓
3. Quality Scoring
   ↓
   videos → VideoScorer.score_video() for each
   ↓
   [{video, scores}, ...] → sort by overall score
   ↓
4. User Selection
   ↓
   [selected_video]
   ↓
5. 3D Reconstruction
   ↓
   video → ReconstructionModule.run_reconstruction()
   ↓
   [3D_asset.splat]
   ↓
6. Agent Testing
   ↓
   asset → AgentModule.test_world()
   ↓
   [violations, metrics]
   ↓
7. Prompt Revision
   ↓
   (prompt, violations) → PromptReviser.revise_prompt()
   ↓
   [revised_prompt]
   ↓
8. Loop Back (Optional)
   ↓
   revised_prompt → Step 2
```

## Module Descriptions

### Configuration System

**File**: `src/config.py`

**Features**:
- Environment variable loading
- Default value fallbacks
- Directory management
- Validation checks

**Key Settings**:
```python
Config.USE_MOCK          # Mock vs production mode
Config.SORA_API_KEY      # API authentication
Config.DATA_ROOT         # Storage location
Config.VIDEO_DURATION    # Generation parameters
```

### Utility Modules

#### File Manager (`src/utils/file_manager.py`)

**Functions**:
- `generate_prompt_hash()` - Create unique IDs
- `create_generation_directory()` - Set up folders
- `get_relative_url()` - Path to URL conversion
- `cleanup_old_generations()` - Maintenance

#### Logger (`src/utils/logger.py`)

**Features**:
- Console and file logging
- Configurable log levels
- Structured formatting
- Module-specific loggers

## API Endpoints

### `POST /api/generate`

Generate video takes from a prompt.

**Request**:
```json
{
  "prompt": "A robot walks down a hallway",
  "num_takes": 3
}
```

**Response**:
```json
{
  "prompt_hash": "abc123...",
  "prompt": "A robot walks down a hallway",
  "takes": [
    {
      "take_id": 1,
      "video_url": "/data/generations/abc123/take_1.mp4",
      "video_path": "/full/path/to/take_1.mp4",
      "scores": {
        "identity_persistence": 0.95,
        "path_realism": 0.92,
        "overall": 0.93
      },
      "rank": 1
    }
  ],
  "success": true
}
```

### `POST /api/reconstruct`

Reconstruct 3D world from video.

**Request**:
```json
{
  "prompt_hash": "abc123...",
  "video_path": "/path/to/video.mp4"
}
```

**Response**:
```json
{
  "asset_url": "/data/reconstructions/abc123/output.splat",
  "asset_path": "/full/path/to/output.splat",
  "format": "splat",
  "success": true
}
```

### `POST /api/run_agent`

Run agent tests on 3D world.

**Request**:
```json
{
  "asset_path": "/path/to/asset.splat",
  "prompt": "original prompt text"
}
```

**Response**:
```json
{
  "violations": [
    {
      "type": "PhysicsViolation",
      "description": "Agent path collided with solid object",
      "severity": "high",
      "location": {"x": 1.5, "y": 0, "z": 2.3},
      "timestamp": 5.2
    }
  ],
  "metrics": {
    "collision_rate": 0.05,
    "path_completion": 0.95,
    "physics_score": 0.88
  },
  "revised_prompt": "A robot walks down a hallway with clear solid boundaries",
  "explanation": "Revised prompt to address 1 issue(s)...",
  "success": true
}
```

## Extension Points

### Adding New Video Generators

Extend `SoraHandler` or create a new class:

```python
class CustomVideoGenerator:
    def generate_n_takes(self, prompt, num_takes, output_dir):
        # Your implementation
        pass
```

### Adding New Scoring Metrics

Extend `VideoScorer`:

```python
def _compute_custom_metric(self, frames) -> float:
    # Your metric calculation
    return score
```

### Adding New Agent Tests

Add to `AgentModule.test_world()`:

```python
test_scenarios = [
    'collision_detection',
    'custom_test',  # Your new test
]
```

### Adding New Revision Rules

Update `PromptReviser.revision_rules`:

```python
self.revision_rules['NewViolationType'] = [
    "enhancement phrase 1",
    "enhancement phrase 2"
]
```

## Deployment Architecture

### Development

```
Local Machine
├── Flask Dev Server (port 5000)
├── SQLite (optional)
└── Local File Storage (data/)
```

### Production (Docker)

```
Docker Container
├── Gunicorn (WSGI server)
├── Flask Application
├── Volume Mounts
│   ├── /app/data → persistent storage
│   └── /app/logs → log files
└── Health Checks
```

### Production (Cloud)

```
Load Balancer
├── App Server 1 (Docker)
├── App Server 2 (Docker)
└── App Server N (Docker)
    ↓
S3/GCS (File Storage)
    ↓
PostgreSQL (Metadata)
    ↓
Redis (Caching)
    ↓
Celery Workers (Async Tasks)
```

## Performance Considerations

1. **Video Generation**: Can take 30s-2min per take
2. **3D Reconstruction**: 1-5 minutes depending on video length
3. **Agent Testing**: 5-30 seconds per world
4. **Concurrent Requests**: Current design is synchronous

### Optimization Strategies

- Implement async task queue (Celery)
- Add caching layer (Redis)
- Use CDN for video delivery
- Implement request batching
- Add GPU acceleration for ML tasks

## Security Considerations

1. **Input Validation**: Sanitize all user inputs
2. **File Upload Limits**: Enforce max file sizes
3. **Path Traversal**: Validate file paths
4. **API Rate Limiting**: Prevent abuse
5. **Authentication**: Add JWT tokens for production
6. **CORS**: Configure appropriate origins

## Future Enhancements

1. **Real-time Updates**: WebSocket for progress updates
2. **Multi-user Support**: User accounts and sessions
3. **Prompt Library**: Save and share prompts
4. **Advanced Metrics**: ML-based quality assessment
5. **3D Viewer**: Interactive WebGL viewer
6. **Audio-Visual Sync**: Foley and music analysis
7. **Version Control**: Track generation iterations
8. **A/B Testing**: Compare multiple revisions

---

For questions or clarifications about the architecture, please open an issue or contact the maintainers.

