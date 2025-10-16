# Railway Deployment Guide

## ✅ Pre-Deployment Checklist

This project is **Railway-ready**! All configuration files are in place.

### Files Configured:
- ✅ `Procfile` - Gunicorn production server
- ✅ `runtime.txt` - Python 3.11.9
- ✅ `requirements.txt` - Lightweight dependencies (~150MB)
- ✅ `.railwayignore` - Excludes unnecessary files
- ✅ No Dockerfile - Uses Railway's fast Python buildpack

---

## 🚀 Deploy to Railway (5 Minutes)

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Railway deployment ready"
git push origin main
```

### Step 2: Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `sora-demo` repository
5. Railway will auto-detect Python and deploy!

### Step 3: Set Environment Variables
In Railway dashboard → **Variables** tab, add:

```env
OPENAI_API_KEY=your_openai_api_key_here
FLASK_ENV=production
FLASK_DEBUG=False
```

### Step 4: Deploy!
Railway will automatically:
- ✅ Detect `Procfile`
- ✅ Install Python 3.11.9
- ✅ Install dependencies from `requirements.txt`
- ✅ Start with `gunicorn`
- ✅ Assign a public URL

**Build time:** ~2-3 minutes

---

## 🔧 Configuration Details

### Procfile
```
web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 src.main:app
```

- **2 workers** - Good balance for Railway's resources
- **120s timeout** - Allows for Sora API calls
- **Automatic PORT binding** - Railway sets `$PORT` env var

### Dependencies (Lightweight)
- Total size: ~150MB (fast builds!)
- `opencv-python-headless` - No GUI dependencies
- `gunicorn` - Production WSGI server
- `openai` - Sora API client

### What's Excluded:
- ❌ PyTorch (~800MB) - Too large, uses fallback
- ❌ Development tools (pytest, black, flake8)
- ❌ Optional 3D libraries (open3d, trimesh)

---

## 📊 Expected Railway Metrics

### Build Phase:
- **Duration:** 2-3 minutes
- **Size:** ~150MB
- **Status:** ✅ Success

### Runtime:
- **Memory:** ~200-300MB idle
- **Memory:** ~500-800MB during Sora generation
- **CPU:** Low (<10%) idle, bursts during video processing

### Free Tier Limits:
- ✅ 500 hours/month execution
- ✅ Plenty for demo/testing
- ⚠️ Shared resources (may be slower than local)

---

## 🌐 Post-Deployment

### Your App URL:
Railway will give you: `https://sora-demo-production.up.railway.app`

### Test It:
1. Visit the URL
2. Click "Quick Demo" → Should load cube video
3. Click "Reconstruct 3D World" → GPT-4 Vision generates scene
4. Enter a prompt → Generate with Sora API

### Monitoring:
- **Logs:** Railway dashboard → "Deployments" → "View Logs"
- **Metrics:** CPU, Memory, Network graphs
- **Errors:** Real-time error streaming

---

## 🐛 Troubleshooting

### Build Timeout:
- ✅ **Fixed** - We removed heavy dependencies (PyTorch, etc.)
- If still fails: Reduce workers in Procfile to 1

### Memory Errors:
- Upgrade to Railway Pro ($5/month) for more RAM
- Or optimize: Remove depth estimation if unused

### Sora API Errors:
- Check `OPENAI_API_KEY` is set correctly
- Verify API key has Sora access (preview program)

### 404 Errors:
- Ensure `templates/` and `static/` folders are committed
- Check `.railwayignore` isn't excluding necessary files

---

## 🔐 Security Notes

### Environment Variables (Railway):
- ✅ Encrypted at rest
- ✅ Not exposed in logs
- ✅ Separate from source code

### Production Checklist:
- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Use real `SECRET_KEY` (not default)
- [ ] Monitor API usage (OpenAI dashboard)

---

## 💡 Next Steps

### After Successful Deploy:
1. **Test all features** - Generate, reconstruct, agent test
2. **Monitor costs** - OpenAI API usage
3. **Share the link!** - Your API key is safe (server-side only)

### Optional Enhancements:
- Add custom domain (Railway supports this)
- Set up persistent storage (Railway volumes)
- Enable Redis for caching (Railway addons)
- Deploy to multiple regions

---

## 📞 Support

If deployment fails:
- Check Railway build logs for errors
- Verify all files are committed (`git status`)
- Ensure Python version is compatible

**Ready to deploy!** 🚀

