#!/usr/bin/env python3
"""Database migration script."""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.storage.models import Base, get_engine
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def create_tables():
    """Create all database tables."""
    engine = get_engine(settings.sqlite_path)
    
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Create indexes for better performance
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_documents_path ON documents(file_path);
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_documents_checksum ON documents(checksum);
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_queries_timestamp ON queries(timestamp);
        """))
        
    await engine.dispose()
    logger.info("Database tables created successfully")


async def main():
    """Run migrations."""
    print("🔧 Running database migrations...")
    await create_tables()
    print("✅ Database migrations complete!")


if __name__ == "__main__":
    asyncio.run(main())