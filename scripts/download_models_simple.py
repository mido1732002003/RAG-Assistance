#!/usr/bin/env python3
"""Pre-download required models for offline use - simplified version."""

from sentence_transformers import SentenceTransformer, CrossEncoder

def download_models():
    """Download and cache all required models."""
    print("📥 Downloading models...")
    
    # Download embedding model
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    print(f"  • Downloading embedding model: {model_name}")
    _ = SentenceTransformer(model_name)
    
    # Download reranker model
    reranker_model = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    print(f"  • Downloading reranker model: {reranker_model}")
    _ = CrossEncoder(reranker_model)
    
    print("✅ Models downloaded successfully!")


if __name__ == "__main__":
    download_models()