# AI System Prompt - CourtListener Case Law Browser

## Project Overview

This is a **Case Law Search and Citation Network Analysis** application built with CourtListener's bulk legal data. The application enables users to search through 10M+ legal opinions and visualize citation relationships between cases.

## High-Level Architecture

### Deployment
- **Backend**: Railway (PostgreSQL + FastAPI)
- **Frontend**: Vercel (React + TypeScript)
- **Repository**: GitHub (monorepo with backend/ and frontend/ directories)

### Tech Stack

**Backend:**
- FastAPI (Python web framework)
- PostgreSQL 15+ (database)
- SQLAlchemy (ORM)
- Celery + Redis (background tasks, planned)
- Python 3.11+

**Frontend:**
- React 18+ with TypeScript
- Vite (build tool)
- D3.js (citation network visualization)
- TanStack Query (data fetching)
- Tailwind CSS (styling)
- React Router (routing)

## Project Structure

```
Court Listener V@/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   │   └── v1/         # API v1 endpoints
│   │   ├── core/           # Core configuration (database, config)
│   │   ├── models/         # SQLAlchemy database models
│   │   └── services/       # Business logic (CSV import, etc.)
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment variables template
│
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── pages/         # Page components
│   │   └── components/    # Reusable components (to be created)
│   ├── package.json       # Node dependencies
│   └── vite.config.ts     # Vite configuration
│
├── data/                  # CSV data files (gitignored)
│   └── *.csv             # CourtListener bulk data files
│
├── AI_Instructions.md     # Detailed technical documentation
├── AI_System_Prompt.md    # This file - high-level overview
└── README.md              # User-facing README
```

## Core Data Model

The application uses CourtListener's database schema with these key tables:

1. **search_court** - Court information (~1K rows)
2. **search_docket** - Case dockets (~30M rows)
3. **search_opinioncluster** - Opinion clusters (~10M rows)
4. **search_opinion** - Individual opinions (~15M rows)
5. **search_opinionscited** - Citation graph edges (~70M rows) ⭐ **THE KILLER FEATURE**

### Relationships
- Court → Docket (one-to-many)
- Docket → OpinionCluster (one-to-many)
- OpinionCluster → Opinion (one-to-many: lead, concurrence, dissent)
- Opinion → Opinion (many-to-many via OpinionsCited: citation graph)

## Key Features

1. **Case Search** - Full-text search across opinions
2. **Citation Mapping** - See what cases cite and are cited by a case
3. **Citation Network Visualization** - Interactive D3.js graph
4. **Citation Analytics** - Timeline, most cited cases, related cases

## Development Workflow

1. **Backend Development**: Work in `backend/app/`
2. **Frontend Development**: Work in `frontend/src/`
3. **Database Changes**: Update models in `backend/app/models/`, use Alembic for migrations
4. **API Changes**: Add routes in `backend/app/api/v1/`

## Important Files

- `AI_Instructions.md` - **READ THIS FIRST** - Detailed technical documentation
- `courtlistener-caselaw-citation-plan.md` - Original project plan
- `backend/app/models/` - Database schema definitions
- `backend/app/services/csv_importer.py` - CSV import logic
- `backend/app/api/v1/` - API endpoints

## Environment Variables

**Backend** (Railway):
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection (for Celery)
- `CORS_ORIGINS` - Allowed frontend origins
- `ENVIRONMENT` - development/production

**Frontend** (Vercel):
- `VITE_API_URL` - Backend API URL

## Current Status

- ✅ Project structure created
- ✅ Database models defined
- ✅ Basic API endpoints scaffolded
- ✅ Frontend structure created
- ⏳ CSV import system (needs testing)
- ⏳ Citation queries (needs implementation)
- ⏳ Frontend components (needs implementation)

## Next Steps

1. Set up Railway PostgreSQL database
2. Test CSV import with sample data
3. Implement citation query endpoints
4. Build frontend citation visualization
5. Deploy to production

## How to Create/Update Instruction Files

When working on this project, maintain these instruction files:

1. **AI_System_Prompt.md** (this file):
   - High-level overview
   - Architecture decisions
   - Project structure
   - Deployment info

2. **AI_Instructions.md**:
   - Detailed technical documentation
   - File-by-file explanations
   - Service descriptions
   - API endpoint documentation
   - Database schema details
   - Dependencies and their purposes

Both files should be updated whenever:
- New features are added
- Architecture changes
- New dependencies are added
- Services are refactored
- API endpoints change

