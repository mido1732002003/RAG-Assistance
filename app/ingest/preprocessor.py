"""Text preprocessing utilities."""

import re
from typing import Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)


class TextPreprocessor:
    """Preprocess text for indexing."""
    def __init__(self):
    # Patterns for cleaning
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self.email_pattern = re.compile(r'\S+@\S+')
        self.whitespace_pattern = re.compile(r'\s+')
    # إزالة أي رموز خاصة غير الأحرف/الأرقام/المسافات وبعض علامات الترقيم
        self.special_char_pattern = re.compile(r"[^\w\s\-.,!?;:(){}\"'/]")
    
    
    def process(self, text: str) -> str:
        """Apply all preprocessing steps."""
        if not text:
            return ""
        
        # Normalize whitespace
        text = self.normalize_whitespace(text)
        
        # Remove control characters
        text = self.remove_control_characters(text)
        
        # Optionally redact PII
        # text = self.redact_pii(text)
        
        # Fix encoding issues
        text = self.fix_encoding(text)
        
        return text.strip()
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace characters."""
        # Replace various whitespace with single space
        text = self.whitespace_pattern.sub(' ', text)
        
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text
    
    def remove_control_characters(self, text: str) -> str:
        """Remove control characters except newlines and tabs."""
        # Keep only printable characters, newlines, and tabs
        return ''.join(char for char in text if char.isprintable() or char in '\n\t')
    
    def redact_pii(self, text: str) -> str:
        """Redact potential PII (emails, URLs)."""
        # Replace emails
        text = self.email_pattern.sub('[EMAIL]', text)
        
        # Replace URLs
        text = self.url_pattern.sub('[URL]', text)
        
        # Could add more PII detection here (phone numbers, SSN, etc.)
        
        return text
    
    def fix_encoding(self, text: str) -> str:
        """Fix common encoding issues."""
        # Common replacements
        replacements = {
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',
            '—': '-',
            '…': '...',
            '\u00a0': ' ',  # Non-breaking space
            '\u200b': '',   # Zero-width space
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text