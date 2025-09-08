"""FAISS vector store for similarity search."""

import pickle
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import faiss

from app.core.embeddings import EmbeddingModel
from app.utils.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Manages FAISS index for vector similarity search."""
    
    def __init__(self, index_dir: Path, embedding_model: EmbeddingModel):
        self.index_dir = index_dir
        self.embedding_model = embedding_model
        self.dimension = embedding_model.dimension
        self.index = None
        self.id_map = {}  # Maps FAISS index to embedding IDs
        self.index_path = index_dir / "faiss.index"
        self.id_map_path = index_dir / "id_map.pkl"
    
    async def initialize(self):
        """Initialize or load the vector store."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        if self.index_path.exists() and self.id_map_path.exists():
            await self.load()
        else:
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
            self.id_map = {}
            logger.info("Created new FAISS index")
    
    async def load(self):
        """Load index from disk."""
        try:
            self.index = faiss.read_index(str(self.index_path))
            with open(self.id_map_path, "rb") as f:
                self.id_map = pickle.load(f)
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            self.index = faiss.IndexFlatIP(self.dimension)
            self.id_map = {}
    
    async def save(self):
        """Save index to disk."""
        try:
            faiss.write_index(self.index, str(self.index_path))
            with open(self.id_map_path, "wb") as f:
                pickle.dump(self.id_map, f)
            logger.info(f"Saved FAISS index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    async def add_embeddings(
        self,
        texts: List[str],
        embedding_ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Add embeddings to the index."""
        if not texts:
            return
        
        # Generate embeddings
        embeddings = await self.embedding_model.embed_batch(texts)
        embeddings = np.array(embeddings).astype("float32")
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add to index
        start_idx = self.index.ntotal
        self.index.add(embeddings)
        
        # Update ID map
        for i, embedding_id in enumerate(embedding_ids):
            self.id_map[start_idx + i] = {
                "id": embedding_id,
                "metadata": metadata[i] if metadata else {}
            }
        
        logger.debug(f"Added {len(texts)} embeddings to index")
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors."""
        if self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = await self.embedding_model.embed(query)
        query_embedding = np.array([query_embedding]).astype("float32")
        
        # Normalize for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Search
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx >= 0 and distance >= threshold:
                item = self.id_map.get(idx)
                if item:
                    results.append((item["id"], float(distance), item.get("metadata", {})))
        
        return results
    
    async def remove_embeddings(self, embedding_ids: List[str]) -> None:
        """Remove embeddings from the index."""
        # Find indices to remove
        indices_to_remove = []
        for idx, item in self.id_map.items():
            if item["id"] in embedding_ids:
                indices_to_remove.append(idx)
        
        if not indices_to_remove:
            return
        
        # Rebuild index without removed items
        new_index = faiss.IndexFlatIP(self.dimension)
        new_id_map = {}
        new_idx = 0
        
        for old_idx in range(self.index.ntotal):
            if old_idx not in indices_to_remove:
                vector = self.index.reconstruct(old_idx)
                new_index.add(np.array([vector]))
                if old_idx in self.id_map:
                    new_id_map[new_idx] = self.id_map[old_idx]
                new_idx += 1
        
        self.index = new_index
        self.id_map = new_id_map
        
        logger.debug(f"Removed {len(indices_to_remove)} embeddings from index")
    
    async def clear(self):
        """Clear the entire index."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.id_map = {}
        logger.info("Cleared FAISS index")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "index_size_bytes": self.index_path.stat().st_size if self.index_path.exists() else 0,
        }