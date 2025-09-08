"""Chat commands."""

import click
import asyncio
import httpx
from rich.console import Console
from rich.prompt import Prompt

console = Console()


@click.group()
def chat():
    """Chat commands."""
    pass


@chat.command()
@click.option('--mode', default='auto', type=click.Choice(['auto', 'offline', 'llm']))
async def start(mode):
    """Start interactive chat session."""
    console.print("[bold blue]RAG Chat Session[/bold blue]")
    console.print("Type 'exit' to quit\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            query = Prompt.ask("[yellow]You[/yellow]")
            if query.lower() in ['exit', 'quit']:
                break
            
            response = await client.post(
                "http://localhost:8000/api/chat/",
                json={"query": query, "mode": mode if mode != 'auto' else None}
            )
            
            if response.status_code == 200:
                data = response.json()
                console.print(f"\n[green]Assistant ({data['mode']}):[/green]")
                console.print(data['answer'])
                
                if data['citations']:
                    console.print("\n[cyan]Sources:[/cyan]")
                    for citation in data['citations']:
                        console.print(f"  [{citation['index']}] {citation['filename']}")
            else:
                console.print(f"[red]Error: {response.text}[/red]")