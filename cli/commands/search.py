"""Search commands."""

import click
import asyncio
import httpx
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def search():
    """Search commands."""
    pass


@search.command()
@click.argument('query')
@click.option('--top-k', '-k', default=5, help='Number of results')
async def query(query, top_k):
    """Search for documents."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/search/",
            params={"q": query, "top_k": top_k}
        )
        if response.status_code == 200:
            data = response.json()
            table = Table(title=f"Search Results for: {query}")
            table.add_column("Score", style="cyan")
            table.add_column("File", style="magenta")
            table.add_column("Text", style="green")
            
            for result in data["results"]:
                table.add_row(
                    f"{result['score']:.3f}",
                    result['filename'],
                    result['text'][:100] + "..."
                )
            console.print(table)
        else:
            console.print(f"[red]Search failed: {response.text}[/red]")