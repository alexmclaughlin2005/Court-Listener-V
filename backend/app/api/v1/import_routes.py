"""
Import management API endpoints
"""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.services.csv_importer import CSVImporter, run_import
from app.services.sample_data_generator import generate_sample_data
from typing import Optional

router = APIRouter()


@router.post("/sample")
async def import_sample_data(
    courts: int = 5,
    dockets: int = 20,
    clusters: int = 20,
    opinions: int = 25,
    citations: int = 30,
    db: Session = Depends(get_db)
):
    """
    Generate and import sample data for testing

    This creates realistic but minimal sample data:
    - courts: Number of courts (max 5, uses real court IDs)
    - dockets: Number of case dockets
    - clusters: Number of opinion clusters
    - opinions: Number of opinions
    - citations: Number of citation relationships

    Perfect for development and testing before importing full dataset
    """
    try:
        # Check if data already exists
        existing_count = db.execute(text("SELECT COUNT(*) FROM search_court")).scalar()
        if existing_count > 0:
            return {
                "status": "warning",
                "message": f"Database already contains {existing_count} courts. Sample data not imported.",
                "hint": "Use DELETE /api/v1/import/clear to clear existing data first"
            }

        # Generate sample data
        results = generate_sample_data(
            db=db,
            courts=min(courts, 5),
            dockets=dockets,
            clusters=clusters,
            opinions=opinions,
            citations=citations
        )

        return {
            "status": "success",
            "message": "Sample data imported successfully",
            "counts": results,
            "total_records": sum(results.values())
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sample data import failed: {str(e)}")


@router.post("/start")
async def start_import(
    background_tasks: BackgroundTasks,
    data_dir: Optional[str] = None
):
    """
    Start the CSV import process from files

    This runs as a background task and can take many hours.
    Requires CSV files to be available in the specified directory.
    """
    # TODO: Implement proper background task with Celery
    background_tasks.add_task(run_import, data_dir)
    return {
        "status": "started",
        "message": "Import process started in background",
        "warning": "This is a long-running process. Check logs for progress."
    }


@router.get("/status")
async def get_import_status(db: Session = Depends(get_db)):
    """Get current data import status and row counts"""
    try:
        courts_count = db.execute(text("SELECT COUNT(*) FROM search_court")).scalar()
        dockets_count = db.execute(text("SELECT COUNT(*) FROM search_docket")).scalar()
        clusters_count = db.execute(text("SELECT COUNT(*) FROM search_opinioncluster")).scalar()
        opinions_count = db.execute(text("SELECT COUNT(*) FROM search_opinion")).scalar()
        citations_count = db.execute(text("SELECT COUNT(*) FROM search_opinionscited")).scalar()

        total = courts_count + dockets_count + clusters_count + opinions_count + citations_count

        return {
            "status": "success",
            "counts": {
                "courts": courts_count,
                "dockets": dockets_count,
                "opinion_clusters": clusters_count,
                "opinions": opinions_count,
                "citations": citations_count
            },
            "total_records": total,
            "has_data": total > 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.delete("/clear")
async def clear_all_data(
    confirm: bool = False,
    db: Session = Depends(get_db)
):
    """
    Clear all imported data from database

    WARNING: This deletes ALL data! Set confirm=true to proceed.
    """
    if not confirm:
        return {
            "status": "warning",
            "message": "Data not cleared. Set confirm=true to proceed with deletion.",
            "warning": "This will delete ALL data from all tables!"
        }

    try:
        # Delete in reverse order (respect foreign keys)
        db.execute(text("DELETE FROM search_opinionscited"))
        db.execute(text("DELETE FROM search_opinion"))
        db.execute(text("DELETE FROM search_opinioncluster"))
        db.execute(text("DELETE FROM search_docket"))
        db.execute(text("DELETE FROM search_court"))
        db.commit()

        return {
            "status": "success",
            "message": "All data cleared successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")

