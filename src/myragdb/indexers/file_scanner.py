# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/indexers/file_scanner.py
# Description: File discovery and text extraction for repository indexing
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import os
from pathlib import Path
from typing import List, Iterator, Optional
from dataclasses import dataclass
import fnmatch
import chardet

from myragdb.config import RepositoryConfig


@dataclass
class ScannedFile:
    """
    Represents a discovered file ready for indexing.

    Business Purpose: Encapsulates all information needed to index a file,
    including its path, content, and metadata.

    Example:
        file = ScannedFile(
            file_path="/path/to/file.py",
            repository_name="MyProject",
            content="def hello()...",
            file_type=".py",
            size_bytes=1024
        )
    """
    file_path: str
    repository_name: str
    content: str
    file_type: str
    size_bytes: int
    relative_path: str  # Path relative to repository root


class FileScanner:
    """
    Discovers and processes files in repositories for indexing.

    Business Purpose: Finds all files matching configured patterns and
    extracts their text content, enabling them to be indexed and searched.

    Example:
        scanner = FileScanner(repository_config)
        for file in scanner.scan():
            print(f"Found: {file.file_path}")
    """

    def __init__(self, repository_config: RepositoryConfig):
        """
        Initialize file scanner for a repository.

        Args:
            repository_config: Configuration for the repository to scan
        """
        self.config = repository_config
        self.repo_path = Path(repository_config.path)

    def scan(self) -> Iterator[ScannedFile]:
        """
        Scan repository and yield files matching configured patterns.

        Business Purpose: Main entry point for file discovery. Walks the
        repository directory tree and yields files that match include patterns
        and don't match exclude patterns.

        Yields:
            ScannedFile objects for each matching file

        Example:
            scanner = FileScanner(repo_config)
            file_count = sum(1 for _ in scanner.scan())
            print(f"Found {file_count} files")
        """
        for file_path in self._discover_files():
            try:
                scanned_file = self._process_file(file_path)
                if scanned_file:
                    yield scanned_file
            except Exception as e:
                # Log error but continue scanning
                print(f"Error processing {file_path}: {e}")
                continue

    def _discover_files(self) -> Iterator[Path]:
        """
        Discover files in repository matching patterns.

        Business Purpose: Walks directory tree and applies include/exclude
        filters to find relevant files for indexing.

        Yields:
            Path objects for files matching criteria
        """
        for root, dirs, files in os.walk(self.repo_path):
            root_path = Path(root)

            # Filter directories (modify in-place to affect os.walk)
            dirs[:] = [d for d in dirs if not self._should_exclude_dir(root_path / d)]

            # Process files
            for filename in files:
                file_path = root_path / filename

                if self._should_include_file(file_path):
                    yield file_path

    def _should_include_file(self, file_path: Path) -> bool:
        """
        Check if file matches include patterns and doesn't match exclude patterns.

        Business Purpose: Determines which files should be indexed based on
        configuration, preventing unnecessary indexing of build artifacts.

        Args:
            file_path: Path to check

        Returns:
            True if file should be included, False otherwise
        """
        relative_path = file_path.relative_to(self.repo_path)

        # Check exclude patterns first (more efficient)
        for pattern in self.config.file_patterns.exclude:
            if self._matches_pattern(relative_path, pattern):
                return False

        # Check include patterns
        for pattern in self.config.file_patterns.include:
            if self._matches_pattern(relative_path, pattern):
                return True

        return False

    def _matches_pattern(self, path: Path, pattern: str) -> bool:
        """
        Check if path matches pattern, with proper ** glob support.

        Business Purpose: Provides correct glob pattern matching that handles
        ** wildcards for both root and nested files.

        Args:
            path: Path to check
            pattern: Glob pattern (e.g., "**/*.md", "*.py")

        Returns:
            True if path matches pattern
        """
        # Convert path to string for matching
        path_str = str(path)

        # Handle ** patterns by trying both with and without directory prefix
        if pattern.startswith('**/'):
            # Pattern like **/*.md should match both "file.md" and "dir/file.md"
            suffix_pattern = pattern[3:]  # Remove **/ prefix
            if fnmatch.fnmatch(path_str, suffix_pattern) or fnmatch.fnmatch(path_str, pattern):
                return True
            # Also try matching just the filename
            if fnmatch.fnmatch(path.name, suffix_pattern):
                return True

        # Standard fnmatch for other patterns
        return fnmatch.fnmatch(path_str, pattern)

    def _should_exclude_dir(self, dir_path: Path) -> bool:
        """
        Check if directory should be excluded from traversal.

        Business Purpose: Prevents walking into directories that contain
        only excluded files (e.g., node_modules, .git), improving performance.

        Args:
            dir_path: Directory path to check

        Returns:
            True if directory should be excluded
        """
        relative_path = dir_path.relative_to(self.repo_path)
        relative_str = str(relative_path)

        for pattern in self.config.file_patterns.exclude:
            # Check if pattern matches directory
            if fnmatch.fnmatch(relative_str, pattern.replace('**/', '').replace('/**', '')):
                return True

        return False

    def _process_file(self, file_path: Path) -> Optional[ScannedFile]:
        """
        Read and process a single file.

        Business Purpose: Extracts text content from file with proper encoding
        detection, preparing it for indexing.

        Args:
            file_path: Path to file to process

        Returns:
            ScannedFile object or None if file couldn't be processed

        Example:
            scanned = self._process_file(Path("README.md"))
            if scanned:
                print(f"Read {len(scanned.content)} characters")
        """
        try:
            # Get file info
            size_bytes = file_path.stat().st_size

            # Skip very large files (> 10MB)
            if size_bytes > 10 * 1024 * 1024:
                print(f"Skipping large file: {file_path} ({size_bytes} bytes)")
                return None

            # Read content with encoding detection
            content = self._read_file_content(file_path)
            if content is None:
                return None

            # Get file type
            file_type = file_path.suffix

            # Calculate relative path
            relative_path = str(file_path.relative_to(self.repo_path))

            return ScannedFile(
                file_path=str(file_path.absolute()),
                repository_name=self.config.name,
                content=content,
                file_type=file_type,
                size_bytes=size_bytes,
                relative_path=relative_path
            )

        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return None

    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """
        Read file content with automatic encoding detection.

        Business Purpose: Safely reads text files with various encodings,
        preventing indexing failures due to encoding issues.

        Args:
            file_path: Path to file to read

        Returns:
            File content as string or None if file couldn't be read

        Example:
            content = self._read_file_content(Path("file.py"))
            if content:
                print(f"File has {len(content.splitlines())} lines")
        """
        try:
            # Try UTF-8 first (most common)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                pass

            # Detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()

            detected = chardet.detect(raw_data)
            encoding = detected.get('encoding')

            if not encoding:
                print(f"Could not detect encoding for {file_path}")
                return None

            # Read with detected encoding
            return raw_data.decode(encoding, errors='ignore')

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None


def scan_repository(repository_config: RepositoryConfig) -> List[ScannedFile]:
    """
    Scan a repository and return all matching files.

    Business Purpose: Convenience function to scan entire repository
    and collect all files in one operation.

    Args:
        repository_config: Repository configuration

    Returns:
        List of ScannedFile objects

    Example:
        from myragdb.config import load_repositories_config
        repos = load_repositories_config()
        repo = repos.get_repository_by_name("MyProject")
        files = scan_repository(repo)
        print(f"Scanned {len(files)} files from {repo.name}")
    """
    scanner = FileScanner(repository_config)
    return list(scanner.scan())
