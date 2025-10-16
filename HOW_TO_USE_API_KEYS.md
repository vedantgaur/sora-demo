# How to Use API Keys Safely with Sora Director

---

## Step-by-Step: Adding Your API Key

### Step 1: Create a `.env` file

```bash
cd /Users/vedantgaur/Downloads/Projects/sora-demo

# Create .env from template
cp env-template.txt .env
```

### Step 2: Edit `.env` with your ACTUAL key

Open `.env` in a text editor and replace the placeholder:

```bash
# Using nano
nano .env

# Or using VS Code
code .env

# Or using any text editor
open -a TextEdit .env
```

Add this line:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### Step 3: Verify `.env` is gitignored

Check that `.env` won't be committed:

```bash
git status
```

You should NOT see `.env` in the list. If you do:

```bash
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
```

### Step 4: Test the application

```bash
# With mock mode (no API calls)
python src/main.py
```

### Step 5: (Optional) Enable production mode

In your `.env` file:

```bash
USE_MOCK=false
```

This will use your actual API key for requests.

---

## Understanding the Current Project

### Does This Project Need an OpenAI API Key?

**For Mock Mode (default):** ❌ NO
- The project works without any API keys
- Uses test patterns and simulated data
- Perfect for demos and development

**For Production Mode:** ✅ YES (when Sora API is available)
- Currently, Sora API is not publicly available
- When it is, you'll need a Sora-specific API key
- Your OpenAI key might work if Sora becomes part of OpenAI's API

### What Can OpenAI API Be Used For?

Even without Sora API, your OpenAI key could be integrated for:

1. **Prompt Enhancement** (using GPT-4)
   - Better automatic prompt revision
   - More intelligent prompt analysis
   
2. **Vision Analysis** (using GPT-4 Vision)
   - Actual video frame analysis
   - Real quality scoring

3. **Future: Sora Integration**
   - When Sora API becomes available

---

## Current Project Status

### ✅ Works Right Now (Mock Mode)
```bash
USE_MOCK=true  # No API key needed
```

The system:
- Generates test pattern videos
- Provides simulated scores
- Demonstrates the complete workflow
- Perfect for learning and development

### 🔮 Future (Production Mode)
```bash
USE_MOCK=false
SORA_API_KEY=your_key_when_available
```

When Sora API is released:
- Real video generation
- Actual 3D reconstruction
- Live agent testing

---


## Quick Commands

### Create .env file:
```bash
cp env-template.txt .env
nano .env  # Edit with your key
```

### Check if .env is gitignored:
```bash
git check-ignore .env
# Should output: .env
```

### Run in mock mode (safe, no API calls):
```bash
python src/main.py
```

### Check your OpenAI usage:
```bash
open https://platform.openai.com/usage
```

---

## FAQ

**Q: Do I need an API key to use this project?**  
A: No! It works in mock mode by default.

**Q: What's mock mode?**  
A: It simulates video generation without calling real APIs. Perfect for demos.

**Q: When should I use production mode?**  
A: When Sora API is publicly available and you want real video generation.

**Q: I exposed my key. What now?**  
A: Revoke it immediately at https://platform.openai.com/api-keys

**Q: Can I use my OpenAI key for this project?**  
A: You can, but Sora API isn't public yet. For now, use mock mode.

---

## Getting Help

- Read: [SECURITY.md](SECURITY.md)
- Check: [QUICKSTART.md](QUICKSTART.md)
- Ask: Open an issue on GitHub

**Remember**: When in doubt, use mock mode! It's safe, fast, and free.

