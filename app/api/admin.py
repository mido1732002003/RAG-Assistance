"""Admin API endpoints."""

import shutil
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from app.dependencies import get_vector_store, get_document_store, get_retriever
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/backup")
async def create_backup(
    background_tasks: BackgroundTasks,
    vector_store = Depends(get_vector_store),
    document_store = Depends(get_document_store)
):
    """Create a backup snapshot."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    snapshot_dir = Path("./snapshots") / f"backup_{timestamp}"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Save vector store
        await vector_store.save()
        
        # Copy files
        shutil.copy2(settings.sqlite_path, snapshot_dir / "rag.db")
        shutil.copy2(settings.index_dir / "faiss.index", snapshot_dir / "faiss.index")
        shutil.copy2(settings.index_dir / "id_map.pkl", snapshot_dir / "id_map.pkl")
        
        # Create manifest
        manifest = {
            "timestamp": timestamp,
            "version": "0.1.0",
            "stats": vector_store.get_stats(),
        }
        
        import json
        with open(snapshot_dir / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
        
        # Create archive
        archive_path = Path("./snapshots") / f"backup_{timestamp}.tar.gz"
        shutil.make_archive(
            str(archive_path.with_suffix("")),
            "gztar",
            snapshot_dir
        )
        
        # Clean up directory
        shutil.rmtree(snapshot_dir)
        
        return {
            "status": "success",
            "snapshot": f"backup_{timestamp}.tar.gz",
            "path": str(archive_path)
        }
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        if snapshot_dir.exists():
            shutil.rmtree(snapshot_dir)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore/{snapshot_name}")
async def restore_backup(
    snapshot_name: str,
    vector_store = Depends(get_vector_store),
):
    """Restore from a backup snapshot."""
    archive_path = Path("./snapshots") / snapshot_name
    
    if not archive_path.exists():
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    temp_dir = Path("./var/restore_temp")
    
    try:
        # Extract archive
        shutil.unpack_archive(archive_path, temp_dir)
        
        # Backup current state
        backup_dir = Path("./var/restore_backup")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        if settings.sqlite_path.exists():
            shutil.copy2(settings.sqlite_path, backup_dir / "rag.db.bak")
        if (settings.index_dir / "faiss.index").exists():
            shutil.copy2(settings.index_dir / "faiss.index", backup_dir / "faiss.index.bak")
        if (settings.index_dir / "id_map.pkl").exists():
            shutil.copy2(settings.index_dir / "id_map.pkl", backup_dir / "id_map.pkl.bak")
        
        # Restore files
        shutil.copy2(temp_dir / "rag.db", settings.sqlite_path)
        shutil.copy2(temp_dir / "faiss.index", settings.index_dir / "faiss.index")
        shutil.copy2(temp_dir / "id_map.pkl", settings.index_dir / "id_map.pkl")
        
        # Reload vector store
        await vector_store.load()
        
        # Clean up
        shutil.rmtree(temp_dir)
        shutil.rmtree(backup_dir)
        
        return {
            "status": "success",
            "message": f"Restored from {snapshot_name}"
        }
        
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        
        # Try to restore backup
        if backup_dir.exists():
            if (backup_dir / "rag.db.bak").exists():
                shutil.copy2(backup_dir / "rag.db.bak", settings.sqlite_path)
            if (backup_dir / "faiss.index.bak").exists():
                shutil.copy2(backup_dir / "faiss.index.bak", settings.index_dir / "faiss.index")
            if (backup_dir / "id_map.pkl.bak").exists():
                shutil.copy2(backup_dir / "id_map.pkl.bak", settings.index_dir / "id_map.pkl")
        
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rebuild-index")
async def rebuild_index(
    background_tasks: BackgroundTasks,
    retriever = Depends(get_retriever)
):
    """Rebuild search indices."""
    background_tasks.add_task(retriever.rebuild_bm25_index)
    
    return {
        "status": "started",
        "message": "Index rebuild started in background"
    }


@router.delete("/cache")
async def clear_cache():
    """Clear all caches."""
    from app.storage.cache import QueryCache
    
    cache = QueryCache(settings.index_dir.parent, settings.cache_ttl)
    await cache.clear()
    
    return {"status": "success", "message": "Cache cleared"}