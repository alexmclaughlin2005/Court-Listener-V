# Setup Guide - CourtListener Case Law Browser

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or Railway PostgreSQL)
- Git

## Initial Setup

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd "Court Listener V@"
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your database URL
# DATABASE_URL=postgresql://user:password@localhost:5432/courtlistener
```

### 3. Initialize Database

```bash
# Create tables
python init_db.py
```

### 4. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Create environment file
echo "VITE_API_URL=http://localhost:8000" > .env.local
```

## Running Locally

### Backend

```bash
cd backend
source venv/bin/activate  # If not already activated
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000
API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:3000

## Importing Data

### Option 1: Via Python Script

```bash
cd backend
source venv/bin/activate
python run_import.py ../data
```

### Option 2: Via API

```bash
curl -X POST http://localhost:8000/api/v1/import/start
```

**Note**: Importing all data can take 24-48 hours. Start with sample files for testing.

## Deployment

### Railway (Backend)

1. Connect GitHub repository to Railway
2. Select `backend/` directory as root
3. Railway will auto-detect Python and install dependencies
4. Add PostgreSQL service
5. Set environment variables:
   - `DATABASE_URL` (auto-set by Railway PostgreSQL)
   - `CORS_ORIGINS` (your Vercel frontend URL)
   - `ENVIRONMENT=production`

### Vercel (Frontend)

1. Connect GitHub repository to Vercel
2. Select `frontend/` directory as root
3. Set environment variable:
   - `VITE_API_URL` (your Railway backend URL)
4. Deploy

## Testing

### Test Backend

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

### Test Frontend

Open http://localhost:3000 in your browser

## Troubleshooting

### Database Connection Issues

- Check `DATABASE_URL` in `.env`
- Ensure PostgreSQL is running
- Verify credentials

### Import Issues

- Check CSV files exist in `data/` directory
- Verify file permissions
- Check database has enough space (100GB+ recommended)

### Frontend API Errors

- Verify `VITE_API_URL` is set correctly
- Check CORS settings in backend
- Ensure backend is running

## Next Steps

1. ✅ Set up local development environment
2. ⏳ Import sample data (start with small CSV files)
3. ⏳ Test API endpoints
4. ⏳ Build frontend components
5. ⏳ Deploy to Railway/Vercel

