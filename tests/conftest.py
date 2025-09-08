"""Pytest fixtures."""

import pytest
import tempfile
from pathlib import Path
from app.config import Settings


@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_settings(temp_dir):
    """Create test settings."""
    return Settings(
        watch_dirs=str(temp_dir / "data"),
        index_dir=temp_dir / "index",
        sqlite_path=temp_dir / "test.db",
        offline_mode=True,
    )