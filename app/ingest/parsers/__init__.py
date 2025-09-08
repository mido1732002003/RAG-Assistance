"""Document parsers for various file types."""

from pathlib import Path
from typing import Optional

from app.ingest.parsers.base import BaseParser
from app.ingest.parsers.pdf import PDFParser
from app.ingest.parsers.text import TextParser
from app.ingest.parsers.docx import DocxParser
from app.ingest.parsers.csv import CSVParser


def get_parser(file_path: Path) -> Optional[BaseParser]:
    """Get appropriate parser for file type."""
    suffix = file_path.suffix.lower()
    
    parsers = {
        '.pdf': PDFParser(),
        '.txt': TextParser(),
        '.md': TextParser(),
        '.markdown': TextParser(),
        '.docx': DocxParser(),
        '.csv': CSVParser(),
    }
    
    return parsers.get(suffix)


__all__ = ['get_parser', 'BaseParser']