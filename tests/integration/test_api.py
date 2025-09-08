"""Test API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock


@pytest.fixture
def client():
    """Create test client."""
    with patch('app.dependencies.get_document_store') as mock_doc_store, \
         patch('app.dependencies.get_vector_store') as mock_vector_store, \
         patch('app.dependencies.get_embedding_model') as mock_embedding, \
         patch('app.dependencies.get_retriever') as mock_retriever, \
         patch('app.dependencies.get_generator') as mock_generator:
        
        # Setup mocks
        mock_doc_store.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_embedding.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_generator.return_value = Mock()
        
        from app.main import app
        return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/health/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_search_endpoint(client):
    """Test search endpoint."""
    with patch('app.api.search.get_retriever') as mock_retriever:
        mock_retriever.return_value.search = AsyncMock(return_value=[])
        
        response = client.get("/api/search/", params={"q": "test", "top_k": 5})
        assert response.status_code == 200
        assert "results" in response.json()