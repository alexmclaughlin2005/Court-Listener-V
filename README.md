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
- Anthropic Claude Sonnet 4.5 (AI-powered citation risk analysis)
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

## Features

### Citation Risk Analysis
- Automated analysis of case citations to identify citation risks
- Risk categorization: Negative (overruled, questioned), Positive (affirmed, followed), Neutral (cited)
- AI-powered deep analysis using Claude Sonnet 4.5
- Visual citation network mapping with D3.js
- Treatment history timeline

### AI Analysis (Powered by Anthropic Claude Sonnet 4.5)
For cases with negative citation risk, the system provides AI-powered analysis including:
- Overview of why the case is at risk
- Potential impacts on legal theories
- Connection analysis between cited and citing cases
- Practical implications for legal practice

## Documentation

- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Complete getting started guide
- **[TREATMENT_ANALYSIS.md](TREATMENT_ANALYSIS.md)** - Citation treatment analysis documentation
- **[AI_Instructions.md](AI_Instructions.md)** - Technical documentation
- **[AI_System_Prompt.md](AI_System_Prompt.md)** - Architecture overview
- **[RAILWAY_CHECKLIST.md](RAILWAY_CHECKLIST.md)** - Step-by-step Railway setup

