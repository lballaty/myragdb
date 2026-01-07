# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/indexers/file_scanner.py
# Description: File discovery and text extraction for repository indexing
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import os
from pathlib import Path
from typing import List, Iterator, Optional
from dataclasses import dataclass, field
import fnmatch
import chardet

from myragdb.config import RepositoryConfig


@dataclass
class ScannedFile:
    """
    Represents a discovered file ready for indexing.

    Business Purpose: Encapsulates all information needed to index a file,
    including its path, content, and metadata. Supports both repository
    and non-repository directory sources.

    Example:
        # From repository
        file = ScannedFile(
            file_path="/path/to/file.py",
            repository_name="MyProject",
            content="def hello()...",
            file_type=".py",
            size_bytes=1024,
            relative_path="src/main.py"
        )

        # From directory
        file = ScannedFile(
            file_path="/path/to/documents/file.md",
            repository_name=None,
            content="# Document...",
            file_type=".md",
            size_bytes=2048,
            relative_path="file.md",
            directory_id=1
        )
    """
    file_path: str
    content: str
    file_type: str
    size_bytes: int
    relative_path: str  # Path relative to repository/directory root
    repository_name: Optional[str] = None  # Repository name (None if from directory)
    directory_id: Optional[int] = None  # Directory ID (None if from repository)


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


class DirectoryScanner:
    """
    Discovers and processes files in non-repository directories for indexing.

    Business Purpose: Finds all files in a managed directory (not a git repository)
    and extracts their text content, enabling them to be indexed and searched
    alongside repository files.

    Example:
        scanner = DirectoryScanner(directory_path="/path/to/documents", directory_id=1)
        for file in scanner.scan():
            print(f"Found: {file.file_path}")
    """

    def __init__(
        self,
        directory_path: str,
        directory_id: int,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ):
        """
        Initialize directory scanner for a non-repository directory.

        Business Purpose: Prepares scanner for discovering files in arbitrary
        directories with configurable include/exclude patterns.

        Args:
            directory_path: Absolute path to directory to scan
            directory_id: Database ID of the managed directory
            include_patterns: File patterns to include (e.g., ["**/*.md", "**/*.py"])
                            If None, includes all text files
            exclude_patterns: File patterns to exclude (e.g., ["**/.*", "**/__pycache__/**"])
                            If None, uses default exclusions
        """
        self.directory_path = Path(directory_path)
        self.directory_id = directory_id

        # Default patterns: include common text files, exclude binary and system files
        self.include_patterns = include_patterns or [
            "**/*.md",
            "**/*.txt",
            "**/*.py",
            "**/*.js",
            "**/*.ts",
            "**/*.tsx",
            "**/*.jsx",
            "**/*.json",
            "**/*.yaml",
            "**/*.yml",
            "**/*.xml",
            "**/*.html",
            "**/*.css",
            "**/*.sql",
            "**/*.sh",
            "**/*.bash",
            "**/*.rb",
            "**/*.go",
            "**/*.rs",
            "**/*.java",
            "**/*.cpp",
            "**/*.c",
            "**/*.h",
            "**/*.dart"
        ]

        self.exclude_patterns = exclude_patterns or [
            "**/.*",                      # Hidden files
            "**/__pycache__/**",          # Python cache
            "**/node_modules/**",         # Node modules
            "**/.git/**",                 # Git directory
            "**/venv/**",                 # Virtual environments
            "**/*.pyc",                   # Python bytecode
            "**/*.o",                     # Object files
            "**/*.a",                     # Archive files
            "**/dist/**",                 # Distribution directories
            "**/build/**"                 # Build directories
        ]

    def scan(self) -> Iterator[ScannedFile]:
        """
        Scan directory and yield files matching configured patterns.

        Business Purpose: Main entry point for file discovery in directory.
        Walks the directory tree and yields files that match include patterns
        and don't match exclude patterns.

        Yields:
            ScannedFile objects with directory_id set (repository_name=None)

        Example:
            scanner = DirectoryScanner("/path/to/docs", 1)
            file_count = sum(1 for _ in scanner.scan())
            print(f"Found {file_count} files")
        """
        if not self.directory_path.exists():
            print(f"Directory does not exist: {self.directory_path}")
            return

        if not self.directory_path.is_dir():
            print(f"Path is not a directory: {self.directory_path}")
            return

        for file_path in self._discover_files():
            try:
                scanned_file = self._process_file(file_path)
                if scanned_file:
                    yield scanned_file
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue

    def _discover_files(self) -> Iterator[Path]:
        """
        Discover files in directory matching patterns.

        Business Purpose: Walks directory tree and applies include/exclude
        filters to find relevant files for indexing.

        Yields:
            Path objects for files matching criteria
        """
        for root, dirs, files in os.walk(self.directory_path):
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
        relative_path = file_path.relative_to(self.directory_path)

        # Check exclude patterns first (more efficient)
        for pattern in self.exclude_patterns:
            if self._matches_pattern(relative_path, pattern):
                return False

        # Check include patterns
        for pattern in self.include_patterns:
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
        path_str = str(path)

        # Handle ** patterns
        if pattern.startswith('**/'):
            suffix_pattern = pattern[3:]
            if fnmatch.fnmatch(path_str, suffix_pattern) or fnmatch.fnmatch(path_str, pattern):
                return True
            if fnmatch.fnmatch(path.name, suffix_pattern):
                return True

        return fnmatch.fnmatch(path_str, pattern)

    def _should_exclude_dir(self, dir_path: Path) -> bool:
        """
        Check if directory should be excluded from traversal.

        Business Purpose: Prevents walking into directories that contain
        only excluded files, improving performance.

        Args:
            dir_path: Directory path to check

        Returns:
            True if directory should be excluded
        """
        relative_path = dir_path.relative_to(self.directory_path)
        relative_str = str(relative_path)

        for pattern in self.exclude_patterns:
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

            # Calculate relative path from directory root
            relative_path = str(file_path.relative_to(self.directory_path))

            return ScannedFile(
                file_path=str(file_path.absolute()),
                content=content,
                file_type=file_type,
                size_bytes=size_bytes,
                relative_path=relative_path,
                repository_name=None,              # Not from a repository
                directory_id=self.directory_id     # From this managed directory
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

            return raw_data.decode(encoding, errors='ignore')

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None


def scan_directory(directory_path: str, directory_id: int) -> List[ScannedFile]:
    """
    Scan a non-repository directory and return all matching files.

    Business Purpose: Convenience function to scan entire directory
    and collect all files in one operation.

    Args:
        directory_path: Absolute path to directory
        directory_id: Database ID of the managed directory

    Returns:
        List of ScannedFile objects with directory_id set

    Example:
        files = scan_directory("/path/to/documents", directory_id=1)
        print(f"Scanned {len(files)} files from directory")
    """
    scanner = DirectoryScanner(directory_path, directory_id)
    return list(scanner.scan())
