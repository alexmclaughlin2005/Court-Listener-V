"""
FastAPI application entry point
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.database import engine, Base
from app.models import Court, Docket, OpinionCluster, Opinion, OpinionsCited

app = FastAPI(
    title="CourtListener Case Law API",
    description="API for searching case law and analyzing citation networks",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "message": "CourtListener Case Law API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/init-db")
async def initialize_database():
    """
    Initialize database tables (one-time setup)
    WARNING: Only call this once after deployment
    """
    try:
        Base.metadata.create_all(bind=engine)
        return {
            "status": "success",
            "message": "Database tables created successfully",
            "tables": ["courts", "dockets", "opinion_clusters", "opinions", "opinions_cited"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")

