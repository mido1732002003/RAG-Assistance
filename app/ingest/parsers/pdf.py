"""PDF document parser."""

from pathlib import Path
from typing import Dict, Any
import pypdf
from pdfminer.high_level import extract_text as pdfminer_extract

from app.ingest.parsers.base import BaseParser
from app.utils.logging import get_logger

logger = get_logger(__name__)


class PDFParser(BaseParser):
    """Parse PDF documents."""
    
    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse PDF file."""
        if not self.validate_file(file_path):
            raise ValueError(f"Invalid file: {file_path}")
        
        text = ""
        metadata = {}
        
        try:
            # Try pypdf first
            with open(file_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                
                # Extract metadata
                if reader.metadata:
                    metadata = {
                        "title": reader.metadata.get('/Title', ''),
                        "author": reader.metadata.get('/Author', ''),
                        "subject": reader.metadata.get('/Subject', ''),
                        "creator": reader.metadata.get('/Creator', ''),
                    }
                
                # Extract text from all pages
                pages_text = []
                for i, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        pages_text.append(f"[Page {i}]\n{page_text}")
                
                text = "\n\n".join(pages_text)
        
        except Exception as e:
            logger.warning(f"pypdf failed, trying pdfminer: {e}")
            
            # Fallback to pdfminer
            try:
                text = pdfminer_extract(str(file_path))
            except Exception as e2:
                logger.error(f"Both PDF parsers failed: {e2}")
                raise
        
        return {
            "text": text,
            "metadata": metadata,
            "mime_type": "application/pdf",
            "title": metadata.get("title") or file_path.stem,
        }