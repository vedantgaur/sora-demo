# Autonomous Video-to-Playable World Director

An end-to-end system that generates videos using Sora API, reconstructs them into interactive 3D environments using **GPT-4 Vision**, deploys animated agents to test physics and continuity, and automatically revises prompts through an agentic feedback loop.

## 🎯 Project Goal

Demonstrate a complete agentic feedback loop for generative world creation:
1. **Generates** video from text prompts (Sora API or mock)
2. **Analyzes** video frames with GPT-4 Vision to understand the scene
3. **Reconstructs** into 3D using AI-generated Three.js code
4. **Tests** the world with animated agents to find flaws
5. **Revises** prompts automatically to improve next generation

## ✨ Key Features

- **GPT-4 Vision Integration**: Analyzes video keyframes to generate accurate 3D scenes (works in both Mock & Sora modes!)
- **Single Video Generation**: Streamlined workflow - generates 1 high-quality video per prompt
- **Real-time Agent Animation**: Watch AI agents explore and test your 3D world
- **Dark Mode SaaS UI**: Modern, professional interface inspired by Linear/Vercel
- **Dual Mode**: Mock mode (free) and Real Sora API mode
- **Video Upload & Sample**: Test with your own videos or use our sample video - no API costs

## 🏗️ Architecture

```
┌─────────────┐
│   User UI   │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────────┐
│         Flask Orchestrator (main.py)            │
└──────┬──────────────────────────────────────────┘
       │
   ┌───┴──────────────────────────────┐
   │                                   │
┌──▼────────────┐           ┌─────────▼──────────┐
│ Sora Handler  │           │  Scoring Module    │
│ (Video Gen)   │           │  (Quality Rank)    │
└──┬────────────┘           └─────────┬──────────┘
   │                                   │
┌──▼────────────────┐       ┌─────────▼──────────┐
│ Reconstruction    │       │  Agent Module      │
│ (Video→3D)        │       │  (Physics Test)    │
└──┬────────────────┘       └─────────┬──────────┘
   │                                   │
   └───────────┬───────────────────────┘
               │
        ┌──────▼──────────┐
        │ Prompt Reviser  │
        │ (Auto-improve)  │
        └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip or conda

### Installation

1. Clone and navigate to the project:
```bash
cd /Users/vedantgaur/Downloads/Projects/sora-demo
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys (optional for mock mode)
```

5. Run the application:
```bash
python src/main.py
```

6. Open your browser:
```
http://localhost:5001
```

## 📁 Project Structure

```
sora-demo/
├── src/
│   ├── main.py                    # Flask orchestrator & API endpoints
│   ├── config.py                  # Configuration management
│   ├── sora_handler.py            # Sora API interface
│   ├── scoring_module.py          # Video quality scoring
│   ├── reconstruction_module.py   # Video-to-3D conversion
│   ├── agent_module.py            # Agent-based physics testing
│   ├── prompt_reviser.py          # Automatic prompt improvement
│   └── utils/
│       ├── file_manager.py        # File system operations
│       └── logger.py              # Logging utilities
├── templates/
│   └── index.html                 # Web UI
├── static/
│   ├── script.js                  # Frontend logic
│   └── style.css                  # UI styling
├── data/                          # Generated content (gitignored)
│   ├── generations/               # Video takes
│   └── reconstructions/           # 3D assets
├── tests/                         # Unit and integration tests
├── docker/                        # Docker configuration
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── README.md
```

## 🎬 User Journey

### 1. Generate or Upload Video
- **Option A**: Enter a text prompt (e.g., "A robot walks down a futuristic hallway") and click **Generate Videos**
- **Option B**: Click **Use Sample Video** for instant testing
- **Option C**: Upload your own video in Mock Mode
The system generates 1 high-quality video and scores it.

### 2. Reconstruct to 3D World
Click **Reconstruct 3D World**. The system:
- Extracts keyframes from the video
- Analyzes them with **GPT-4 Vision** (if API key provided)
- Generates custom Three.js code to recreate the scene
- Renders an interactive 3D environment matching the video

### 3. Run Agent Test
Click **Run Agent Test**. Watch a simulated agent navigate the 3D world in real-time:
- Agent moves intelligently through the environment
- Tests for physics violations (collisions, unstable geometry)
- Red markers appear where violations are detected
- Results show issue count and descriptions

### 4. Auto-Revise Prompt
Based on detected violations, the system automatically generates an improved prompt (e.g., "A robot walks down a wide, well-lit futuristic hallway with clear pathways and stable floor"). Click **Regenerate** to iterate with the enhanced prompt.

## 🔧 Configuration

### Mock Mode (Default)
No API keys needed. Uses simulated video generation and scoring for rapid development and testing.

### Production Mode
Set `USE_MOCK=false` in `.env` and provide:
- `SORA_API_KEY`: Your Sora API credentials
- `RECONSTRUCTION_SERVICE_URL`: 3D reconstruction endpoint
- `AGENT_MODEL_PATH`: Path to trained VLA model

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_sora_handler.py
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t sora-director .

# Run container
docker run -p 5000:5000 -v $(pwd)/data:/app/data sora-director
```

## 📊 Evaluation Metrics

- **Identity Persistence**: Embedding cosine similarity across frames
- **Path Realism**: Velocity/acceleration smoothness
- **Physics Plausibility**: Collision compliance and trajectory stability
- **Audio-Visual Sync**: Event-to-sound alignment (Sora 2)

## 🛠️ Technology Stack

- **Backend**: Flask, Python 3.9+
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Video Processing**: OpenCV, FFmpeg
- **3D Reconstruction**: Video Gaussian Splatting
- **Agent**: RT-2-style VLA policy (simulated in MVP)
- **Storage**: Local filesystem (upgradeable to S3/GCS)

## 🔮 Roadmap

### MVP (Current)
- [x] Text-to-video generation with ranking
- [x] Basic 3D reconstruction
- [x] Simulated agent testing
- [x] Automatic prompt revision

### Phase 2
- [ ] Real Sora API integration
- [ ] Advanced video-Gaussian reconstruction
- [ ] RT-2 VLA deployment
- [ ] Multi-environment support

### Phase 3
- [ ] Promptable mid-scene events
- [ ] Audio-visual sync testing
- [ ] C2PA provenance metadata
- [ ] Social feed integration

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## 📧 Contact

For questions or issues, please open a GitHub issue or contact the maintainer.

