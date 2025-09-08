"""Ingest commands."""

import click
import asyncio
from pathlib import Path
import httpx
from rich.console import Console

console = Console()


@click.group()
def ingest():
    """Document ingestion commands."""
    pass


@ingest.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--recursive', '-r', is_flag=True, help='Recursively ingest directories')
async def add(path, recursive):
    """Ingest documents from path."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/ingest/directory",
            json={"path": str(path), "recursive": recursive}
        )
        if response.status_code == 200:
            console.print(f"[green]Successfully started ingestion of {path}[/green]")
        else:
            console.print(f"[red]Failed to ingest: {response.text}[/red]")


@ingest.command()
async def watch():
    """Start watching configured directories."""
    console.print("[yellow]Watcher is managed by the main server[/yellow]")
    console.print("Ensure server is running with: uvicorn app.main:app")