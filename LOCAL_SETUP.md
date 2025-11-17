# Local Development Setup

This guide helps you set up the application locally for testing before deploying to Railway/Vercel.

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or Docker)

## Option 1: Local PostgreSQL

### Install PostgreSQL

**macOS**:
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install postgresql-15
sudo systemctl start postgresql
```

**Windows**:
Download from https://www.postgresql.org/download/windows/

### Create Database

```bash
# Create database
createdb courtlistener

# Or via psql
psql postgres
CREATE DATABASE courtlistener;
\q
```

### Update .env

```bash
cd backend
cat > .env << EOF
DATABASE_URL=postgresql://localhost:5432/courtlistener
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
ENVIRONMENT=development
EOF
```

## Option 2: Docker PostgreSQL (Easier)

### Run PostgreSQL in Docker

```bash
docker run --name courtlistener-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=courtlistener \
  -p 5432:5432 \
  -d postgres:15
```

### Update .env

```bash
cd backend
cat > .env << EOF
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/courtlistener
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
ENVIRONMENT=development
EOF
```

## Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py
```

## Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
echo "VITE_API_URL=http://localhost:8000" > .env.local
```

## Run Locally

### Terminal 1: Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Backend: http://localhost:8000
API Docs: http://localhost:8000/docs

### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

Frontend: http://localhost:3000

## Test Import

With local setup, you can test CSV import:

```bash
cd backend
source venv/bin/activate

# Import from project root (where CSV files are)
python run_import.py ..
```

Or test with just the sample file:
```bash
# The importer will find search_docket-sample.csv automatically
python run_import.py ..
```

## Verify Everything Works

1. **Backend Health**: http://localhost:8000/health
2. **API Docs**: http://localhost:8000/docs
3. **Frontend**: http://localhost:3000
4. **Database**: Check tables created:
   ```bash
   psql courtlistener -c "\dt"
   ```

## Troubleshooting

### PostgreSQL Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Or for Docker
docker ps | grep postgres
```

### Port Already in Use

```bash
# Change port in backend
uvicorn app.main:app --reload --port 8001

# Update frontend .env.local
echo "VITE_API_URL=http://localhost:8001" > frontend/.env.local
```

### Import Errors

- Check CSV files exist in project root
- Verify database has enough space
- Check database logs: `tail -f /var/log/postgresql/postgresql-*.log`

## Next Steps

Once local setup works:
1. ✅ Test import with sample data
2. ✅ Test API endpoints
3. ✅ Test frontend
4. ⏳ Deploy to Railway/Vercel (see DEPLOYMENT.md)

