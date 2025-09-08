"""Test document parsers."""

import pytest
from pathlib import Path
import tempfile
from app.ingest.parsers.text import TextParser
from app.ingest.parsers.csv import CSVParser


@pytest.mark.asyncio
async def test_text_parser():
    """Test text file parsing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content\nLine 2\nLine 3")
        temp_path = Path(f.name)
    
    try:
        parser = TextParser()
        result = await parser.parse(temp_path)
        
        assert result["text"] == "Test content\nLine 2\nLine 3"
        assert result["mime_type"] == "text/plain"
        assert result["title"] == temp_path.stem
    finally:
        temp_path.unlink()


@pytest.mark.asyncio
async def test_csv_parser():
    """Test CSV file parsing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("col1,col2\nval1,val2\nval3,val4")
        temp_path = Path(f.name)
    
    try:
        parser = CSVParser()
        result = await parser.parse(temp_path)
        
        assert "col1" in result["text"]
        assert "col2" in result["text"]
        assert result["mime_type"] == "text/csv"
    finally:
        temp_path.unlink()