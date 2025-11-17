# CourtListener Case Law Browser with Citation Mapping

A powerful case law search and citation analysis tool built with CourtListener's bulk legal data.

## Project Structure

```
├── backend/          # FastAPI backend (Railway deployment)
├── frontend/         # React + TypeScript frontend (Vercel deployment)
├── data/             # CSV data files (gitignored)
└── docs/             # Documentation
```

## Tech Stack

### Backend
- FastAPI
- PostgreSQL 15+
- SQLAlchemy
- Celery + Redis (for background tasks)
- Python 3.11+

### Frontend
- React 18+
- TypeScript
- D3.js (for citation network visualization)
- TanStack Query (React Query)
- Tailwind CSS

## Getting Started

**🚀 Quick Start**: See [GETTING_STARTED.md](GETTING_STARTED.md) for the complete guide.

### Quick Options

- **Test Locally First** → [LOCAL_SETUP.md](LOCAL_SETUP.md)
- **Deploy to Railway/Vercel** → [DEPLOYMENT.md](DEPLOYMENT.md)
- **5-Minute Quick Start** → [QUICKSTART.md](QUICKSTART.md)

### Setup Scripts

```bash
# Check your setup
./scripts/check_setup.sh

# Auto-setup local environment
./scripts/setup_local.sh
```

## Deployment

- **Backend**: Railway (PostgreSQL + FastAPI) → [RAILWAY_SETUP.md](RAILWAY_SETUP.md)
- **Frontend**: Vercel (React app) → [VERCEL_SETUP.md](VERCEL_SETUP.md)

## Documentation

- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Complete getting started guide
- **[TREATMENT_ANALYSIS.md](TREATMENT_ANALYSIS.md)** - Citation treatment analysis documentation
- **[AI_Instructions.md](AI_Instructions.md)** - Technical documentation
- **[AI_System_Prompt.md](AI_System_Prompt.md)** - Architecture overview
- **[RAILWAY_CHECKLIST.md](RAILWAY_CHECKLIST.md)** - Step-by-step Railway setup

