"""Embedding model management."""

from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

from app.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingModel:
    """Manages sentence embedding model."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.dimension = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    async def initialize(self):
        """Load the embedding model."""
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        
        # Get embedding dimension
        test_embedding = self.model.encode("test", convert_to_numpy=True)
        self.dimension = len(test_embedding)
        
        logger.info(f"Embedding model loaded (dimension: {self.dimension}, device: {self.device})")
    
    async def embed(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        if not self.model:
            await self.initialize()
        
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embedding
    
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[np.ndarray]:
        """Generate embeddings for multiple texts."""
        if not self.model:
            await self.initialize()
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 100
        )
        return embeddings.tolist()