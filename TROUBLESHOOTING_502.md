# Troubleshooting 502 Error

Your backend is deployed but returning 502 "Application failed to respond". This usually means the app crashed on startup.

## Common Causes

### 1. Database Not Initialized (Most Likely)

The app tries to connect to PostgreSQL but tables don't exist yet.

**Fix**: Initialize the database

```bash
# Via Railway CLI
railway run python init_db.py

# Or via Railway Dashboard
# Service → Deployments → Latest → Shell → Run: python init_db.py
```

### 2. Missing Environment Variables

Check Railway → Your Service → Variables:

Required:
- `DATABASE_URL` (should be auto-set by Railway)
- `CORS_ORIGINS` (optional but recommended)
- `ENVIRONMENT` (optional)

### 3. Database Connection Issues

**Check Railway Logs**:
1. Go to Railway → Your Backend Service
2. Click **"View Logs"**
3. Look for database connection errors

**Common errors**:
- `could not connect to server` → PostgreSQL not linked
- `relation "search_court" does not exist` → Database not initialized
- `password authentication failed` → Wrong DATABASE_URL

### 4. Application Startup Error

Check logs for Python errors:
- Import errors
- Missing dependencies
- Configuration errors

## Step-by-Step Fix

### Step 1: Check Railway Logs

1. Railway Dashboard → Your Backend Service
2. Click **"View Logs"** or **"Deployments"** → Latest → **"View Logs"**
3. Look for error messages at the bottom

### Step 2: Verify PostgreSQL is Linked

1. Railway Dashboard → Your Backend Service → **Settings**
2. Scroll to **"Service Dependencies"**
3. Verify PostgreSQL service is listed
4. If not, click **"+ Add Service"** → Select PostgreSQL

### Step 3: Initialize Database

```bash
# Install Railway CLI if needed
npm i -g @railway/cli

# Login and link
railway login
railway link

# Initialize database
railway run python init_db.py
```

### Step 4: Check Environment Variables

Railway → Your Backend Service → **Variables**:

```
DATABASE_URL=postgresql://... (should be auto-set)
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=production
```

### Step 5: Redeploy

After fixing issues:
1. Railway → Your Backend Service
2. Click **"Redeploy"**
3. Watch logs for startup messages

## Expected Logs (When Working)

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Still Not Working?

1. **Check Railway Logs** - Most important!
2. **Verify DATABASE_URL** is set correctly
3. **Try redeploying** after fixes
4. **Check PostgreSQL** is running (green status)

---

**Next**: Once backend is working, proceed to Vercel frontend setup!

