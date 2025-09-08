"""Chat API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import time

from app.dependencies import get_retriever, get_generator, get_document_store
from app.storage.cache import QueryCache
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model."""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    mode: Optional[str] = Field(default=None, pattern="^(offline|llm)$")

    use_cache: bool = Field(default=True)


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str
    citations: list
    contexts: list
    mode: str
    confidence: float
    processing_time: float


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    retriever = Depends(get_retriever),
    generator = Depends(get_generator),
    document_store = Depends(get_document_store),
):
    """Process a chat query."""
    start_time = time.time()
    
    # Initialize cache
    cache = QueryCache(settings.index_dir.parent, settings.cache_ttl)
    
    # Check cache
    if request.use_cache:
        cached = await cache.get(
            request.query,
            request.mode or ("offline" if settings.offline_mode else "llm"),
            request.top_k
        )
        if cached:
            return ChatResponse(**cached, processing_time=time.time() - start_time)
    
    try:
        # Retrieve relevant contexts
        contexts = await retriever.search(
            query=request.query,
            top_k=request.top_k,
            use_reranker=not settings.offline_mode
        )
        
        # Generate answer
        result = await generator.generate(
            query=request.query,
            contexts=contexts,
            mode=request.mode
        )
        
        processing_time = time.time() - start_time
        
        # Save query history in background
        background_tasks.add_task(
            document_store.save_query,
            query_text=request.query,
            response_text=result["answer"],
            mode=result["mode"],
            provider=settings.active_llm_provider,
            top_k=request.top_k,
            processing_time=processing_time,
            citations=[
                {"chunk_id": c["chunk_id"], "score": c.get("score", 0)}
                for c in result.get("citations", [])
            ]
        )
        
        # Cache result
        if request.use_cache:
            await cache.set(
                request.query,
                result["mode"],
                request.top_k,
                {
                    "answer": result["answer"],
                    "citations": result["citations"],
                    "contexts": result["contexts"],
                    "mode": result["mode"],
                    "confidence": result["confidence"],
                }
            )
        
        return ChatResponse(
            answer=result["answer"],
            citations=result["citations"],
            contexts=result["contexts"],
            mode=result["mode"],
            confidence=result["confidence"],
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(
    limit: int = 50,
    document_store = Depends(get_document_store)
):
    """Get chat history."""
    queries = await document_store.get_query_history(limit)
    return {
        "queries": [
            {
                "id": q.id,
                "query": q.query_text,
                "response": q.response_text,
                "mode": q.mode,
                "timestamp": q.timestamp.isoformat(),
                "processing_time": q.processing_time,
            }
            for q in queries
        ]
    }