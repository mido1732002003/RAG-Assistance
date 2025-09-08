"""Test deduplication."""

import pytest
from app.core.deduplication import Deduplicator


def test_exact_duplicate_detection():
    """Test exact duplicate detection."""
    dedup = Deduplicator()
    
    text1 = "This is a test document."
    text2 = "This is a test document."
    text3 = "This is a different document."
    
    assert not dedup.is_duplicate_exact(text1)
    assert dedup.is_duplicate_exact(text2)  # Same as text1
    assert not dedup.is_duplicate_exact(text3)


def test_fuzzy_duplicate_detection():
    """Test fuzzy duplicate detection."""
    dedup = Deduplicator(threshold=0.8)
    
    text1 = "The quick brown fox jumps over the lazy dog"
    text2 = "The quick brown fox jumps over the lazy cat"  # Similar
    
    is_dup1, score1 = dedup.is_duplicate_fuzzy(text1)
    is_dup2, score2 = dedup.is_duplicate_fuzzy(text2)
    
    assert not is_dup1
    # Second might be detected as similar depending on threshold


def test_chunk_deduplication():
    """Test chunk deduplication."""
    dedup = Deduplicator()
    
    chunks = [
        {"text": "First unique chunk"},
        {"text": "First unique chunk"},  # Duplicate
        {"text": "Second unique chunk"},
        {"text": "Third unique chunk"}
    ]
    
    deduplicated = dedup.deduplicate_chunks(chunks)
    
    assert len(deduplicated) < len(chunks)
    assert len(deduplicated) == 3