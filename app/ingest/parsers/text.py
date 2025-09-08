"""Plain text and markdown parser."""

from pathlib import Path
from typing import Dict, Any
import chardet

from app.ingest.parsers.base import BaseParser
from app.utils.logging import get_logger

logger = get_logger(__name__)


class TextParser(BaseParser):
    """Parse plain text and markdown files."""
    
    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse text file."""
        if not self.validate_file(file_path):
            raise ValueError(f"Invalid file: {file_path}")
        
        # Detect encoding
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
        
        # Read text
        try:
            text = raw_data.decode(encoding)
        except UnicodeDecodeError:
            # Fallback to utf-8 with errors ignored
            text = raw_data.decode('utf-8', errors='ignore')
            logger.warning(f"Encoding issues in {file_path}, some characters may be lost")
        
        # Extract title from markdown
        title = None
        if file_path.suffix.lower() in ['.md', '.markdown']:
            lines = text.split('\n')
            for line in lines[:10]:  # Check first 10 lines
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
        
        return {
            "text": text,
            "metadata": {"encoding": encoding},
            "mime_type": "text/plain" if file_path.suffix == '.txt' else "text/markdown",
            "title": title or file_path.stem,
        }