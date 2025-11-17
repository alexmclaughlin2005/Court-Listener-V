# Railway Setup Guide

## Step 1: Create Railway Account & Project

1. Go to https://railway.app
2. Sign up/login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Connect your GitHub repository
6. Select the repository: `Court Listener V@`

## Step 2: Add PostgreSQL Service

1. In your Railway project, click "+ New"
2. Select "Database" → "Add PostgreSQL"
3. Railway will automatically create a PostgreSQL database
4. **Important**: Note the database name (you'll need it later)

## Step 3: Configure Backend Service

1. Railway should auto-detect the `backend/` directory
2. If not, go to Settings → Root Directory → Set to `backend`
3. Railway will auto-detect Python and install dependencies

## Step 4: Set Environment Variables

In Railway, go to your backend service → Variables tab, add:

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
ENVIRONMENT=production
```

**Note**: `DATABASE_URL` is automatically set by Railway when you link the PostgreSQL service.

To link PostgreSQL:
1. Go to your backend service
2. Click "+ New" → "Add Database" → Select your PostgreSQL service
3. Railway will automatically set `DATABASE_URL`

## Step 5: Deploy

1. Railway will auto-deploy on push to main branch
2. Or click "Deploy" button to deploy manually
3. Wait for deployment to complete
4. Copy the generated URL (e.g., `https://your-app.up.railway.app`)

## Step 6: Initialize Database

Once deployed, initialize the database tables:

### Option A: Via Railway CLI (Recommended)

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

### Option B: Via Railway Dashboard

1. Go to your backend service
2. Click "Deployments" → Latest deployment
3. Click "View Logs" → "Shell"
4. Run: `python init_db.py`

### Option C: Via API (After deployment)

The database will be initialized automatically when you first access the API, or you can trigger it via:

```bash
curl -X POST https://your-app.up.railway.app/api/v1/import/start
```

## Step 7: Verify Deployment

1. Health check: `https://your-app.up.railway.app/health`
2. API docs: `https://your-app.up.railway.app/docs`

## Step 8: Import Data

Once database is initialized, import CSV data:

```bash
# Via Railway CLI
railway run python run_import.py /path/to/data

# Or trigger via API (if you upload CSVs to Railway)
curl -X POST https://your-app.up.railway.app/api/v1/import/start
```

**Note**: For large CSV files, you may want to:
- Upload CSVs to Railway's file system
- Or use Railway's volume storage
- Or import directly from S3/cloud storage

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL service is linked to backend service
- Check `DATABASE_URL` is set correctly
- Ensure database is running (check Railway dashboard)

### Import Issues
- Check Railway logs: `railway logs`
- Verify CSV files are accessible
- Check database has enough storage (upgrade plan if needed)

### Deployment Issues
- Check build logs in Railway dashboard
- Verify `requirements.txt` is correct
- Ensure Python version is compatible (Railway auto-detects)

## Next: Vercel Frontend Setup

After Railway backend is set up, proceed to `VERCEL_SETUP.md` for frontend deployment.

