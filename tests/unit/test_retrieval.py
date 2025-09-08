"""Test retrieval."""

import pytest
from unittest.mock import Mock, AsyncMock
from app.core.retrieval import HybridRetriever


@pytest.mark.asyncio
async def test_hybrid_retriever_initialization():
    """Test retriever initialization."""
    mock_vector_store = Mock()
    mock_document_store = Mock()
    
    retriever = HybridRetriever(
        vector_store=mock_vector_store,
        document_store=mock_document_store
    )
    
    mock_document_store.list_documents = AsyncMock(return_value=[])
    await retriever.initialize()
    
    assert retriever.vector_store == mock_vector_store
    assert retriever.document_store == mock_document_store


@pytest.mark.asyncio
async def test_search_empty_index():
    """Test search with empty index."""
    mock_vector_store = Mock()
    mock_vector_store.search = AsyncMock(return_value=[])
    
    mock_document_store = Mock()
    mock_document_store.list_documents = AsyncMock(return_value=[])
    
    retriever = HybridRetriever(
        vector_store=mock_vector_store,
        document_store=mock_document_store
    )
    
    await retriever.initialize()
    results = await retriever.search("test query", top_k=5)
    
    assert results == []