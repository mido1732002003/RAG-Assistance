"""Test end-to-end chat flow."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock


@pytest.mark.asyncio
async def test_chat_flow():
    """Test complete chat flow."""
    with patch('app.dependencies.get_retriever') as mock_retriever, \
         patch('app.dependencies.get_generator') as mock_generator, \
         patch('app.dependencies.get_document_store') as mock_doc_store:
        
        # Setup mocks
        mock_retriever.return_value.search = AsyncMock(return_value=[
            {
                "chunk_id": 1,
                "document_id": 1,
                "text": "Test context",
                "score": 0.9,
                "file_path": "test.txt",
                "filename": "test.txt",
                "page_number": None,
                "chunk_index": 0
            }
        ])
        
        mock_generator.return_value.generate = AsyncMock(return_value={
            "answer": "Test answer based on context",
            "citations": [{"index": 1, "filename": "test.txt"}],
            "contexts": [],
            "mode": "offline",
            "confidence": 0.9
        })
        
        mock_doc_store.return_value.save_query = AsyncMock()
        
        from app.main import app
        client = TestClient(app)
        
        response = client.post("/api/chat/", json={
            "query": "Test question",
            "top_k": 5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["mode"] == "offline"