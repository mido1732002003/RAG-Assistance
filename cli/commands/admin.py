"""Admin commands."""

import click
import asyncio
import httpx
from rich.console import Console

console = Console()


@click.group()
def admin():
    """Admin commands."""
    pass


@admin.command()
async def backup():
    """Create backup snapshot."""
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:8000/api/admin/backup")
        if response.status_code == 200:
            data = response.json()
            console.print(f"[green]Backup created: {data['snapshot']}[/green]")
        else:
            console.print(f"[red]Backup failed: {response.text}[/red]")


@admin.command()
@click.argument('snapshot')
async def restore(snapshot):
    """Restore from snapshot."""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"http://localhost:8000/api/admin/restore/{snapshot}")
        if response.status_code == 200:
            console.print(f"[green]Restored from {snapshot}[/green]")
        else:
            console.print(f"[red]Restore failed: {response.text}[/red]")


@admin.command()
async def rebuild_index():
    """Rebuild search indices."""
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:8000/api/admin/rebuild-index")
        if response.status_code == 200:
            console.print("[green]Index rebuild started[/green]")
        else:
            console.print(f"[red]Rebuild failed: {response.text}[/red]")