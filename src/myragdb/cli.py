# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/cli.py
# Description: Command-line interface for MyRAGDB search
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import click
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from myragdb.search.hybrid_search import HybridSearchEngine
from myragdb.indexers.meilisearch_indexer import MeilisearchIndexer
from myragdb.indexers.vector_indexer import VectorIndexer


console = Console()


@click.group()
def cli():
    """
    MyRAGDB - Hybrid search for code and documentation.

    Business Purpose: Provides command-line access to search functionality
    for quick queries and agent integration testing.
    """
    pass


@cli.command()
@click.argument('query')
@click.option('--limit', '-l', default=10, help='Maximum number of results')
@click.option('--repos', '-r', multiple=True, help='Filter by repository')
@click.option('--min-score', '-s', default=0.0, type=float, help='Minimum score threshold')
@click.option('--type', '-t', 'search_type',
              type=click.Choice(['hybrid', 'keyword', 'semantic']),
              default='hybrid',
              help='Search type')
def search(query: str, limit: int, repos: tuple, min_score: float, search_type: str):
    """
    Search indexed files.

    Business Purpose: Primary CLI command for executing searches from terminal.
    Useful for quick lookups and testing search quality.

    Args:
        query: Search query string
        limit: Maximum results
        repos: Repository filter
        min_score: Minimum score threshold
        search_type: Type of search (hybrid/keyword/semantic)

    Example:
        myragdb search "JWT authentication" --limit 5
        myragdb search "how to login" --type semantic
        myragdb search "auth" --repos xLLMArionComply --min-score 0.5
    """
    console.print(f"\n[bold cyan]Searching for:[/bold cyan] {query}\n")

    try:
        # Initialize search engines
        with console.status("[bold green]Initializing search engines..."):
            if search_type == 'keyword':
                indexer = MeilisearchIndexer()
                results = indexer.search(
                    query=query,
                    limit=limit,
                    repository=repos[0] if repos else None
                )
                # Convert to common format
                formatted_results = [
                    {
                        'file_path': r.file_path,
                        'repository': r.repository,
                        'relative_path': r.relative_path,
                        'score': r.score,
                        'keyword_score': r.score,
                        'vector_score': None,
                        'snippet': r.snippet,
                        'file_type': r.file_type
                    }
                    for r in results
                ]
            elif search_type == 'semantic':
                indexer = VectorIndexer()
                results = indexer.search(
                    query=query,
                    limit=limit,
                    repository=repos[0] if repos else None
                )
                # Convert to common format
                formatted_results = [
                    {
                        'file_path': r.file_path,
                        'repository': r.repository,
                        'relative_path': r.relative_path,
                        'score': r.score,
                        'keyword_score': None,
                        'vector_score': r.score,
                        'snippet': r.snippet,
                        'file_type': r.file_type
                    }
                    for r in results
                ]
            else:  # hybrid
                engine = HybridSearchEngine()
                results = engine.search(
                    query=query,
                    limit=limit,
                    repository=repos[0] if repos else None,
                    min_score=min_score
                )
                formatted_results = [
                    {
                        'file_path': r.file_path,
                        'repository': r.repository,
                        'relative_path': r.relative_path,
                        'score': r.combined_score,
                        'keyword_score': r.keyword_score,
                        'vector_score': r.vector_score,
                        'snippet': r.snippet,
                        'file_type': r.file_type
                    }
                    for r in results
                ]

        # Display results
        if not formatted_results:
            console.print("[yellow]No results found.[/yellow]\n")
            return

        console.print(f"[bold green]Found {len(formatted_results)} results:[/bold green]\n")

        for i, result in enumerate(formatted_results, 1):
            # Create score display
            score_text = Text()
            score_text.append(f"{result['score']:.3f}", style="bold magenta")

            if result.get('keyword_score') is not None and result.get('vector_score') is not None:
                score_text.append(f" (Keyword: {result['keyword_score']:.3f}, Vec: {result['vector_score']:.3f})", style="dim")

            # Create result panel
            panel_content = f"""[bold]{result['relative_path']}[/bold]
[dim]{result['repository']} • {result['file_type']}[/dim]

{result['snippet']}

[dim]Full path: {result['file_path']}[/dim]"""

            panel = Panel(
                panel_content,
                title=f"[bold]Result {i}[/bold]",
                subtitle=score_text,
                border_style="blue"
            )
            console.print(panel)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")
        raise click.Abort()


@cli.command()
def stats():
    """
    Show index statistics.

    Business Purpose: Provides visibility into index size and health
    for monitoring and debugging.

    Example:
        myragdb stats
    """
    try:
        with console.status("[bold green]Loading statistics..."):
            engine = HybridSearchEngine()
            stats_data = engine.get_stats()

        table = Table(title="Index Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Keyword Documents", str(stats_data['keyword_documents']))
        table.add_row("Vector Chunks", str(stats_data['vector_chunks']))

        console.print()
        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")
        raise click.Abort()


if __name__ == '__main__':
    cli()
