"""Text chunking strategies."""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ChunkConfig:
    """Configuration for text chunking."""
    chunk_size: int = 512
    chunk_overlap: int = 50
    min_chunk_size: int = 100
    respect_sentence_boundary: bool = True
    respect_word_boundary: bool = True


class TextChunker:
    """Semantic-aware text chunker with overlap."""
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig()
        
        # Sentence splitting pattern
        self.sentence_pattern = re.compile(r'[.!?]\s+')
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks."""
        if not text or len(text.strip()) < self.config.min_chunk_size:
            return []
        
        # Clean text
        text = self._clean_text(text)
        
        # Split into sentences if configured
        if self.config.respect_sentence_boundary:
            chunks = self._chunk_by_sentences(text)
        else:
            chunks = self._chunk_by_size(text)
        
        # Add metadata to chunks
        result = []
        for i, chunk_data in enumerate(chunks):
            chunk_dict = {
                "text": chunk_data["text"],
                "start_char": chunk_data["start"],
                "end_char": chunk_data["end"],
                "chunk_index": i,
                "metadata": metadata or {}
            }
            
            # Add page number if available
            if metadata and "page_number" in metadata:
                chunk_dict["page_number"] = metadata["page_number"]
            
            result.append(chunk_dict)
        
        return result
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    def _chunk_by_sentences(self, text: str) -> List[Dict[str, Any]]:
        """Chunk text by sentences with overlap."""
        sentences = self.sentence_pattern.split(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        start_pos = 0
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_size = len(sentence)
            
            # Check if adding this sentence exceeds chunk size
            if current_size + sentence_size > self.config.chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "start": start_pos,
                    "end": start_pos + len(chunk_text)
                })
                
                # Handle overlap
                if self.config.chunk_overlap > 0:
                    # Keep last few sentences for overlap
                    overlap_size = 0
                    overlap_sentences = []
                    
                    for sent in reversed(current_chunk):
                        overlap_size += len(sent)
                        overlap_sentences.insert(0, sent)
                        if overlap_size >= self.config.chunk_overlap:
                            break
                    
                    current_chunk = overlap_sentences
                    current_size = sum(len(s) for s in current_chunk)
                    start_pos = start_pos + len(chunk_text) - current_size
                else:
                    current_chunk = []
                    current_size = 0
                    start_pos = start_pos + len(chunk_text) + 1
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "start": start_pos,
                "end": start_pos + len(chunk_text)
            })
        
        return chunks
    
    def _chunk_by_size(self, text: str) -> List[Dict[str, Any]]:
        """Simple size-based chunking with overlap."""
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            # Calculate end position
            end = min(start + self.config.chunk_size, text_len)
            
            # Respect word boundary
            if self.config.respect_word_boundary and end < text_len:
                # Find last space before end
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            # Extract chunk
            chunk_text = text[start:end].strip()
            
            if len(chunk_text) >= self.config.min_chunk_size:
                chunks.append({
                    "text": chunk_text,
                    "start": start,
                    "end": end
                })
            
            # Move start position with overlap
            if end >= text_len:
                break
            
            start = end - self.config.chunk_overlap
            if start <= chunks[-1]["start"] if chunks else 0:
                start = end
        
        return chunks