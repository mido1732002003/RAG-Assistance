"""UI route handlers."""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.dependencies import get_retriever, get_generator, get_document_store
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Setup templates
templates = Jinja2Templates(directory="app/ui/templates")


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Render chat interface."""
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "offline_mode": settings.offline_mode,
            "llm_provider": settings.active_llm_provider,
            "default_top_k": settings.default_top_k,
        }
    )


@router.post("/chat", response_class=HTMLResponse)
async def chat_submit(
    request: Request,
    query: str = Form(...),
    top_k: int = Form(5),
    mode: str = Form("auto"),
    retriever = Depends(get_retriever),
    generator = Depends(get_generator),
):
    """Handle chat form submission."""
    # Retrieve contexts
    contexts = await retriever.search(query, top_k=top_k)
    
    # Generate answer
    result = await generator.generate(
        query=query,
        contexts=contexts,
        mode=None if mode == "auto" else mode
    )
    
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "query": query,
            "answer": result["answer"],
            "citations": result["citations"],
            "contexts": contexts,
            "mode": result["mode"],
            "confidence": result["confidence"],
            "offline_mode": settings.offline_mode,
            "llm_provider": settings.active_llm_provider,
            "default_top_k": top_k,
        }
    )