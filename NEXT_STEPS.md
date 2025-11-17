# Next Steps - Backend URL Configured

Your backend URL: `https://court-listener-v-production.up.railway.app`

## ⚠️ Current Issue: 502 Error

The backend is deployed but returning 502 errors. This means the app isn't starting properly.

## 🔧 Immediate Fix: Initialize Database

The most likely cause is that the database tables haven't been created yet.

### Quick Fix:

```bash
# Install Railway CLI (if not installed)
npm i -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Initialize database (creates all tables)
railway run python init_db.py
```

### Alternative: Via Railway Dashboard

1. Go to Railway → Your Backend Service
2. Click **"Deployments"** → Latest deployment
3. Click **"View Logs"** → **"Shell"** tab
4. Run: `python init_db.py`

## ✅ After Database is Initialized

### 1. Test Backend

```bash
# Health check
curl https://court-listener-v-production.up.railway.app/health

# Should return: {"status": "healthy"}
```

### 2. Check API Docs

Open in browser:
```
https://court-listener-v-production.up.railway.app/docs
```

### 3. Set Environment Variables

Railway → Backend Service → **Variables**:

```
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=production
```

### 4. Deploy Frontend to Vercel

Follow `VERCEL_ENV_SETUP.md` - I've already configured it with your backend URL!

## 📋 Checklist

- [ ] Initialize database (`railway run python init_db.py`)
- [ ] Verify health endpoint works
- [ ] Check API docs are accessible
- [ ] Set CORS_ORIGINS environment variable
- [ ] Deploy frontend to Vercel
- [ ] Update backend CORS with Vercel URL

## 🐛 If Still Getting 502

Check Railway logs:
1. Railway Dashboard → Backend Service → **View Logs**
2. Look for error messages
3. Common issues:
   - Database connection errors
   - Missing environment variables
   - Import errors

See `TROUBLESHOOTING_502.md` for detailed help.

---

**Your Backend URL**: `https://court-listener-v-production.up.railway.app`
**API Docs**: `https://court-listener-v-production.up.railway.app/docs` (once working)

