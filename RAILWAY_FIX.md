# Railway Build Fix

If you're getting "Error creating build plan with Railpack", follow these steps:

## Quick Fix

The issue is that Railway needs explicit configuration to detect Python. I've added the necessary files:

1. ✅ `backend/runtime.txt` - Specifies Python version
2. ✅ `backend/Procfile` - Tells Railway how to run the app
3. ✅ `backend/nixpacks.toml` - Explicit build configuration
4. ✅ Updated `backend/railway.toml` - Better Railway config

## Steps to Fix in Railway

### Option 1: Redeploy (Recommended)

1. In Railway dashboard, go to your service
2. Click **"Redeploy"** button
3. Railway will pick up the new configuration files
4. Build should succeed now

### Option 2: Verify Settings

1. Go to your backend service → **Settings**
2. Check **Root Directory** is set to: `backend`
3. Check **Build Command** (should be auto-detected)
4. Check **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Option 3: Manual Configuration

If auto-detection still fails:

1. Go to Settings → **Build & Deploy**
2. **Build Command**: Leave empty (auto-detected)
3. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Root Directory**: `backend`

## Verify Files Are Committed

Make sure the new files are pushed to GitHub:

```bash
cd "/Users/alexmclaughlin/Desktop/Cursor Projects/Court Listener V@"
git add backend/runtime.txt backend/Procfile backend/nixpacks.toml backend/railway.toml
git commit -m "Add Railway build configuration files"
git push
```

Then Railway will automatically redeploy.

## Common Issues

### Still Getting Build Errors?

1. **Check Railway Logs**: Service → Deployments → Latest → View Logs
2. **Verify Python Detection**: Look for "Detected Python" in logs
3. **Check Requirements**: Ensure `requirements.txt` is in `backend/` directory

### Alternative: Use Dockerfile

If Nixpacks still fails, we can create a Dockerfile instead. Let me know if you need this.

