#!/usr/bin/env python3
# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/scripts/discover_repos.py
# Description: CLI script to discover git repositories and add them to configuration
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from myragdb.utils.repo_discovery import RepositoryDiscovery


def main():
    """
    Discover git repositories and add them to configuration.

    Business Purpose: Provides command-line interface for repository discovery,
    making it easy to scan directories and update configuration in one step.

    Example:
        # Scan directory and add repos to config
        python scripts/discover_repos.py /Users/user/projects --add

        # Just list discovered repos without adding
        python scripts/discover_repos.py /Users/user/projects

        # Scan with custom depth
        python scripts/discover_repos.py /Users/user/projects --max-depth 4 --add
    """
    parser = argparse.ArgumentParser(
        description="Discover git repositories and optionally add them to configuration"
    )
    parser.add_argument(
        "directory",
        help="Root directory to scan for git repositories"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Maximum directory depth to scan (default: 3)"
    )
    parser.add_argument(
        "--config",
        default="config/repositories.yaml",
        help="Path to repositories configuration file (default: config/repositories.yaml)"
    )
    parser.add_argument(
        "--add",
        action="store_true",
        help="Add discovered repositories to configuration file"
    )
    parser.add_argument(
        "--enabled",
        action="store_true",
        default=True,
        help="Enable discovered repositories (default: True)"
    )
    parser.add_argument(
        "--priority",
        choices=["high", "medium", "low"],
        default="medium",
        help="Priority for discovered repositories (default: medium)"
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=None,
        help="Additional directory names to exclude (e.g., archive old)"
    )

    args = parser.parse_args()

    print(f"🔍 Scanning {args.directory} for git repositories...")
    print(f"   Max depth: {args.max_depth}")
    if args.exclude:
        print(f"   Excluding: {', '.join(args.exclude)}")
    print()

    # Create discovery instance
    discovery = RepositoryDiscovery()

    # Scan for repositories
    repos = discovery.scan_directory(
        args.directory,
        max_depth=args.max_depth,
        exclude_patterns=args.exclude
    )

    # Display results
    if not repos:
        print("❌ No git repositories found")
        return 0

    print(f"✅ Found {len(repos)} git repositories:\n")
    for i, repo in enumerate(repos, 1):
        print(f"{i}. {repo.name}")
        print(f"   Path: {repo.path}")
        print()

    # Add to config if requested
    if args.add:
        print("📝 Adding repositories to configuration...")
        added = discovery.add_repositories_to_config(
            repos,
            args.config,
            enabled=args.enabled,
            priority=args.priority
        )
        print(f"\n✅ Added {added} new repositories to {args.config}")
    else:
        print("ℹ️  Use --add flag to add these repositories to configuration")

    return 0


if __name__ == "__main__":
    sys.exit(main())
