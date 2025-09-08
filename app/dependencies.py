"""Dependency injection for FastAPI."""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.storage.document_store import DocumentStore
from app.storage.vector_store import VectorStore
from app.core.embeddings import EmbeddingModel
from app.core.retrieval import HybridRetriever
from app.core.generator import AnswerGenerator
from app.ingest.watcher import FolderWatcher
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Singleton instances
_document_store: Optional[DocumentStore] = None
_vector_store: Optional[VectorStore] = None
_embedding_model: Optional[EmbeddingModel] = None
_retriever: Optional[HybridRetriever] = None
_generator: Optional[AnswerGenerator] = None
_folder_watcher: Optional[FolderWatcher] = None


async def get_document_store() -> DocumentStore:
    """Get or create document store instance."""
    global _document_store
    if _document_store is None:
        _document_store = DocumentStore(settings.sqlite_path)
        await _document_store.initialize()
    return _document_store


async def get_vector_store() -> VectorStore:
    """Get or create vector store instance."""
    global _vector_store
    if _vector_store is None:
        embedding_model = await get_embedding_model()
        _vector_store = VectorStore(
            index_dir=settings.index_dir,
            embedding_model=embedding_model,
        )
        await _vector_store.initialize()
    return _vector_store


async def get_embedding_model() -> EmbeddingModel:
    """Get or create embedding model instance."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel(settings.model_name)
        await _embedding_model.initialize()
    return _embedding_model


async def get_retriever() -> HybridRetriever:
    """Get or create retriever instance."""
    global _retriever
    if _retriever is None:
        vector_store = await get_vector_store()
        document_store = await get_document_store()
        _retriever = HybridRetriever(
            vector_store=vector_store,
            document_store=document_store,
            reranker_model=settings.reranker_model if not settings.offline_mode else None,
        )
        await _retriever.initialize()
    return _retriever


async def get_generator() -> AnswerGenerator:
    """Get or create answer generator instance."""
    global _generator
    if _generator is None:
        _generator = AnswerGenerator(
            offline_mode=settings.offline_mode,
            provider=settings.active_llm_provider,
            api_key=getattr(settings, f"{settings.active_llm_provider}_api_key", None)
            if settings.active_llm_provider else None,
        )
        await _generator.initialize()
    return _generator


async def get_folder_watcher() -> FolderWatcher:
    """Get or create folder watcher instance."""
    global _folder_watcher
    if _folder_watcher is None:
        document_store = await get_document_store()
        vector_store = await get_vector_store()
        embedding_model = await get_embedding_model()
        
        _folder_watcher = FolderWatcher(
            watch_dirs=settings.parsed_watch_dirs,
            document_store=document_store,
            vector_store=vector_store,
            embedding_model=embedding_model,
        )
    return _folder_watcher


@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager."""
    logger.info("Starting RAG Assistant...")
    
    # Initialize core components
    await get_document_store()
    await get_vector_store()
    await get_embedding_model()
    await get_retriever()
    await get_generator()
    
    # Start folder watcher
    watcher = await get_folder_watcher()
    await watcher.start()
    
    logger.info("RAG Assistant started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down RAG Assistant...")
    
    if _folder_watcher:
        await _folder_watcher.stop()
    
    if _document_store:
        await _document_store.close()
    
    if _vector_store:
        await _vector_store.save()
    
    logger.info("RAG Assistant shut down successfully")


async def verify_api_key() -> str:
    """Verify that an API key is configured when not in offline mode."""
    if settings.offline_mode:
        return "offline"
    
    if not settings.has_llm_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No LLM API key configured. Please set OPENAI_API_KEY, MISTRAL_API_KEY, or ANTHROPIC_API_KEY, or enable OFFLINE_MODE.",
        )
    
    return settings.active_llm_provider