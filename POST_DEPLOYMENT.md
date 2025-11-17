# Post-Deployment Steps

Congratulations! Your backend is deployed on Railway. Here's what to do next.

## Step 1: Verify Deployment ✅

1. **Check Health Endpoint**:
   ```
   https://your-app.up.railway.app/health
   ```
   Should return: `{"status": "healthy"}`

2. **Check API Docs**:
   ```
   https://your-app.up.railway.app/docs
   ```
   Should show Swagger UI with all endpoints

## Step 2: Initialize Database 🗄️

Your database tables need to be created. Choose one method:

### Option A: Via Railway CLI (Recommended)

```bash
# Install Railway CLI if not already installed
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run database initialization
railway run python init_db.py
```

### Option B: Via Railway Dashboard

1. Go to your backend service → **Deployments** → Latest deployment
2. Click **"View Logs"** → **"Shell"** tab
3. Run: `python init_db.py`

### Option C: Via API Endpoint (After first request)

The database will be initialized automatically when you first access certain endpoints, or you can trigger it manually.

## Step 3: Set Environment Variables 🔧

Go to Railway → Your Backend Service → **Variables** tab:

Add these variables:

```
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
ENVIRONMENT=production
```

**Note**: `DATABASE_URL` should already be set automatically by Railway when you linked PostgreSQL.

## Step 4: Test API Endpoints 🧪

Test your deployed API:

```bash
# Health check
curl https://your-app.up.railway.app/health

# API docs
open https://your-app.up.railway.app/docs
```

## Step 5: Deploy Frontend to Vercel 🚀

Now that backend is working, deploy frontend:

1. Follow **VERCEL_SETUP.md** guide
2. Set `VITE_API_URL` to your Railway backend URL
3. Deploy frontend
4. Update backend CORS with Vercel URL

## Step 6: Import Data 📊

Once database is initialized, you can import CSV data:

### Option A: Via Railway CLI

```bash
# Upload CSV files to Railway (or use existing ones)
railway run python run_import.py /path/to/data
```

### Option B: Via API

```bash
curl -X POST https://your-app.up.railway.app/api/v1/import/start
```

**Note**: For large CSV files, you may need to:
- Upload files to Railway's file system
- Or import from cloud storage (S3, etc.)
- Or use Railway's volume storage

## Step 7: Verify Everything Works ✅

1. ✅ Backend health check returns 200
2. ✅ API docs accessible
3. ✅ Database tables created
4. ✅ Frontend deployed and connected
5. ✅ Can make API calls from frontend

## Troubleshooting

### Database Connection Issues

- Verify PostgreSQL service is linked
- Check `DATABASE_URL` is set
- Ensure database is running

### CORS Errors

- Update `CORS_ORIGINS` in Railway variables
- Include your Vercel frontend URL
- Redeploy backend after changing variables

### Import Issues

- Check Railway logs for errors
- Verify CSV files are accessible
- Ensure database has enough storage

## Next Steps

After everything is working:

1. ⏳ Import sample data (start with small CSV files)
2. ⏳ Test search functionality
3. ⏳ Implement citation endpoints
4. ⏳ Build citation visualization
5. ⏳ Add more features

---

**Need help?** Check Railway logs: Service → Deployments → Latest → View Logs

