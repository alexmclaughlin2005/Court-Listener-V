"""
Import management API endpoints
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.csv_importer import CSVImporter, run_import

router = APIRouter()


@router.post("/start")
async def start_import(
    background_tasks: BackgroundTasks,
    data_dir: str = None
):
    """
    Start the CSV import process
    
    This runs as a background task and can take many hours
    """
    # TODO: Implement proper background task with Celery
    background_tasks.add_task(run_import, data_dir)
    return {
        "status": "started",
        "message": "Import process started in background"
    }


@router.get("/status")
async def get_import_status():
    """Get current import status"""
    # TODO: Implement status tracking
    return {
        "status": "unknown",
        "current_table": None,
        "rows_imported": 0,
        "total_rows": 0
    }

