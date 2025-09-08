"""Path utilities for cross-platform compatibility."""

import os
from pathlib import Path
from typing import List


def normalize_path(path: str | Path) -> Path:
    """Normalize path for cross-platform compatibility."""
    path = Path(path)
    
    # Expand user directory
    if str(path).startswith("~"):
        path = path.expanduser()
    
    # Resolve to absolute path
    path = path.resolve()
    
    return path


def safe_path_join(*parts: str | Path) -> Path:
    """Safely join path components."""
    return Path(*parts).resolve()


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists."""
    path = normalize_path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_safe_path(path: Path, base_path: Path) -> bool:
    """Check if path is within base path (prevent directory traversal)."""
    try:
        path = normalize_path(path)
        base_path = normalize_path(base_path)
        return str(path).startswith(str(base_path))
    except:
        return False


def get_relative_path(path: Path, base_path: Path) -> Path:
    """Get relative path from base path."""
    try:
        return path.relative_to(base_path)
    except ValueError:
        return path