"""Citation extraction and formatting."""

import re
from typing import List, Dict, Any, Tuple

from app.utils.logging import get_logger

logger = get_logger(__name__)

class CitationExtractor:
    def __init__(self):
        # Pattern to find citation markers like [1], [2], etc.
        self.citation_pattern = re.compile(r'\[(\d+)\]')

    def extract(self, text: str):
        return self.citation_pattern.findall(text)



    
    def extract(self, answer: str, contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract citations from answer text."""
        citations = []
        markers = self.citation_pattern.findall(answer)
        
        for marker in markers:
            idx = int(marker) - 1
            if 0 <= idx < len(contexts):
                context = contexts[idx]
                citation = {
                    "index": int(marker),
                    "chunk_id": context.get("chunk_id"),
                    "document_id": context.get("document_id"),
                    "file_path": context.get("file_path"),
                    "filename": context.get("filename"),
                    "page_number": context.get("page_number"),
                    "text_snippet": self._create_snippet(context.get("text", "")),
                }
                if citation not in citations:
                    citations.append(citation)
        
        if not citations and contexts:
            for i, context in enumerate(contexts[:3], 1):
                citations.append({
                    "index": i,
                    "chunk_id": context.get("chunk_id"),
                    "document_id": context.get("document_id"),
                    "file_path": context.get("file_path"),
                    "filename": context.get("filename"),
                    "page_number": context.get("page_number"),
                    "text_snippet": self._create_snippet(context.get("text", "")),
                    "implicit": True,
                })
        
        return citations
    
    def _create_snippet(self, text: str, max_length: int = 200) -> str:
        """Create a text snippet for citation preview."""
        if len(text) <= max_length:
            return text
        snippet = text[:max_length]
        last_period = snippet.rfind(".")
        if last_period > max_length * 0.7:
            snippet = snippet[:last_period + 1]
        else:
            snippet = snippet.rsplit(" ", 1)[0] + "..."
        return snippet
    
    def format_citations(self, citations: List[Dict[str, Any]]) -> str:
        """Format citations for display."""
        if not citations:
            return ""
        formatted = []
        for citation in citations:
            parts = [f"[{citation['index']}] {citation.get('filename', 'Unknown')}"]
            if citation.get("page_number"):
                parts.append(f"(page {citation['page_number']})")
            formatted.append(" ".join(parts))
        return "\n".join(formatted)