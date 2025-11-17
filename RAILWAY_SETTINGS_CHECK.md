# Railway Settings Verification

## ✅ Watch Paths (What You're Showing)

**Current Setting**: `/backend/**`

**Status**: ✅ **CORRECT**

This tells Railway to redeploy when any file in the `backend/` directory changes. This is perfect for your setup.

**Optional**: You could also add `/frontend/**` if you want Railway to track frontend changes, but since frontend deploys to Vercel, this isn't necessary.

## 🔍 Other Settings to Verify

### 1. Root Directory
**Location**: Settings → General → Root Directory

**Should be**: `backend`

**Why**: This tells Railway where your Python application lives.

### 2. Build Command
**Location**: Settings → Build & Deploy → Build Command

**Should be**: *(Leave empty or auto-detected)*

**Why**: Railway will auto-detect Python and run `pip install -r requirements.txt` automatically because:
- We have `requirements.txt` in `backend/`
- We have `nixpacks.toml` with build config
- Railway's Nixpacks will handle it

### 3. Start Command
**Location**: Settings → Build & Deploy → Start Command

**Should be**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Why**: This starts your FastAPI application on Railway's assigned port.

### 4. Environment Variables
**Location**: Settings → Variables

**Should have**:
- `DATABASE_URL` - (Auto-set when PostgreSQL is linked)
- `CORS_ORIGINS` - Your frontend URLs
- `ENVIRONMENT=production`

## ✅ Quick Checklist

- [x] Watch Paths: `/backend/**` ✅
- [ ] Root Directory: `backend` (verify)
- [ ] Build Command: Empty/auto (verify)
- [ ] Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (verify)
- [ ] PostgreSQL service linked (verify)
- [ ] Environment variables set (verify)

## 🎯 Summary

Your Watch Paths setting is **perfect**! Just make sure:
1. Root Directory is set to `backend`
2. Start Command matches what's above
3. PostgreSQL is linked to your backend service

Everything else should work automatically with the configuration files we added!

