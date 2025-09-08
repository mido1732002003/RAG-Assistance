"""Evaluation runner."""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import httpx
from eval.metrics import precision_at_k, recall_at_k, mean_reciprocal_rank, ndcg_at_k


async def run_evaluation(dataset_path: Path, top_k: int = 5) -> Dict[str, float]:
    """Run evaluation on a dataset."""
    with open(dataset_path) as f:
        dataset = json.load(f)
    
    results = {
        "precision_at_k": [],
        "recall_at_k": [],
        "mrr": [],
        "ndcg_at_k": []
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query_item in dataset["queries"]:
            # Search
            response = await client.get(
                "http://localhost:8000/api/search/",
                params={"q": query_item["question"], "top_k": top_k}
            )
            
            if response.status_code == 200:
                data = response.json()
                retrieved = [r["filename"] for r in data["results"]]
                relevant = query_item["relevant_docs"]
                
                # Calculate metrics
                results["precision_at_k"].append(precision_at_k(relevant, retrieved, top_k))
                results["recall_at_k"].append(recall_at_k(relevant, retrieved, top_k))
                results["mrr"].append(mean_reciprocal_rank(relevant, retrieved))
                results["ndcg_at_k"].append(ndcg_at_k(relevant, retrieved, top_k))
    
    # Average metrics
    return {
        metric: sum(values) / len(values) if values else 0.0
        for metric, values in results.items()
    }


if __name__ == "__main__":
    import sys
    dataset_path = Path(sys.argv[1] if len(sys.argv) > 1 else "eval/datasets/sample_qa.json")
    results = asyncio.run(run_evaluation(dataset_path))
    
    print("Evaluation Results:")
    print("-" * 40)
    for metric, value in results.items():
        print(f"{metric}: {value:.3f}")