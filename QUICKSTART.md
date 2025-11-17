# Quick Start Guide

## Get Up and Running in 5 Minutes

### 1. Backend Setup (2 minutes)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:
```bash
cat > .env << EOF
DATABASE_URL=postgresql://user:password@localhost:5432/courtlistener
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
EOF
```

Initialize database:
```bash
python init_db.py
```

Start server:
```bash
uvicorn app.main:app --reload
```

✅ Backend running at http://localhost:8000

### 2. Frontend Setup (2 minutes)

```bash
cd frontend
npm install
npm run dev
```

✅ Frontend running at http://localhost:3000

### 3. Test Import (1 minute)

Import a sample CSV file:
```bash
cd backend
python run_import.py ..
```

Or test with the sample docket file:
```bash
# The importer will automatically find search_docket-sample.csv
```

## Verify It Works

1. **Backend Health**: http://localhost:8000/health
2. **API Docs**: http://localhost:8000/docs
3. **Frontend**: http://localhost:3000

## Next Steps

- Import more data: `python backend/run_import.py ..`
- Check API endpoints: http://localhost:8000/docs
- Read full docs: `SETUP.md` and `AI_Instructions.md`

