"""Language detection utilities."""

from typing import Optional
import langdetect
from langdetect import detect_langs, LangDetectException

from app.utils.logging import get_logger

logger = get_logger(__name__)

# Configure langdetect for consistency
langdetect.DetectorFactory.seed = 42


class LanguageDetector:
    """Detect language of text content."""
    
    def __init__(self, min_confidence: float = 0.7):
        self.min_confidence = min_confidence
        self.supported_languages = {
            'en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'ru', 'zh', 'ja', 'ko'
        }
    
    def detect(self, text: str) -> Optional[str]:
        """Detect the primary language of text."""
        if not text or len(text.strip()) < 20:
            return None
        
        try:
            # Get language probabilities
            langs = detect_langs(text)
            
            if not langs:
                return None
            
            # Get most probable language
            best_lang = langs[0]
            
            # Check confidence threshold
            if best_lang.prob >= self.min_confidence:
                lang_code = best_lang.lang
                
                # Map language codes to ISO 639-1
                if lang_code.startswith('zh-'):
                    lang_code = 'zh'
                
                if lang_code in self.supported_languages:
                    return lang_code
            
            return 'en'  # Default to English if uncertain
            
        except LangDetectException as e:
            logger.debug(f"Language detection failed: {e}")
            return 'en'
    
    def is_supported(self, lang_code: str) -> bool:
        """Check if a language is supported."""
        return lang_code in self.supported_languages
    
    def get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name."""
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'nl': 'Dutch',
            'ru': 'Russian',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
        }
        return language_names.get(lang_code, 'Unknown')