"""Search API endpoints."""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.dependencies import get_retriever
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class SearchResult(BaseModel):
    """Search result model."""
    chunk_id: int
    document_id: int
    text: str
    score: float
    file_path: str
    filename: str
    page_number: Optional[int]


class SearchResponse(BaseModel):
    """Search response model."""
    query: str
    results: List[SearchResult]
    total: int


@router.get("/", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=500),
    top_k: int = Query(default=10, ge=1, le=50),
    retriever = Depends(get_retriever)
):
    """Search for relevant documents."""
    results = await retriever.search(
        query=q,
        top_k=top_k,
        use_reranker=False  # Fast search without reranking
    )
    
    return SearchResponse(
        query=q,
        results=[SearchResult(**r) for r in results],
        total=len(results)
    )