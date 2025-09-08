"""Hybrid retrieval combining vector search and BM25."""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from app.storage.vector_store import VectorStore
from app.storage.document_store import DocumentStore
from app.utils.logging import get_logger

logger = get_logger(__name__)


class HybridRetriever:
    """Combines vector similarity and BM25 for hybrid search."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        document_store: DocumentStore,
        reranker_model: Optional[str] = None,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
    ):
        self.vector_store = vector_store
        self.document_store = document_store
        self.reranker_model_name = reranker_model
        self.reranker = None
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.bm25_index = None
        self.chunk_texts = []
        self.chunk_ids = []
    
    async def initialize(self):
        """Initialize retriever components."""
        # Load reranker if specified
        if self.reranker_model_name:
            logger.info(f"Loading reranker: {self.reranker_model_name}")
            self.reranker = CrossEncoder(self.reranker_model_name)
        
        # Build BM25 index
        await self.rebuild_bm25_index()
    
    async def rebuild_bm25_index(self):
        """Rebuild BM25 index from all chunks."""
        logger.info("Building BM25 index...")
        
        # Get all documents
        documents = await self.document_store.list_documents(limit=10000)
        
        self.chunk_texts = []
        self.chunk_ids = []
        
        for doc in documents:
            chunks = await self.document_store.get_chunks(doc.id)
            for chunk in chunks:
                self.chunk_texts.append(chunk.text)
                self.chunk_ids.append(chunk.embedding_id)
        
        if self.chunk_texts:
            # Tokenize for BM25
            tokenized_corpus = [text.lower().split() for text in self.chunk_texts]
            self.bm25_index = BM25Okapi(tokenized_corpus)
            logger.info(f"BM25 index built with {len(self.chunk_texts)} chunks")
        else:
            self.bm25_index = None
            logger.warning("No chunks available for BM25 index")
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        use_reranker: bool = True,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search."""
        results = []
        
        # Vector search
        vector_results = await self.vector_store.search(query, top_k=top_k*2)
        
        # BM25 search
        bm25_results = []
        if self.bm25_index and self.chunk_texts:
            tokenized_query = query.lower().split()
            bm25_scores = self.bm25_index.get_scores(tokenized_query)
            
            # Get top-k BM25 results
            top_indices = np.argsort(bm25_scores)[-top_k*2:][::-1]
            for idx in top_indices:
                if idx < len(self.chunk_ids):
                    bm25_results.append((
                        self.chunk_ids[idx],
                        float(bm25_scores[idx]),
                        {}
                    ))
        
        # Combine results
        combined_scores = {}
        all_ids = set()
        
        # Add vector search results
        for embedding_id, score, metadata in vector_results:
            combined_scores[embedding_id] = self.vector_weight * score
            all_ids.add(embedding_id)
        
        # Add BM25 results
        for embedding_id, score, _ in bm25_results:
            if embedding_id in combined_scores:
                combined_scores[embedding_id] += self.bm25_weight * min(score, 1.0)
            else:
                combined_scores[embedding_id] = self.bm25_weight * min(score, 1.0)
            all_ids.add(embedding_id)
        
        # Sort by combined score
        sorted_ids = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get chunk details
        for embedding_id, score in sorted_ids[:top_k*2]:
            chunk = await self.document_store.get_chunk_by_embedding_id(embedding_id)
            if chunk:
                doc = await self.document_store.get_document_by_id(chunk.document_id)
                if doc:
                    results.append({
                        "chunk_id": chunk.id,
                        "document_id": doc.id,
                        "text": chunk.text,
                        "score": score,
                        "file_path": doc.file_path,
                        "filename": doc.filename,
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index,
                    })
        
        # Rerank if enabled
        if use_reranker and self.reranker and results:
            results = await self.rerank(query, results, top_k)
        else:
            results = results[:top_k]
        
        return results
    
    async def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Rerank results using cross-encoder."""
        if not self.reranker or not results:
            return results[:top_k]
        
        # Prepare pairs for reranking
        pairs = [[query, result["text"]] for result in results]
        
        # Get reranking scores
        rerank_scores = self.reranker.predict(pairs)
        
        # Update scores and sort
        for i, result in enumerate(results):
            result["rerank_score"] = float(rerank_scores[i])
            result["original_score"] = result["score"]
            result["score"] = float(rerank_scores[i])
        
        # Sort by rerank score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]