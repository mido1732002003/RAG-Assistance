"""File system watcher for automatic ingestion."""

import asyncio
from pathlib import Path
from typing import List, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from app.ingest.pipeline import IngestionPipeline
from app.storage.document_store import DocumentStore
from app.storage.vector_store import VectorStore
from app.core.embeddings import EmbeddingModel
from app.utils.logging import get_logger

logger = get_logger(__name__)


class FileChangeHandler(FileSystemEventHandler):
    """Handle file system events."""
    
    def __init__(self, watcher: 'FolderWatcher'):
        self.watcher = watcher
        self.pending_files: Set[Path] = set()
        self.loop = asyncio.get_event_loop()
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            logger.debug(f"File created: {file_path}")
            self.schedule_ingestion(file_path)
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            logger.debug(f"File modified: {file_path}")
            self.schedule_ingestion(file_path)
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            logger.debug(f"File deleted: {file_path}")
            self.schedule_deletion(file_path)
    
    def schedule_ingestion(self, file_path: Path):
        """Schedule file for ingestion."""
        self.pending_files.add(file_path)
        asyncio.run_coroutine_threadsafe(
            self.watcher.ingest_file(file_path),
            self.loop
        )
    
    def schedule_deletion(self, file_path: Path):
        """Schedule file for deletion."""
        asyncio.run_coroutine_threadsafe(
            self.watcher.delete_file(file_path),
            self.loop
        )


class FolderWatcher:
    """Watch folders for changes and trigger ingestion."""
    
    def __init__(
        self,
        watch_dirs: List[Path],
        document_store: DocumentStore,
        vector_store: VectorStore,
        embedding_model: EmbeddingModel,
    ):
        self.watch_dirs = watch_dirs
        self.pipeline = IngestionPipeline(
            document_store=document_store,
            vector_store=vector_store,
            embedding_model=embedding_model,
        )
        self.observer = None
        self.handler = FileChangeHandler(self)
        self.running = False
    
    async def start(self):
        """Start watching folders."""
        if self.running:
            return
        
        logger.info(f"Starting folder watcher for: {self.watch_dirs}")
        
        # Initial scan
        await self.initial_scan()
        
        # Start observer
        self.observer = Observer()
        
        for watch_dir in self.watch_dirs:
            if watch_dir.exists() and watch_dir.is_dir():
                self.observer.schedule(
                    self.handler,
                    str(watch_dir),
                    recursive=True
                )
                logger.info(f"Watching: {watch_dir}")
            else:
                logger.warning(f"Directory not found: {watch_dir}")
        
        self.observer.start()
        self.running = True
    
    async def stop(self):
        """Stop watching folders."""
        if not self.running:
            return
        
        logger.info("Stopping folder watcher")
        
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
        
        self.running = False
    
    async def initial_scan(self):
        """Perform initial scan of watched directories."""
        logger.info("Performing initial scan...")
        
        for watch_dir in self.watch_dirs:
            if watch_dir.exists() and watch_dir.is_dir():
                await self.pipeline.ingest_directory(
                    watch_dir,
                    recursive=True
                )
    
    async def ingest_file(self, file_path: Path):
        """Ingest a single file."""
        try:
            # Add small delay to ensure file is fully written
            await asyncio.sleep(0.5)
            
            # Check if file still exists
            if file_path.exists():
                await self.pipeline.ingest_file(file_path)
        except Exception as e:
            logger.error(f"Failed to ingest {file_path}: {e}")
    
    async def delete_file(self, file_path: Path):
        """Delete a file from the index."""
        try:
            await self.pipeline.delete_document(file_path)
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")