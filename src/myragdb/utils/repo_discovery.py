# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/utils/repo_discovery.py
# Description: Repository discovery utility to scan directories for git repositories
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import os
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
import yaml


@dataclass
class DiscoveredRepository:
    """
    Represents a discovered git repository.

    Business Purpose: Contains information about a git repository found during
    directory scanning, ready to be added to the repositories configuration.

    Example:
        repo = DiscoveredRepository(
            name="MyProject",
            path="/Users/user/projects/MyProject",
            git_dir="/Users/user/projects/MyProject/.git"
        )
    """
    name: str
    path: str
    git_dir: str
    is_git_repo: bool = True


class RepositoryDiscovery:
    """
    Scans directories for git repositories and manages repository configuration.

    Business Purpose: Automates the process of finding git repositories on the
    filesystem and adding them to the indexing configuration, saving manual
    configuration effort.

    Example:
        discovery = RepositoryDiscovery()
        repos = discovery.scan_directory("/Users/user/projects", max_depth=2)
        for repo in repos:
            print(f"Found: {repo.name} at {repo.path}")
    """

    def __init__(self):
        """Initialize repository discovery utility."""
        pass

    def is_git_repository(self, directory: Path) -> bool:
        """
        Check if directory is a git repository.

        Business Purpose: Identifies valid git repositories by checking for
        .git directory, avoiding false positives.

        Args:
            directory: Path to check

        Returns:
            True if directory contains .git folder

        Example:
            discovery = RepositoryDiscovery()
            if discovery.is_git_repository(Path("/path/to/repo")):
                print("This is a git repository")
        """
        git_dir = directory / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def scan_directory(
        self,
        root_path: str,
        max_depth: int = 3,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[DiscoveredRepository]:
        """
        Scan directory recursively for git repositories.

        Business Purpose: Automatically discovers all git repositories within
        a directory tree, making it easy to index multiple projects at once.

        Args:
            root_path: Root directory to start scanning from
            max_depth: Maximum directory depth to scan (default: 3)
            exclude_patterns: Directory names to skip (e.g., ["node_modules", "venv"])

        Returns:
            List of discovered git repositories

        Example:
            discovery = RepositoryDiscovery()
            repos = discovery.scan_directory(
                "/Users/user/projects",
                max_depth=2,
                exclude_patterns=["archive", "old"]
            )
            print(f"Found {len(repos)} repositories")
        """
        if exclude_patterns is None:
            exclude_patterns = [
                "node_modules",
                "venv",
                ".venv",
                "env",
                ".env",
                "__pycache__",
                ".git",
                "dist",
                "build",
                "target",
                ".dart_tool",
                "Pods",
                ".gradle",
                "archive",
                "backup"
            ]

        discovered = []
        root = Path(root_path).resolve()

        if not root.exists() or not root.is_dir():
            print(f"Error: {root_path} is not a valid directory")
            return discovered

        # Use os.walk with depth tracking
        for dirpath, dirnames, _ in os.walk(root):
            current_path = Path(dirpath)

            # Calculate depth relative to root
            try:
                depth = len(current_path.relative_to(root).parts)
            except ValueError:
                continue

            # Stop if we've reached max depth
            if depth >= max_depth:
                dirnames.clear()  # Don't recurse deeper
                continue

            # Check if current directory is a git repo
            if self.is_git_repository(current_path):
                repo_name = current_path.name
                discovered.append(DiscoveredRepository(
                    name=repo_name,
                    path=str(current_path),
                    git_dir=str(current_path / ".git"),
                    is_git_repo=True
                ))
                # Don't recurse into git repositories
                dirnames.clear()
                continue

            # Filter out excluded directories
            dirnames[:] = [
                d for d in dirnames
                if d not in exclude_patterns and not d.startswith('.')
            ]

        return discovered

    def get_default_file_patterns(self) -> Dict:
        """
        Get default file patterns for repository configuration.

        Business Purpose: Provides sensible defaults for file inclusion/exclusion
        patterns, ensuring consistent indexing across repositories.

        Returns:
            Dictionary with 'include' and 'exclude' pattern lists

        Example:
            patterns = discovery.get_default_file_patterns()
            print(f"Including: {patterns['include']}")
        """
        return {
            "include": [
                # Documentation
                "**/*.md",
                "**/*.txt",
                # Code files
                "**/*.py",
                "**/*.js",
                "**/*.jsx",
                "**/*.ts",
                "**/*.tsx",
                "**/*.dart",
                # Configuration/Data files
                "**/*.json",
                "**/*.yaml",
                "**/*.yml",
                "**/*.toml",
                # Scripts
                "**/*.sh",
                "**/*.sql"
            ],
            "exclude": [
                # Dependencies and libraries
                "**/node_modules/**",
                "**/vendor/**",
                "**/ios/Pods/**",
                # Version control
                "**/.git/**",
                # Python artifacts
                "**/venv/**",
                "**/__pycache__/**",
                "**/.pytest_cache/**",
                "**/.mypy_cache/**",
                # Build outputs
                "**/dist/**",
                "**/build/**",
                "**/target/**",
                "**/.next/**",
                "**/.nuxt/**",
                # Dart/Flutter artifacts
                "**/.dart_tool/**",
                # Android/Gradle artifacts
                "**/android/.gradle/**",
                "**/.gradle/**",
                # Archives and backups
                "**/archive-*/**",
                # Lock files and coverage
                "**/*.lock",
                "**/coverage/**"
            ]
        }

    def add_repositories_to_config(
        self,
        discovered_repos: List[DiscoveredRepository],
        config_path: str,
        enabled: bool = True,
        priority: str = "medium"
    ) -> int:
        """
        Add discovered repositories to the YAML configuration file.

        Business Purpose: Automates updating the repositories.yaml configuration
        with newly discovered repositories, avoiding manual YAML editing.

        Args:
            discovered_repos: List of discovered repositories to add
            config_path: Path to repositories.yaml file
            enabled: Whether to enable repositories by default
            priority: Priority level (high, medium, low)

        Returns:
            Number of repositories added

        Example:
            repos = discovery.scan_directory("/Users/user/projects")
            count = discovery.add_repositories_to_config(
                repos,
                "config/repositories.yaml",
                enabled=True,
                priority="high"
            )
            print(f"Added {count} repositories to config")
        """
        config_file = Path(config_path)

        # Load existing config
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}

        # Ensure repositories key exists
        if 'repositories' not in config:
            config['repositories'] = []

        # Get existing repository paths to avoid duplicates
        existing_paths = {
            repo['path'] for repo in config['repositories']
            if isinstance(repo, dict) and 'path' in repo
        }

        # Get default file patterns
        default_patterns = self.get_default_file_patterns()

        # Add new repositories
        added = 0
        for repo in discovered_repos:
            if repo.path not in existing_paths:
                config['repositories'].append({
                    'name': repo.name,
                    'path': repo.path,
                    'enabled': enabled,
                    'priority': priority,
                    'file_patterns': default_patterns
                })
                added += 1
                print(f"Added repository: {repo.name} ({repo.path})")
            else:
                print(f"Skipped (already exists): {repo.name} ({repo.path})")

        # Write updated config
        if added > 0:
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            print(f"\nAdded {added} new repositories to {config_path}")
        else:
            print("\nNo new repositories to add")

        return added

    def generate_config_yaml(
        self,
        discovered_repos: List[DiscoveredRepository],
        output_path: str,
        enabled: bool = True,
        priority: str = "medium"
    ) -> None:
        """
        Generate a new repositories.yaml configuration from discovered repositories.

        Business Purpose: Creates a complete repositories configuration file from
        scratch based on discovered repositories, useful for initial setup.

        Args:
            discovered_repos: List of discovered repositories
            output_path: Path to write the YAML configuration
            enabled: Whether to enable repositories by default
            priority: Priority level (high, medium, low)

        Example:
            repos = discovery.scan_directory("/Users/user/projects")
            discovery.generate_config_yaml(
                repos,
                "config/repositories.yaml",
                enabled=True,
                priority="high"
            )
        """
        default_patterns = self.get_default_file_patterns()

        config = {
            'repositories': [
                {
                    'name': repo.name,
                    'path': repo.path,
                    'enabled': enabled,
                    'priority': priority,
                    'file_patterns': default_patterns
                }
                for repo in discovered_repos
            ]
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            # Write header comment
            f.write("# File: " + str(output_file) + "\n")
            f.write("# Description: Repository configuration for indexing\n")
            f.write("# Author: Libor Ballaty <libor@arionetworks.com>\n")
            f.write(f"# Created: {Path(__file__).stat().st_mtime}\n\n")

            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print(f"Generated configuration with {len(discovered_repos)} repositories: {output_path}")
