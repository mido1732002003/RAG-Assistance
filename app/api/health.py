"""Health check endpoints."""

from fastapi import APIRouter, Depends
from datetime import datetime

from app.dependencies import get_vector_store, get_document_store
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/healthz")
async def health():
    """Basic health check."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/readiness")
async def readiness(
    vector_store = Depends(get_vector_store),
    document_store = Depends(get_document_store)
):
    """Readiness check with component status."""
    try:
        # Check vector store
        vector_stats = vector_store.get_stats()
        
        # Check document store
        doc_count = len(await document_store.list_documents(limit=1))
        
        return {
            "status": "ready",
            "components": {
                "vector_store": {
                    "status": "ready",
                    "vectors": vector_stats["total_vectors"]
                },
                "document_store": {
                    "status": "ready",
                    "documents": doc_count
                },
                "mode": "offline" if settings.offline_mode else "llm",
                "llm_provider": settings.active_llm_provider
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }