# Railway Setup Checklist

Follow these steps to deploy your backend to Railway.

## ✅ Pre-Deployment Checklist

- [ ] Code is ready (all files committed)
- [ ] GitHub repository created
- [ ] Railway account created (https://railway.app)
- [ ] Railway CLI installed (optional, for easier management)

## 🚀 Step-by-Step Railway Setup

### Step 1: Prepare GitHub Repository

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit: CourtListener Case Law Browser"

# Create GitHub repo and push
# (Do this via GitHub web interface or GitHub CLI)
gh repo create "Court-Listener-V" --public
git remote add origin https://github.com/YOUR_USERNAME/Court-Listener-V.git
git push -u origin main
```

### Step 2: Create Railway Project

1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select repository: `Court-Listener-V` (or your repo name)
6. Click **"Deploy Now"**

### Step 3: Add PostgreSQL Database

1. In your Railway project dashboard
2. Click **"+ New"** button
3. Select **"Database"** → **"Add PostgreSQL"**
4. Wait for PostgreSQL to provision (~30 seconds)
5. **Important**: Note the database name shown

### Step 4: Link PostgreSQL to Backend

1. Click on your backend service (the one that was auto-created)
2. Go to **"Settings"** tab
3. Scroll to **"Service Dependencies"**
4. Click **"+ Add Service"**
5. Select your PostgreSQL service
6. Railway will automatically set `DATABASE_URL`

### Step 5: Configure Backend Service

1. Still in backend service → **"Settings"**
2. Set **Root Directory** to: `backend`
3. Railway should auto-detect Python

### Step 6: Set Environment Variables

Go to backend service → **"Variables"** tab, add:

```
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
ENVIRONMENT=production
```

**Note**: `DATABASE_URL` is automatically set when you link PostgreSQL - don't add it manually!

### Step 7: Deploy

1. Railway will auto-deploy on every push to main
2. Or click **"Deploy"** button to deploy manually
3. Wait for deployment (~2-3 minutes)
4. Check **"Deployments"** tab for status

### Step 8: Get Your Backend URL

1. Go to backend service → **"Settings"**
2. Scroll to **"Domains"**
3. Copy the generated URL (e.g., `https://your-app.up.railway.app`)
4. **Save this URL** - you'll need it for Vercel setup!

### Step 9: Initialize Database

Once deployed, initialize the database tables:

**Option A: Via Railway Dashboard**
1. Go to backend service → **"Deployments"** → Latest deployment
2. Click **"View Logs"** → **"Shell"** tab
3. Run: `python init_db.py`

**Option B: Via Railway CLI** (Recommended)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run database initialization
railway run python init_db.py
```

**Option C: Via API** (After first deployment)
```bash
# This will be available once the app is deployed
curl -X POST https://your-app.up.railway.app/api/v1/import/start
```

### Step 10: Verify Deployment

1. **Health Check**: `https://your-app.up.railway.app/health`
   - Should return: `{"status": "healthy"}`

2. **API Docs**: `https://your-app.up.railway.app/docs`
   - Should show Swagger UI

3. **Check Logs**: Railway dashboard → Service → Logs
   - Should show "Application startup complete"

## 🎯 Verification Checklist

- [ ] Backend deployed successfully
- [ ] PostgreSQL database created
- [ ] Database linked to backend service
- [ ] Environment variables set
- [ ] Health endpoint returns 200
- [ ] API docs accessible
- [ ] Database tables initialized

## 🐛 Troubleshooting

### Deployment Fails

**Check build logs:**
- Go to Deployments → Latest → View Logs
- Look for Python/package errors
- Verify `requirements.txt` is correct

**Common issues:**
- Missing `requirements.txt` → Add it
- Wrong Python version → Railway auto-detects, but check logs
- Import errors → Check file paths in code

### Database Connection Errors

**Symptoms**: `could not connect to server` errors

**Solutions**:
1. Verify PostgreSQL is linked to backend service
2. Check `DATABASE_URL` is set (should be automatic)
3. Ensure PostgreSQL service is running (green status)
4. Try re-linking PostgreSQL service

### Import/Init Errors

**Symptoms**: Database initialization fails

**Solutions**:
1. Check database has enough storage
2. Verify PostgreSQL version (should be 15+)
3. Check Railway logs for specific errors
4. Try running init manually via Railway shell

## 📊 Monitoring

### View Logs
- Railway dashboard → Service → Logs
- Real-time logs available
- Historical logs in Deployments tab

### Monitor Usage
- Dashboard → Usage tab
- Track database storage
- Monitor compute usage

### Check Database
- PostgreSQL service → Metrics
- View connection count
- Monitor query performance

## 💰 Cost Management

**Free Tier Limits:**
- $5/month credit
- 500 hours compute time
- 1GB database storage

**Upgrade if needed:**
- More storage for large CSV imports
- Better performance for production
- More compute hours

## 🔄 Updating Deployment

Railway auto-deploys on every push to main branch:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

Railway will automatically:
1. Detect the push
2. Build new deployment
3. Deploy to production
4. Keep old deployment as backup

## 📝 Next Steps

After Railway setup is complete:

1. ✅ Save your Railway backend URL
2. ✅ Proceed to Vercel frontend setup (see VERCEL_SETUP.md)
3. ✅ Update Vercel with Railway backend URL
4. ✅ Test full application

---

**Need help?** Check Railway docs: https://docs.railway.app

