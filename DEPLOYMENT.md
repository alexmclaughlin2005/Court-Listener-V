# Complete Deployment Guide

This guide walks you through deploying the entire application to Railway (backend) and Vercel (frontend).

## Overview

- **Backend**: Railway (PostgreSQL + FastAPI)
- **Frontend**: Vercel (React + TypeScript)
- **Total Time**: ~30 minutes

## Part 1: Railway Backend Setup

See `RAILWAY_SETUP.md` for detailed instructions.

**Quick Steps**:
1. Create Railway account
2. Create new project from GitHub
3. Add PostgreSQL service
4. Configure backend service (root: `backend/`)
5. Set environment variables
6. Deploy
7. Initialize database

## Part 2: Vercel Frontend Setup

See `VERCEL_SETUP.md` for detailed instructions.

**Quick Steps**:
1. Create Vercel account
2. Import GitHub repository
3. Configure project (root: `frontend/`)
4. Set `VITE_API_URL` environment variable
5. Deploy
6. Update backend CORS settings

## Part 3: Import Data

Once both are deployed:

### Option 1: Via Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and link
railway login
railway link

# Upload CSV files to Railway (or use existing ones)
# Then run import
railway run python run_import.py /path/to/data
```

### Option 2: Via API Endpoint

```bash
# Start import
curl -X POST https://your-backend.up.railway.app/api/v1/import/start

# Check status
curl https://your-backend.up.railway.app/api/v1/import/status
```

## Verification Checklist

- [ ] Railway backend deployed and accessible
- [ ] PostgreSQL database created and linked
- [ ] Database tables initialized
- [ ] Vercel frontend deployed
- [ ] Frontend can connect to backend API
- [ ] CORS configured correctly
- [ ] Data import started (if applicable)

## Troubleshooting

### Backend Issues

**Problem**: Database connection errors
- **Solution**: Verify PostgreSQL is linked, check `DATABASE_URL`

**Problem**: Import fails
- **Solution**: Check Railway logs, verify CSV files accessible

**Problem**: CORS errors
- **Solution**: Update `CORS_ORIGINS` in Railway environment variables

### Frontend Issues

**Problem**: API calls fail
- **Solution**: Verify `VITE_API_URL` is set correctly

**Problem**: Build fails
- **Solution**: Check Vercel build logs, verify dependencies

## Monitoring

### Railway
- View logs: Railway dashboard → Service → Logs
- Monitor usage: Dashboard → Usage
- Check database: PostgreSQL service → Metrics

### Vercel
- View logs: Vercel dashboard → Deployments → Logs
- Monitor analytics: Analytics tab
- Check performance: Speed Insights

## Cost Estimates

### Railway
- **Free Tier**: $5/month credit
- **PostgreSQL**: ~$5/month for small database
- **Backend**: Free on free tier (limited usage)

### Vercel
- **Free Tier**: Generous for small projects
- **Pro**: $20/month for production (optional)

**Total**: ~$5-10/month for small-scale deployment

## Next Steps

1. ✅ Complete Railway setup
2. ✅ Complete Vercel setup
3. ✅ Import initial data
4. ⏳ Test all features
5. ⏳ Monitor performance
6. ⏳ Scale as needed

