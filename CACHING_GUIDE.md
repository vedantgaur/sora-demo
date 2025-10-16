# Caching System - How It Works

## Overview

Your app now has a **shared caching system** that makes all Sora-generated videos available to all users across deployments!

---

## 🎥 Pre-Cached Demo Videos (Committed to Git)

These videos are **included in the repository** and available to all users immediately:

### 1. Cube Animation Demo
- **File**: `data/samples/demo.mp4` (14KB)
- **Prompt**: "A ball moving left to right"
- **Type**: Local test video (no Sora API)
- **Use**: Quick 3D reconstruction demo

### 2. Man Walking Through Trees
- **File**: `data/generations/796b6b5a7803e5aa/take_1.mp4` (3.4MB)
- **Prompt**: "A man walking through trees"
- **Type**: Real Sora generation
- **Cache**: `data/cache/796b6b5a7803e5aa.json`

### 3. Catapult Launching
- **File**: `data/generations/fec980cf43d9b057/take_1.mp4` (1.8MB)
- **Prompt**: "A medieval catapult launching a projectile in a slow-motion shot"
- **Type**: Real Sora generation
- **Cache**: `data/cache/fec980cf43d9b057.json`

**Total committed video size**: ~5.2MB (safe for Git)

---

## 📦 How Caching Works

### On Railway Deployment:

1. **Initial State**:
   - Pre-cached videos load from Git
   - Dropdown shows 3 demo options immediately
   - No API calls needed for demos

2. **New User Generates Video**:
   ```javascript
   User types: "A dog running in a park"
   ↓
   Backend checks: data/cache/<hash>.json
   ↓
   NOT FOUND → Call Sora API
   ↓
   Save to: data/generations/<hash>/take_1.mp4
   Save cache: data/cache/<hash>.json
   ↓
   Video available for THIS deployment session
   ```

3. **Same User (or different user) requests same prompt**:
   ```javascript
   User types: "A dog running in a park"
   ↓
   Backend checks: data/cache/<hash>.json
   ↓
   FOUND! → Load cached video
   ↓
   No API call, instant response
   ```

### Important: Railway Storage is Ephemeral

⚠️ **Railway's filesystem is temporary** - new deployments reset it!

- ✅ **Pre-committed videos** (demos) → Persist across deployments
- ❌ **User-generated videos** → Lost on next deploy (unless committed)

---

## 💾 Persistence Options

### Option 1: Manual Git Commits (Current)
**Best for**: Curated demo videos, small library

If you generate a great video you want to keep:
```bash
# Add the video to git
git add -f data/generations/<hash>/take_1.mp4
git add -f data/cache/<hash>.json

# Update .gitignore to allow it
# Add this line to .gitignore:
!data/generations/<hash>/

# Commit and deploy
git commit -m "Add demo video: <prompt>"
git push origin main
```

### Option 2: Railway Volumes (Recommended for Production)
**Best for**: Growing library, automatic persistence

```bash
# In Railway dashboard:
1. Add "Volume" service
2. Mount at: /app/data/generations
3. All videos persist automatically!
```

**Cost**: $2/month for 10GB

### Option 3: External Storage (S3/Cloudinary)
**Best for**: Large-scale, CDN delivery

Update `src/sora_handler.py` to upload videos to S3:
```python
# After generating video
s3_url = upload_to_s3(video_path)
# Save s3_url in cache instead of local path
```

### Option 4: Database + Object Storage
**Best for**: Full production app

- Store metadata in PostgreSQL (Railway addon)
- Store videos in S3/R2/Cloudflare
- Fast queries, infinite scale

---

## 🔄 Current Behavior on Railway

### What's Saved:
- ✅ 3 demo videos (Git committed)
- ✅ Cache metadata for demos
- ✅ User videos *during* deployment session

### What's Lost on Redeploy:
- ❌ User-generated videos (not committed to Git)
- ❌ Their cache entries

### User Experience:
1. **Alice** deploys to Railway
2. **Bob** visits, types "A dog running" → Calls Sora API, caches it
3. **Carol** visits, types "A dog running" → Uses Bob's cache! ✅
4. **Alice** redeploys code → Cache resets
5. **Bob** types "A dog running" again → Calls Sora API again ❌

---

## 🎯 Recommended Setup for Your Use Case

Since you want **all users to share cached videos** and you're using **your API key** for everyone:

### Best Solution: Railway Volume

1. **Add Volume in Railway**:
   - Dashboard → Your project → "New" → "Volume"
   - Name: `video-storage`
   - Size: 5GB (plenty for hundreds of videos)
   - Mount path: `/app/data`

2. **Update `src/config.py`**:
   ```python
   # Use Railway volume if available, fallback to local
   DATA_ROOT = Path(os.getenv('DATA_ROOT', '/app/data'))
   ```

3. **Deploy**:
   - Videos persist across deployments ✅
   - All users see each other's cached videos ✅
   - No Git commits needed ✅

**Cost**: Free tier + $2/month for volume

---

## 📊 Cache Statistics

Check your cache with:
```bash
# Count cached prompts
ls data/cache/*.json | wc -l

# Total video storage
du -sh data/generations/

# List all cached prompts
for f in data/cache/*.json; do 
  jq -r .prompt "$f"; 
done
```

---

## 🚀 Frontend Integration

The dropdown automatically loads cached videos:

```javascript
// Fetches from /api/cached_prompts
loadCachedPrompts() {
  // Returns all *.json files in data/cache/
  // Displays as dropdown options
  // Click to load instantly!
}
```

**No code changes needed** - works automatically! 🎉

---

## Summary

- ✅ **3 demo videos committed** (5.2MB total)
- ✅ **All users see cached videos** during session
- ✅ **Add Railway Volume** for permanent cache
- ✅ **No API calls for cached prompts**

**You're ready to deploy!** 🚀

