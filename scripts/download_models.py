#!/usr/bin/env python3
"""Pre-download required models for offline use."""

import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sentence_transformers import SentenceTransformer, CrossEncoder
from app.config import settings


def download_models():
    """Download and cache all required models."""
    print("📥 Downloading models...")
    
    # Download embedding model
    print(f"  • Downloading embedding model: {settings.model_name}")
    _ = SentenceTransformer(settings.model_name)
    
    # Download reranker model if not in offline mode
    if not settings.offline_mode and settings.reranker_model:
        print(f"  • Downloading reranker model: {settings.reranker_model}")
        _ = CrossEncoder(settings.reranker_model)
    
    print("✅ Models downloaded successfully!")


if __name__ == "__main__":
    download_models()