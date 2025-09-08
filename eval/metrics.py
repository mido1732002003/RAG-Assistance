"""Evaluation metrics."""

from typing import List, Dict, Any
import numpy as np


def precision_at_k(relevant: List[str], retrieved: List[str], k: int) -> float:
    """Calculate precision@k."""
    if not retrieved:
        return 0.0
    
    retrieved_k = retrieved[:k]
    relevant_set = set(relevant)
    
    count = sum(1 for doc in retrieved_k if doc in relevant_set)
    return count / len(retrieved_k)


def recall_at_k(relevant: List[str], retrieved: List[str], k: int) -> float:
    """Calculate recall@k."""
    if not relevant:
        return 0.0
    
    retrieved_k = retrieved[:k]
    relevant_set = set(relevant)
    
    count = sum(1 for doc in retrieved_k if doc in relevant_set)
    return count / len(relevant)


def mean_reciprocal_rank(relevant: List[str], retrieved: List[str]) -> float:
    """Calculate MRR."""
    relevant_set = set(relevant)
    
    for i, doc in enumerate(retrieved, 1):
        if doc in relevant_set:
            return 1.0 / i
    
    return 0.0


def ndcg_at_k(relevant: List[str], retrieved: List[str], k: int) -> float:
    """Calculate NDCG@k."""
    if not retrieved:
        return 0.0
    
    retrieved_k = retrieved[:k]
    relevant_set = set(relevant)
    
    # Calculate DCG
    dcg = 0.0
    for i, doc in enumerate(retrieved_k, 1):
        if doc in relevant_set:
            dcg += 1.0 / np.log2(i + 1)
    
    # Calculate IDCG
    idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(relevant), k)))
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg