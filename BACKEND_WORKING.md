# Backend Successfully Deployed! 🎉

Your backend is now live at: `https://court-listener-v-production.up.railway.app`

## ✅ Current Status

- ✅ Backend deployed successfully
- ✅ Application starting without errors
- ⏳ Database initialization (next step)

## 🔧 Next Steps

### Step 1: Initialize Database

The database tables need to be created. Run:

```bash
# Install Railway CLI if not installed
npm i -g @railway/cli

# Login and link
railway login
railway link

# Initialize database (creates all tables)
railway run python init_db.py
```

**Alternative**: Via Railway Dashboard
1. Go to Railway → Backend Service → Deployments → Latest
2. Click "View Logs" → "Shell" tab
3. Run: `python init_db.py`

### Step 2: Test API Endpoints

After database initialization:

```bash
# Health check
curl https://court-listener-v-production.up.railway.app/health

# Root endpoint
curl https://court-listener-v-production.up.railway.app/

# API docs (open in browser)
open https://court-listener-v-production.up.railway.app/docs
```

### Step 3: Set Environment Variables

Railway → Backend Service → **Variables**:

Add:
```
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=production
```

(You'll add your Vercel URL to CORS_ORIGINS after frontend deployment)

### Step 4: Deploy Frontend to Vercel

Now that backend is working:

1. Follow `VERCEL_ENV_SETUP.md`
2. Set `VITE_API_URL=https://court-listener-v-production.up.railway.app`
3. Deploy frontend
4. Update backend CORS with Vercel URL

## 📊 API Endpoints Available

Once database is initialized, these endpoints will work:

- `GET /health` - Health check
- `GET /` - Root endpoint
- `GET /docs` - API documentation (Swagger UI)
- `GET /api/v1/search/cases` - Search cases
- `GET /api/v1/citations/outbound/{opinion_id}` - Get outbound citations
- `GET /api/v1/citations/inbound/{opinion_id}` - Get inbound citations
- `GET /api/v1/citations/network/{opinion_id}` - Get citation network
- `GET /api/v1/citations/analytics/{opinion_id}` - Get citation analytics
- `GET /api/v1/citations/most-cited` - Get most cited cases

## 🎯 Quick Checklist

- [x] Backend deployed successfully
- [ ] Initialize database (`railway run python init_db.py`)
- [ ] Test health endpoint
- [ ] Set CORS_ORIGINS environment variable
- [ ] Deploy frontend to Vercel
- [ ] Update CORS with Vercel URL
- [ ] Test full application

## 🐛 Troubleshooting

### Database Connection Errors

If you see database errors after initialization:
- Verify PostgreSQL service is linked to backend
- Check `DATABASE_URL` is set (should be automatic)
- Ensure database is running (green status in Railway)

### API Not Responding

- Check Railway logs for errors
- Verify database tables were created
- Test health endpoint first

---

**Backend URL**: `https://court-listener-v-production.up.railway.app`
**API Docs**: `https://court-listener-v-production.up.railway.app/docs`

