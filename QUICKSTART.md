# Quick Start Guide

Get Sora Director up and running in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- 2GB free disk space
- Modern web browser

## Installation

### Option 1: Automated Setup (Recommended)

```bash
# Clone or navigate to the project
cd /Users/vedantgaur/Downloads/Projects/sora-demo

# Run the setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
```

The setup script will:
- ✅ Create a virtual environment
- ✅ Install all dependencies
- ✅ Create necessary directories
- ✅ Generate a default `.env` file

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data/generations data/reconstructions logs

# Create .env file (optional, uses defaults if missing)
cp .env.example .env
```

## Running the Application

### Using the run script:

```bash
chmod +x scripts/run.sh
./scripts/run.sh
```

### Or manually:

```bash
source venv/bin/activate
python src/main.py
```

The application will start on `http://localhost:5000`

## First Use Tutorial

### Step 1: Enter a Prompt

1. Open http://localhost:5000 in your browser
2. Type a scene description, for example:
   ```
   A robot walks down a futuristic hallway with glowing panels
   ```
3. Click **"Generate Videos"**
4. Wait 5-10 seconds while the system generates 3 video variations

### Step 2: Review and Select

1. The system will display 3 ranked video takes
2. Review the quality scores for each:
   - Identity Persistence
   - Path Realism
   - Overall Score
3. Click **"Select for 3D Reconstruction"** on your preferred take (usually Rank 1)

### Step 3: Lift to 3D

1. Click **"🏗️ Lift to 3D World"**
2. Wait 5-10 seconds for reconstruction
3. A 3D world viewer will appear

### Step 4: Test with Agent

1. Click **"🤖 Run Agent Test"**
2. Wait for the agent to explore the 3D world
3. Review the test results:
   - Any violations detected (physics, boundaries, etc.)
   - Performance metrics
   - Automatically revised prompt

### Step 5: Iterate (Optional)

1. If violations were found, the system suggests an improved prompt
2. Click **"🔄 Regenerate with Improved Prompt"**
3. The cycle begins again with a better prompt

## Understanding Mock Mode

By default, the application runs in **MOCK MODE**:

- ✅ No API keys required
- ✅ Fast execution (uses test patterns)
- ✅ Perfect for learning and development
- ✅ Demonstrates the complete workflow

To see the mode, check the badge in the top-right corner of the UI.

## Example Prompts

Try these prompts to see different results:

**Simple scenes:**
```
A car driving down a desert highway
A cat walking through a garden
A drone flying over a city
```

**Complex scenes:**
```
A robot exploring an abandoned space station, cinematic lighting
A medieval knight walking through a misty forest at dawn
A futuristic train departing from a neon-lit station
```

**Action scenes:**
```
A parkour athlete jumping between rooftops
A spacecraft landing on an alien planet
A tornado forming over flat plains
```

## Troubleshooting

### Port already in use
```bash
# Change the port in .env
PORT=5001
```

### Missing dependencies
```bash
pip install -r requirements.txt
```

### Videos not generating
- Check that `data/generations` directory exists
- Check logs in `logs/sora_director.log`
- Ensure you're in MOCK mode (USE_MOCK=true)

### Page not loading
- Ensure Flask is running (check terminal)
- Try http://127.0.0.1:5000 instead of localhost
- Check firewall settings

## Configuration

Edit the `.env` file to customize:

```bash
# Change port
PORT=5001

# Change number of video takes
NUM_TAKES_PER_GENERATION=5

# Enable debug mode
FLASK_DEBUG=True

# Change log level
LOG_LEVEL=DEBUG
```

## Production Mode

To use real APIs (requires API keys):

1. Set `USE_MOCK=false` in `.env`
2. Add your API keys:
   ```
   SORA_API_KEY=your_key_here
   RECONSTRUCTION_SERVICE_URL=http://your-service:8001
   ```
3. Restart the application

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
- Read [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- Check out the full [README.md](README.md) for advanced features

## Running Tests

```bash
# Run all tests
chmod +x scripts/test.sh
./scripts/test.sh

# Or manually
pytest
```

## Docker Deployment

```bash
# Build and run with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Getting Help

- 📖 Check [README.md](README.md)
- 🏗️ Review [ARCHITECTURE.md](ARCHITECTURE.md)
- 🐛 Open an issue on GitHub
- 💬 Check existing issues for solutions

## Performance Notes

**Mock Mode Timing:**
- Video generation: 2-5 seconds per take
- Scoring: < 1 second
- 3D reconstruction: 2-3 seconds
- Agent testing: 2-3 seconds
- **Total workflow: ~15-30 seconds**

**Production Mode (estimated):**
- Video generation: 30-120 seconds per take
- Scoring: 5-10 seconds
- 3D reconstruction: 60-300 seconds
- Agent testing: 10-30 seconds
- **Total workflow: 5-15 minutes**

## Key Features

✨ **Automatic Prompt Improvement**: System learns from failures  
🎬 **Multi-take Generation**: Get variations, pick the best  
🏗️ **Video-to-3D**: Turn 2D videos into playable worlds  
🤖 **Agentic Testing**: Automated quality assurance  
📊 **Quality Metrics**: Objective scoring for every take  
🔄 **Feedback Loop**: Continuous improvement cycle  

## Tips for Best Results

1. **Be Specific**: More details = better results
2. **Use Action Verbs**: "walks", "flies", "explores"
3. **Describe Lighting**: "well-lit", "sunset", "neon-lit"
4. **Set the Scene**: "futuristic hallway", "ancient temple"
5. **Iterate**: Use the revised prompts to improve

---

**Ready to create some worlds?** Fire up the application and start generating! 🚀

