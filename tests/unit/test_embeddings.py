"""Test embeddings."""

import pytest
import numpy as np
from app.core.embeddings import EmbeddingModel


@pytest.mark.asyncio
async def test_embedding_model_initialization():
    """Test embedding model initialization."""
    model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
    await model.initialize()
    
    assert model.model is not None
    assert model.dimension == 384  # Expected dimension for MiniLM


@pytest.mark.asyncio
async def test_single_embedding():
    """Test single text embedding."""
    model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
    await model.initialize()
    
    embedding = await model.embed("Test text")
    
    assert isinstance(embedding, np.ndarray)
    assert len(embedding) == 384
    assert np.linalg.norm(embedding) > 0


@pytest.mark.asyncio  
async def test_batch_embedding():
    """Test batch text embedding."""
    model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
    await model.initialize()
    
    texts = ["First text", "Second text", "Third text"]
    embeddings = await model.embed_batch(texts)
    
    assert len(embeddings) == 3
    assert all(len(e) == 384 for e in embeddings)