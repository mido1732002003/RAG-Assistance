"""SQLAlchemy database models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, Boolean,
    ForeignKey, Index, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import relationship
from pathlib import Path

Base = declarative_base()


class Document(Base):
    """Document metadata model."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    file_path = Column(String(500), unique=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100))
    checksum = Column(String(64), nullable=False)
    language = Column(String(10))
    title = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    indexed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_documents_path", "file_path"),
        Index("idx_documents_checksum", "checksum"),
    )


class Chunk(Base):
    """Text chunk model."""
    
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    start_char = Column(Integer)
    end_char = Column(Integer)
    page_number = Column(Integer)
    metadata_json = Column(Text)  # JSON string for additional metadata
    embedding_id = Column(String(100))  # Reference to FAISS index
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        Index("idx_chunks_document", "document_id"),
        Index("idx_chunks_embedding", "embedding_id"),
    )


class Query(Base):
    """Query history model."""
    
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text)
    mode = Column(String(20))  # "offline" or "llm"
    provider = Column(String(50))  # "openai", "mistral", etc.
    top_k = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    processing_time = Column(Float)
    user_rating = Column(Integer)  # Optional user feedback
    
    __table_args__ = (
        Index("idx_queries_timestamp", "timestamp"),
    )


class Citation(Base):
    """Citation tracking model."""
    
    __tablename__ = "citations"
    
    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, ForeignKey("queries.id"), nullable=False)
    chunk_id = Column(Integer, ForeignKey("chunks.id"), nullable=False)
    relevance_score = Column(Float)
    position = Column(Integer)  # Position in the response
    
    # Relationships
    query = relationship("Query")
    chunk = relationship("Chunk")


def get_engine(db_path: Path) -> AsyncEngine:
    """Create async database engine."""
    return create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        echo=False,
        future=True,
    )