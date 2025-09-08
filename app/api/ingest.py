"""Ingestion API endpoints."""

import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel

from app.dependencies import get_folder_watcher
from app.ingest.pipeline import IngestionPipeline
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class IngestResponse(BaseModel):
    """Ingestion response model."""
    status: str
    message: str
    document_id: Optional[int] = None
    chunks: Optional[int] = None


@router.post("/file", response_model=IngestResponse)
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    watcher = Depends(get_folder_watcher)
):
    """Upload and ingest a single file."""
    # Save uploaded file temporarily
    temp_dir = Path("./var/uploads")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    temp_path = temp_dir / file.filename
    
    try:
        # Save file
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Ingest file
        result = await watcher.pipeline.ingest_file(temp_path)
        
        if result["status"] == "success":
            # Move to data directory
            data_dir = Path("./data/uploads")
            data_dir.mkdir(parents=True, exist_ok=True)
            final_path = data_dir / file.filename
            
            # Handle duplicates
            if final_path.exists():
                base = final_path.stem
                ext = final_path.suffix
                counter = 1
                while final_path.exists():
                    final_path = data_dir / f"{base}_{counter}{ext}"
                    counter += 1
            
            temp_path.rename(final_path)
            
            return IngestResponse(
                status="success",
                message=f"File ingested successfully",
                document_id=result.get("document_id"),
                chunks=result.get("chunks")
            )
        else:
            # Clean up temp file
            temp_path.unlink()
            return IngestResponse(
                status=result["status"],
                message=result.get("message", "Ingestion failed")
            )
            
    except Exception as e:
        logger.error(f"Failed to ingest uploaded file: {e}")
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/directory")
async def ingest_directory(
    path: str,
    background_tasks: BackgroundTasks,
    watcher = Depends(get_folder_watcher)
):
    """Ingest all files in a directory."""
    dir_path = Path(path)
    
    if not dir_path.exists() or not dir_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid directory path")
    
    # Run ingestion in background
    background_tasks.add_task(
        watcher.pipeline.ingest_directory,
        dir_path,
        recursive=True
    )
    
    return {
        "status": "started",
        "message": f"Ingestion started for {dir_path}"
    }


@router.delete("/document")
async def delete_document(
    file_path: str,
    watcher = Depends(get_folder_watcher)
):
    """Delete a document from the index."""
    path = Path(file_path)
    
    success = await watcher.pipeline.delete_document(path)
    
    if success:
        return {"status": "success", "message": "Document deleted"}
    else:
        raise HTTPException(status_code=404, detail="Document not found")