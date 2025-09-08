#!/usr/bin/env python3
"""CLI entry point."""

import click
import asyncio
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()


@click.group()
def cli():
    """Local RAG Assistant CLI."""
    pass


@cli.group()
def ingest():
    """Document ingestion commands."""
    pass


@ingest.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--recursive', '-r', is_flag=True, help='Recursively ingest directories')
def add(path, recursive):
    """Ingest documents from path."""
    from app.ingest.pipeline import IngestionPipeline
    # Implementation would connect to the running service
    console.print(f"[green]Ingesting {path}...[/green]")


@cli.group()
def search():
    """Search commands."""
    pass


@search.command()
@click.argument('query')
@click.option('--top-k', '-k', default=5, help='Number of results')
def query(query, top_k):
    """Search for documents."""
    console.print(f"[blue]Searching for: {query}[/blue]")
    # Implementation would call the API


@cli.group()
def admin():
    """Admin commands."""
    pass


@admin.command()
def backup():
    """Create backup snapshot."""
    console.print("[yellow]Creating backup...[/yellow]")
    # Implementation would call the backup API


@admin.command()
@click.argument('snapshot')
def restore(snapshot):
    """Restore from snapshot."""
    console.print(f"[yellow]Restoring from {snapshot}...[/yellow]")
    # Implementation would call the restore API


if __name__ == "__main__":
    cli()