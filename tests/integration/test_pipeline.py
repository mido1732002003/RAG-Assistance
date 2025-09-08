"""Test ingestion pipeline."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from app.ingest.pipeline import IngestionPipeline


@pytest.mark.asyncio
async def test_ingest_text_file():
    """Test ingesting a text file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test document content for ingestion.")
        temp_path = Path(f.name)
    
    try:
        mock_doc_store = Mock()
        mock_doc_store.get_document = AsyncMock(return_value=None)
        mock_doc_store.add_document = AsyncMock(return_value=Mock(id=1))
        mock_doc_store.add_chunks = AsyncMock(return_value=[])
        mock_doc_store.compute_checksum = Mock(return_value="abc123")
        
        mock_vector_store = Mock()
        mock_vector_store.add_embeddings = AsyncMock()
        mock_vector_store.save = AsyncMock()
        
        mock_embedding = Mock()
        mock_embedding.embed_batch = AsyncMock(return_value=[[0.1]*384])
        
        pipeline = IngestionPipeline(
            document_store=mock_doc_store,
            vector_store=mock_vector_store,
            embedding_model=mock_embedding
        )
        
        result = await pipeline.ingest_file(temp_path)
        
        assert result["status"] == "success"
        assert mock_doc_store.add_document.called
        assert mock_vector_store.add_embeddings.called
    finally:
        temp_path.unlink()