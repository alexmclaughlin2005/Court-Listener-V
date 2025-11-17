"""
Admin endpoints for data management
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import os
import httpx
import bz2
import shutil
from typing import Optional

router = APIRouter()

# Configuration
VOLUME_PATH = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "/data")
OPINIONS_URL = "https://storage.courtlistener.com/bulk-data/opinions-2025-10-31.csv.bz2"

# Track download status
download_status = {
    "status": "idle",  # idle, downloading, extracting, complete, error
    "progress": 0,
    "message": "",
    "file_path": None
}

class DownloadResponse(BaseModel):
    status: str
    message: str
    progress: Optional[int] = None
    file_path: Optional[str] = None

@router.get("/download-status", response_model=DownloadResponse)
async def get_download_status():
    """Get current download status"""
    return download_status

def download_opinions_csv():
    """Background task to download opinions CSV"""
    global download_status

    try:
        download_status["status"] = "downloading"
        download_status["progress"] = 0
        download_status["message"] = "Starting download..."

        # Check if volume exists
        if not os.path.exists(VOLUME_PATH):
            download_status["status"] = "error"
            download_status["message"] = f"Volume path {VOLUME_PATH} does not exist"
            return

        output_path = os.path.join(VOLUME_PATH, "opinions-2025-10-31.csv.bz2")

        # Download file using httpx
        download_status["message"] = f"Downloading from {OPINIONS_URL}"
        with httpx.stream("GET", OPINIONS_URL, timeout=None) as response:
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        download_status["progress"] = int((downloaded / total_size) * 100) if total_size else 0

        download_status["status"] = "extracting"
        download_status["message"] = "Extracting compressed file..."
        download_status["progress"] = 0

        # Extract file
        extracted_path = os.path.join(VOLUME_PATH, "opinions-2025-10-31.csv")
        with bz2.BZ2File(output_path, 'rb') as source:
            with open(extracted_path, 'wb') as dest:
                shutil.copyfileobj(source, dest)

        # Clean up compressed file
        os.remove(output_path)

        download_status["status"] = "complete"
        download_status["message"] = "Download and extraction complete"
        download_status["progress"] = 100
        download_status["file_path"] = extracted_path

    except Exception as e:
        download_status["status"] = "error"
        download_status["message"] = str(e)
        download_status["progress"] = 0

@router.post("/download-opinions", response_model=DownloadResponse)
async def start_download_opinions(background_tasks: BackgroundTasks):
    """Start downloading opinions CSV in the background"""
    global download_status

    if download_status["status"] == "downloading":
        raise HTTPException(status_code=400, detail="Download already in progress")

    # Reset status
    download_status = {
        "status": "downloading",
        "progress": 0,
        "message": "Download started",
        "file_path": None
    }

    # Start download in background
    background_tasks.add_task(download_opinions_csv)

    return download_status

@router.get("/volume-info")
async def get_volume_info():
    """Get information about the Railway volume"""
    volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "/data")

    if not os.path.exists(volume_path):
        return {
            "exists": False,
            "path": volume_path,
            "message": "Volume path does not exist"
        }

    # Get directory contents
    files = []
    try:
        for item in os.listdir(volume_path):
            item_path = os.path.join(volume_path, item)
            size = os.path.getsize(item_path) if os.path.isfile(item_path) else 0
            files.append({
                "name": item,
                "size_bytes": size,
                "size_gb": round(size / (1024**3), 2),
                "is_file": os.path.isfile(item_path)
            })
    except Exception as e:
        return {
            "exists": True,
            "path": volume_path,
            "error": str(e)
        }

    return {
        "exists": True,
        "path": volume_path,
        "writable": os.access(volume_path, os.W_OK),
        "files": files,
        "total_files": len(files)
    }
