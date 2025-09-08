"""Simple caching layer for queries and responses."""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

from app.utils.logging import get_logger

logger = get_logger(__name__)


class QueryCache:
    """Simple file-based cache for query results."""
    
    def __init__(self, cache_dir: Path, ttl_seconds: int = 3600):
        self.cache_dir = cache_dir / "query_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def _get_cache_key(self, query: str, mode: str, top_k: int) -> str:
        """Generate cache key from query parameters."""
        key_string = f"{query.lower().strip()}:{mode}:{top_k}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path."""
        return self.cache_dir / f"{cache_key}.json"
    
    async def get(
        self,
        query: str,
        mode: str,
        top_k: int
    ) -> Optional[Dict[str, Any]]:
        """Get cached result if available and not expired."""
        cache_key = self._get_cache_key(query, mode, top_k)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, "r") as f:
                cached = json.load(f)
            
            # Check expiration
            cached_time = datetime.fromisoformat(cached["timestamp"])
            if datetime.utcnow() - cached_time > self.ttl:
                cache_path.unlink()
                return None
            
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return cached["data"]
        except Exception as e:
            logger.error(f"Failed to read cache: {e}")
            return None
    
    async def set(
        self,
        query: str,
        mode: str,
        top_k: int,
        data: Dict[str, Any]
    ) -> None:
        """Cache query result."""
        cache_key = self._get_cache_key(query, mode, top_k)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            cached = {
                "timestamp": datetime.utcnow().isoformat(),
                "query": query,
                "mode": mode,
                "top_k": top_k,
                "data": data
            }
            
            with open(cache_path, "w") as f:
                json.dump(cached, f)
            
            logger.debug(f"Cached result for query: {query[:50]}...")
        except Exception as e:
            logger.error(f"Failed to write cache: {e}")
    
    async def clear(self) -> None:
        """Clear all cached results."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        logger.info("Cleared query cache")