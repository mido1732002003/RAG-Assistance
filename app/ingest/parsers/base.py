"""Base parser interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any


class BaseParser(ABC):
    """Abstract base class for document parsers."""
    
    @abstractmethod
    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse document and return extracted content.
        
        Returns:
            Dictionary with keys:
            - text: extracted text content
            - metadata: additional metadata
            - mime_type: MIME type of the document
            - title: document title if available
        """
        pass
    
    def validate_file(self, file_path: Path) -> bool:
        """Validate that file exists and is readable."""
        return file_path.exists() and file_path.is_file()