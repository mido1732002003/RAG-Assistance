"""Document ingestion pipeline."""

import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

from app.ingest.parsers import get_parser
from app.ingest.preprocessor import TextPreprocessor
from app.core.chunker import TextChunker, ChunkConfig
from app.core.language import LanguageDetector
from app.core.deduplication import Deduplicator
from app.storage.document_store import DocumentStore
from app.storage.vector_store import VectorStore
from app.core.embeddings import EmbeddingModel
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class IngestionPipeline:
    """Orchestrates document ingestion process."""
    
    def __init__(
        self,
        document_store: DocumentStore,
        vector_store: VectorStore,
        embedding_model: EmbeddingModel,
    ):
        self.document_store = document_store
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        
        # Initialize components
        self.preprocessor = TextPreprocessor()
        self.chunker = TextChunker(ChunkConfig(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        ))
        self.language_detector = LanguageDetector()
        self.deduplicator = Deduplicator()
    
    async def ingest_file(
        self,
        file_path: Path,
        force: bool = False
    ) -> Dict[str, Any]:
        """Ingest a single file."""
        try:
            logger.info(f"Ingesting file: {file_path}")
            
            # Check if file exists
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return {"status": "error", "message": "File not found"}
            
            # Get parser for file type
            parser = get_parser(file_path)
            if not parser:
                logger.warning(f"No parser available for: {file_path}")
                return {"status": "skipped", "message": "Unsupported file type"}
            
            # Parse document
            content = await parser.parse(file_path)
            if not content or not content.get("text"):
                logger.warning(f"No text extracted from: {file_path}")
                return {"status": "skipped", "message": "No text content"}
            
            # Check for duplicates
            if not force:
                doc = await self.document_store.get_document(file_path)
                if doc:
                    checksum = self.document_store.compute_checksum(content["text"])
                    if doc.checksum == checksum:
                        logger.debug(f"File unchanged: {file_path}")
                        return {"status": "unchanged", "message": "File already indexed"}
            
            # Preprocess text
            processed_text = self.preprocessor.process(content["text"])
            
            # Detect language
            language = self.language_detector.detect(processed_text)
            
            # Add document to store
            document = await self.document_store.add_document(
                file_path=file_path,
                content=processed_text,
                mime_type=content.get("mime_type", "text/plain"),
                language=language,
                title=content.get("title"),
                metadata=content.get("metadata"),
            )
            
            # Chunk text
            chunks = self.chunker.chunk_text(
                processed_text,
                metadata={"document_id": document.id}
            )
            
            # Deduplicate chunks
            chunks = self.deduplicator.deduplicate_chunks(chunks)
            
            if not chunks:
                logger.warning(f"No chunks created for: {file_path}")
                return {"status": "error", "message": "No chunks created"}
            
            # Generate embeddings and store
            chunk_texts = [chunk["text"] for chunk in chunks]
            embedding_ids = [
                f"doc_{document.id}_chunk_{i}" 
                for i in range(len(chunks))
            ]
            
            # Add embeddings to vector store
            await self.vector_store.add_embeddings(
                texts=chunk_texts,
                embedding_ids=embedding_ids,
                metadata=[{"document_id": document.id} for _ in chunks]
            )
            
            # Store chunks in database
            for chunk, embedding_id in zip(chunks, embedding_ids):
                chunk["embedding_id"] = embedding_id
            
            await self.document_store.add_chunks(document.id, chunks)
            
            # Save vector store
            await self.vector_store.save()
            
            logger.info(f"Successfully ingested: {file_path} ({len(chunks)} chunks)")
            
            return {
                "status": "success",
                "document_id": document.id,
                "chunks": len(chunks),
                "language": language,
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest {file_path}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def ingest_directory(
        self,
        directory: Path,
        pattern: str = "*",
        recursive: bool = True
    ) -> Dict[str, Any]:
        """Ingest all files in a directory."""
        results = {
            "total": 0,
            "success": 0,
            "skipped": 0,
            "failed": 0,
            "files": []
        }
        
        # Find files
        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))
        
        results["total"] = len(files)
        logger.info(f"Found {len(files)} files to ingest")
        
        # Process files
        for file_path in files:
            if file_path.is_file():
                result = await self.ingest_file(file_path)
                
                results["files"].append({
                    "path": str(file_path),
                    "status": result["status"]
                })
                
                if result["status"] == "success":
                    results["success"] += 1
                elif result["status"] in ["skipped", "unchanged"]:
                    results["skipped"] += 1
                else:
                    results["failed"] += 1
        
        logger.info(
            f"Ingestion complete: {results['success']} success, "
            f"{results['skipped']} skipped, {results['failed']} failed"
        )
        
        return results
    
    async def delete_document(self, file_path: Path) -> bool:
        """Remove a document from the index."""
        logger.info(f"Deleting document: {file_path}")
        
        # Get document
        doc = await self.document_store.get_document(file_path)
        if not doc:
            logger.warning(f"Document not found: {file_path}")
            return False
        
        # Get chunks to remove from vector store
        chunks = await self.document_store.get_chunks(doc.id)
        embedding_ids = [chunk.embedding_id for chunk in chunks if chunk.embedding_id]
        
        # Remove from vector store
        if embedding_ids:
            await self.vector_store.remove_embeddings(embedding_ids)
            await self.vector_store.save()
        
        # Remove from document store
        await self.document_store.delete_document(file_path)
        
        logger.info(f"Deleted document: {file_path}")
        return True