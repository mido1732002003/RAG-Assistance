"""Cross-encoder reranking for improved relevance."""

from typing import List, Tuple
import torch
from sentence_transformers import CrossEncoder

from app.utils.logging import get_logger

logger = get_logger(__name__)


class Reranker:
    """Cross-encoder based reranker."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    def initialize(self):
        """Load the reranking model."""
        logger.info(f"Loading reranker: {self.model_name}")
        self.model = CrossEncoder(self.model_name, device=self.device)
    
    def rerank(
        self,
        query: str,
        passages: List[str],
        top_k: Optional[int] = None
    ) -> List[Tuple[int, float]]:
        """Rerank passages based on relevance to query."""
        if not self.model:
            self.initialize()
        
        if not passages:
            return []
        
        # Create query-passage pairs
        pairs = [[query, passage] for passage in passages]
        
        # Get scores
        scores = self.model.predict(pairs, show_progress_bar=False)
        
        # Sort by score
        scored_indices = [(i, float(score)) for i, score in enumerate(scores)]
        scored_indices.sort(key=lambda x: x[1], reverse=True)
        
        if top_k:
            scored_indices = scored_indices[:top_k]
        
        return scored_indices