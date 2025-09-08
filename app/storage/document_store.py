"""Document store for managing document metadata."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.storage.models import Document, Chunk, Query, Citation, get_engine
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DocumentStore:
    """Manages document metadata in SQLite."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.engine = None
        self.async_session = None
    
    async def initialize(self):
        """Initialize the document store."""
        self.engine = get_engine(self.db_path)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)
        logger.info(f"Document store initialized at {self.db_path}")
    
    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
    
    def compute_checksum(self, content: str) -> str:
        """Compute SHA256 checksum of content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def add_document(
        self,
        file_path: Path,
        content: str,
        mime_type: str = "text/plain",
        language: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """Add or update a document."""
        async with self.async_session() as session:
            # Check if document exists
            stmt = select(Document).where(Document.file_path == str(file_path))
            result = await session.execute(stmt)
            existing_doc = result.scalar_one_or_none()
            
            checksum = self.compute_checksum(content)
            
            if existing_doc:
                # Update existing document
                if existing_doc.checksum != checksum:
                    existing_doc.checksum = checksum
                    existing_doc.file_size = len(content)
                    existing_doc.mime_type = mime_type
                    existing_doc.language = language
                    existing_doc.title = title or file_path.name
                    existing_doc.modified_at = datetime.utcnow()
                    existing_doc.indexed_at = datetime.utcnow()
                    
                    # Delete old chunks
                    await session.execute(
                        delete(Chunk).where(Chunk.document_id == existing_doc.id)
                    )
                    
                    await session.commit()
                    logger.info(f"Updated document: {file_path}")
                    return existing_doc
                else:
                    logger.debug(f"Document unchanged: {file_path}")
                    return existing_doc
            else:
                # Create new document
                doc = Document(
                    file_path=str(file_path),
                    filename=file_path.name,
                    file_size=len(content),
                    mime_type=mime_type,
                    checksum=checksum,
                    language=language,
                    title=title or file_path.name,
                )
                session.add(doc)
                await session.commit()
                await session.refresh(doc)
                logger.info(f"Added document: {file_path}")
                return doc
    
    async def add_chunks(
        self,
        document_id: int,
        chunks: List[Dict[str, Any]],
    ) -> List[Chunk]:
        """Add chunks for a document."""
        async with self.async_session() as session:
            chunk_objects = []
            
            for i, chunk_data in enumerate(chunks):
                chunk = Chunk(
                    document_id=document_id,
                    chunk_index=i,
                    text=chunk_data["text"],
                    start_char=chunk_data.get("start_char"),
                    end_char=chunk_data.get("end_char"),
                    page_number=chunk_data.get("page_number"),
                    metadata_json=json.dumps(chunk_data.get("metadata", {})),
                    embedding_id=chunk_data.get("embedding_id"),
                )
                session.add(chunk)
                chunk_objects.append(chunk)
            
            await session.commit()
            logger.debug(f"Added {len(chunks)} chunks for document {document_id}")
            return chunk_objects
    
    async def get_document(self, file_path: Path) -> Optional[Document]:
        """Get document by file path."""
        async with self.async_session() as session:
            stmt = select(Document).where(Document.file_path == str(file_path))
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_document_by_id(self, document_id: int) -> Optional[Document]:
        """Get document by ID."""
        async with self.async_session() as session:
            stmt = select(Document).where(Document.id == document_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_chunks(self, document_id: int) -> List[Chunk]:
        """Get all chunks for a document."""
        async with self.async_session() as session:
            stmt = select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index)
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_chunk_by_embedding_id(self, embedding_id: str) -> Optional[Chunk]:
        """Get chunk by embedding ID."""
        async with self.async_session() as session:
            stmt = select(Chunk).where(Chunk.embedding_id == embedding_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    
    async def delete_document(self, file_path: Path) -> bool:
        """Delete a document and its chunks."""
        async with self.async_session() as session:
            stmt = select(Document).where(Document.file_path == str(file_path))
            result = await session.execute(stmt)
            doc = result.scalar_one_or_none()
            
            if doc:
                await session.delete(doc)
                await session.commit()
                logger.info(f"Deleted document: {file_path}")
                return True
            return False
    
    async def list_documents(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """List all documents."""
        async with self.async_session() as session:
            stmt = select(Document).limit(limit).offset(offset).order_by(Document.indexed_at.desc())
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def save_query(
        self,
        query_text: str,
        response_text: str,
        mode: str,
        provider: Optional[str] = None,
        top_k: int = 5,
        processing_time: float = 0.0,
        citations: Optional[List[Dict[str, Any]]] = None,
    ) -> Query:
        """Save a query and its response."""
        async with self.async_session() as session:
            query = Query(
                query_text=query_text,
                response_text=response_text,
                mode=mode,
                provider=provider,
                top_k=top_k,
                processing_time=processing_time,
            )
            session.add(query)
            await session.flush()
            
            # Add citations
            if citations:
                for citation_data in citations:
                    citation = Citation(
                        query_id=query.id,
                        chunk_id=citation_data["chunk_id"],
                        relevance_score=citation_data.get("score", 0.0),
                        position=citation_data.get("position", 0),
                    )
                    session.add(citation)
            
            await session.commit()
            await session.refresh(query)
            return query
    
    async def get_query_history(self, limit: int = 50) -> List[Query]:
        """Get recent query history."""
        async with self.async_session() as session:
            stmt = select(Query).limit(limit).order_by(Query.timestamp.desc())
            result = await session.execute(stmt)
            return result.scalars().all()