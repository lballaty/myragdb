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
from myragdb.utils.repo_discovery import RepositoryDiscovery
from myragdb.config import load_repositories_config


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
                    repository_filter=repos[0] if repos else None
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
                    repository_filter=repos[0] if repos else None
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
                # Initialize indexers for hybrid search
                import asyncio

                meili = MeilisearchIndexer()
                vector = VectorIndexer()
                engine = HybridSearchEngine(
                    meilisearch_indexer=meili,
                    vector_indexer=vector
                )

                # Run async search
                results = asyncio.run(engine.hybrid_search(
                    query=query,
                    limit=limit,
                    rewrite_query=False  # Disable LLM rewrite for CLI simplicity
                ))

                formatted_results = [
                    {
                        'file_path': r.file_path,
                        'repository': r.repository,
                        'relative_path': r.relative_path,
                        'score': r.rrf_score,
                        'keyword_score': r.keyword_score,
                        'vector_score': 1.0 / (1.0 + r.semantic_distance) if r.semantic_distance else 0.0,
                        'snippet': r.snippet,
                        'file_type': r.file_name.split('.')[-1] if '.' in r.file_name else ''
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
            meili = MeilisearchIndexer()
            vector = VectorIndexer()
            engine = HybridSearchEngine(
                meilisearch_indexer=meili,
                vector_indexer=vector
            )
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


@cli.command()
@click.argument('root_path')
@click.option('--depth', '-d', default=3, help='Maximum directory depth to scan')
@click.option('--add', '-a', is_flag=True, help='Automatically add discovered repos to config')
@click.option('--priority', '-p', default='medium',
              type=click.Choice(['high', 'medium', 'low']),
              help='Priority for added repositories')
@click.option('--config', '-c', default='config/repositories.yaml', help='Path to repositories config')
def discover(root_path: str, depth: int, add: bool, priority: str, config: str):
    """
    Discover git repositories in a directory tree.

    Business Purpose: Automatically finds git repositories for indexing,
    avoiding manual configuration of each repo.

    Examples:
        myragdb discover /Users/user/projects
        myragdb discover /Users/user/projects --depth 2
        myragdb discover /Users/user/projects --add --priority high
    """
    try:
        with console.status(f"[bold green]Scanning {root_path} (depth={depth})..."):
            discovery = RepositoryDiscovery()
            repos = discovery.scan_directory(root_path, max_depth=depth)

        if not repos:
            console.print("[yellow]No git repositories found.[/yellow]")
            return

        # Load existing configuration to check for duplicates
        try:
            existing_config = load_repositories_config()
            existing_paths = {repo.path for repo in existing_config.repositories}
        except Exception:
            existing_paths = set()

        # Create results table
        table = Table(title=f"Discovered Repositories ({len(repos)} found)")
        table.add_column("#", style="dim", width=4)
        table.add_column("Repository", style="cyan")
        table.add_column("Path", style="white")
        table.add_column("Status", style="magenta")

        new_repos = []
        for idx, repo in enumerate(repos, 1):
            status = "[dim]Already indexed[/dim]" if repo.path in existing_paths else "[green]New[/green]"
            table.add_row(str(idx), repo.name, repo.path, status)
            if repo.path not in existing_paths:
                new_repos.append(repo)

        console.print()
        console.print(table)
        console.print()

        # Summary
        summary_text = Text()
        summary_text.append(f"Total: {len(repos)} repositories found\n", style="bold")
        summary_text.append(f"New: {len(new_repos)} repositories\n", style="green")
        summary_text.append(f"Already indexed: {len(repos) - len(new_repos)} repositories", style="dim")
        console.print(Panel(summary_text, title="Summary", border_style="blue"))
        console.print()

        # Add to config if requested
        if add:
            if new_repos:
                with console.status("[bold green]Adding repositories to config..."):
                    added = discovery.add_repositories_to_config(
                        new_repos,
                        config,
                        enabled=True,
                        priority=priority
                    )
                console.print(f"[bold green]✓[/bold green] Added {added} repositories to {config}")
                console.print(f"[dim]Run indexing to include these repositories in search.[/dim]")
            else:
                console.print("[yellow]No new repositories to add.[/yellow]")
        else:
            if new_repos:
                console.print(f"[dim]Tip: Run with --add to automatically add {len(new_repos)} new repositories[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")
        raise click.Abort()


if __name__ == '__main__':
    cli()
