"""Configuration management for the RAG assistant."""

import os
from pathlib import Path
from typing import List, Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, ConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        protected_namespaces=('settings_',)  # Fix the model_ conflict warning
    )
    
    # Folder Configuration
    watch_dirs: str = Field(default="./data", description="Comma-separated directories to watch")
    index_dir: Path = Field(default=Path("./var/index"), description="FAISS index directory")
    sqlite_path: Path = Field(default=Path("./var/rag.db"), description="SQLite database path")
    
    # Model Configuration
    model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model name"
    )
    reranker_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Reranker model name"
    )
    offline_mode: bool = Field(default=True, description="Run in offline mode")
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    mistral_api_key: Optional[str] = Field(default=None, description="Mistral API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    
    # Search Configuration
    default_top_k: int = Field(default=5, ge=1, le=50, description="Default number of results")
    max_context_tokens: int = Field(default=2000, ge=100, description="Maximum context tokens")
    chunk_size: int = Field(default=512, ge=100, description="Text chunk size")
    chunk_overlap: int = Field(default=50, ge=0, description="Chunk overlap size")
    
    # Server Configuration
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Path = Field(default=Path("./var/logs/rag.log"), description="Log file path")
    
    # Performance
    batch_size: int = Field(default=32, ge=1, description="Batch size for processing")
    max_workers: int = Field(default=4, ge=1, description="Maximum worker threads")
    cache_ttl: int = Field(default=3600, ge=0, description="Cache TTL in seconds")
    
    @field_validator("index_dir", "sqlite_path", "log_file", mode='before')
    @classmethod
    def ensure_path(cls, v):
        """Ensure paths are Path objects and create parent directories."""
        if v:
            path = Path(v)
            path.parent.mkdir(parents=True, exist_ok=True)
            return path
        return v
    
    @property
    def parsed_watch_dirs(self) -> List[Path]:
        """Get parsed watch directories as Path objects."""
        if isinstance(self.watch_dirs, str):
            return [Path(d.strip()) for d in self.watch_dirs.split(",") if d.strip()]
        return [Path(self.watch_dirs)]
    
    @property
    def has_llm_key(self) -> bool:
        """Check if any LLM API key is configured."""
        return bool(self.openai_api_key or self.mistral_api_key or self.anthropic_api_key)
    
    @property
    def active_llm_provider(self) -> Optional[str]:
        """Get the active LLM provider based on available keys."""
        if self.openai_api_key:
            return "openai"
        elif self.mistral_api_key:
            return "mistral"
        elif self.anthropic_api_key:
            return "anthropic"
        return None
    
    def validate_paths(self) -> None:
        """Validate that all required paths exist or can be created."""
        for dir_path in [self.index_dir, self.sqlite_path.parent, self.log_file.parent]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        for watch_dir in self.parsed_watch_dirs:
            watch_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Validate paths on import
settings.validate_paths()