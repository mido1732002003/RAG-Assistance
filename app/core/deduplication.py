"""Document and chunk deduplication."""

import hashlib
from typing import List, Dict, Any, Optional, Tuple, Set

from datasketch import MinHash, MinHashLSH
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.utils.logging import get_logger

logger = get_logger(__name__)


class Deduplicator:
    """Handle document and chunk deduplication."""
    
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self.lsh = MinHashLSH(threshold=threshold, num_perm=128)
        self.seen_hashes = set()
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        self.document_texts = []
    
    def is_duplicate_exact(self, text: str) -> bool:
        """Check for exact duplicate using hash."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        if text_hash in self.seen_hashes:
            return True
        
        self.seen_hashes.add(text_hash)
        return False
    
    def is_duplicate_fuzzy(self, text: str) -> Tuple[bool, float]:
        """Check for near-duplicate using MinHash."""
        # Create MinHash for the text
        minhash = MinHash(num_perm=128)
        for word in text.lower().split():
            minhash.update(word.encode('utf8'))
        
        # Query LSH for similar documents
        result = self.lsh.query(minhash)
        
        if result:
            return True, self.threshold
        
        # Add to LSH
        doc_id = f"doc_{len(self.seen_hashes)}"
        self.lsh.insert(doc_id, minhash)
        
        return False, 0.0
    
    def find_similar_chunks(
        self,
        chunks: List[str],
        similarity_threshold: float = 0.9
    ) -> List[List[int]]:
        """Find similar chunks within a list using TF-IDF."""
        if len(chunks) < 2:
            return []
        
        # Vectorize chunks
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(chunks)
        except:
            # If vectorization fails, return no duplicates
            return []
        
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Find similar pairs
        similar_groups = []
        processed = set()
        
        for i in range(len(chunks)):
            if i in processed:
                continue
            
            group = [i]
            for j in range(i + 1, len(chunks)):
                if similarity_matrix[i, j] >= similarity_threshold:
                    group.append(j)
                    processed.add(j)
            
            if len(group) > 1:
                similar_groups.append(group)
                processed.add(i)
        
        return similar_groups
    
    def deduplicate_chunks(
        self,
        chunks: List[Dict[str, Any]],
        similarity_threshold: float = 0.9
    ) -> List[Dict[str, Any]]:
        """Remove duplicate chunks from a list."""
        if not chunks:
            return []
        
        # Extract texts
        texts = [chunk["text"] for chunk in chunks]
        
        # Find similar chunks
        similar_groups = self.find_similar_chunks(texts, similarity_threshold)
        
        # Mark chunks to keep (keep first in each group)
        to_remove = set()
        for group in similar_groups:
            for idx in group[1:]:  # Skip first, remove rest
                to_remove.add(idx)
        
        # Filter chunks
        deduplicated = [
            chunk for i, chunk in enumerate(chunks)
            if i not in to_remove
        ]
        
        if len(deduplicated) < len(chunks):
            logger.debug(f"Removed {len(chunks) - len(deduplicated)} duplicate chunks")
        
        return deduplicated