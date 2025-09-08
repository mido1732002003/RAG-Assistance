"""Test text chunking."""

import pytest
from app.core.chunker import TextChunker, ChunkConfig


def test_chunk_by_size():
    """Test size-based chunking."""
    chunker = TextChunker(ChunkConfig(
        chunk_size=100,
        chunk_overlap=20,
        respect_sentence_boundary=False
    ))
    
    text = "This is a test. " * 50
    chunks = chunker.chunk_text(text)
    
    assert len(chunks) > 0
    assert all(len(c["text"]) <= 100 for c in chunks)


def test_chunk_by_sentences():
    """Test sentence-based chunking."""
    chunker = TextChunker(ChunkConfig(
        chunk_size=100,
        chunk_overlap=20,
        respect_sentence_boundary=True
    ))
    
    text = "First sentence. Second sentence. Third sentence. Fourth sentence."
    chunks = chunker.chunk_text(text)
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["text"].endswith(('.', '!', '?')) or chunk == chunks[-1]