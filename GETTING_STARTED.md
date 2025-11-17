# Getting Started - Complete Guide

Welcome! This guide will help you get the CourtListener Case Law Browser up and running.

## 🎯 Quick Decision Tree

**Choose your path:**

1. **I want to test locally first** → See [LOCAL_SETUP.md](LOCAL_SETUP.md)
2. **I want to deploy to Railway/Vercel now** → See [DEPLOYMENT.md](DEPLOYMENT.md)
3. **I just want to see it work quickly** → See [QUICKSTART.md](QUICKSTART.md)

## 📋 Recommended Order

### Step 1: Local Testing (Recommended First)

Test everything locally before deploying:

```bash
# Run setup script
./scripts/setup_local.sh

# Or follow manual setup in LOCAL_SETUP.md
```

**Why test locally first?**
- Faster iteration
- No deployment costs
- Easier debugging
- Test CSV import with sample data

### Step 2: Railway Backend Deployment

Once local testing works:

1. Follow [RAILWAY_SETUP.md](RAILWAY_SETUP.md)
2. Deploy backend to Railway
3. Initialize database on Railway
4. Test API endpoints

### Step 3: Vercel Frontend Deployment

After backend is deployed:

1. Follow [VERCEL_SETUP.md](VERCEL_SETUP.md)
2. Deploy frontend to Vercel
3. Connect frontend to Railway backend
4. Test full application

### Step 4: Import Data

Once both are deployed:

- Import CSV files via Railway CLI or API
- Monitor import progress
- Verify data in database

## 🚀 Fastest Path to Running

### Option A: Local (5 minutes)

```bash
# 1. Setup
./scripts/setup_local.sh

# 2. Start backend (Terminal 1)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# 3. Start frontend (Terminal 2)
cd frontend
npm run dev

# 4. Open browser
open http://localhost:3000
```

### Option B: Railway + Vercel (30 minutes)

1. Follow [RAILWAY_SETUP.md](RAILWAY_SETUP.md) (15 min)
2. Follow [VERCEL_SETUP.md](VERCEL_SETUP.md) (15 min)
3. Done! 🎉

## 📚 Documentation Index

- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute quick start
- **[LOCAL_SETUP.md](LOCAL_SETUP.md)** - Local development setup
- **[RAILWAY_SETUP.md](RAILWAY_SETUP.md)** - Railway backend deployment
- **[VERCEL_SETUP.md](VERCEL_SETUP.md)** - Vercel frontend deployment
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide
- **[AI_Instructions.md](AI_Instructions.md)** - Technical documentation
- **[AI_System_Prompt.md](AI_System_Prompt.md)** - Architecture overview

## ✅ Pre-Flight Checklist

Before starting, make sure you have:

- [ ] GitHub account (for deployment)
- [ ] Railway account (free tier works)
- [ ] Vercel account (free tier works)
- [ ] PostgreSQL (local or Railway)
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] CSV data files (you already have these!)

## 🆘 Need Help?

### Common Issues

**Database connection errors:**
- Check `DATABASE_URL` in `.env`
- Verify PostgreSQL is running
- Check credentials

**Import fails:**
- Verify CSV files exist
- Check file permissions
- Review import logs

**Frontend can't connect:**
- Check `VITE_API_URL` is set
- Verify backend is running
- Check CORS settings

### Check Your Setup

```bash
# Run setup checker
./scripts/check_setup.sh
```

## 🎯 Next Steps After Setup

1. ✅ Import sample data
2. ✅ Test search functionality
3. ✅ Test citation endpoints
4. ⏳ Build citation visualization
5. ⏳ Add more features

## 📞 Support

- Check documentation files
- Review error logs
- Test locally first
- Check Railway/Vercel logs

---

**Ready to start?** Choose your path above and follow the guide! 🚀

