# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/config.py
# Description: Configuration management for MyRAGDB including repository settings and system configuration
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import yaml


class FilePatterns(BaseModel):
    """
    File pattern configuration for repository indexing.

    Business Purpose: Controls which files get indexed and which are ignored,
    preventing unnecessary indexing of build artifacts and dependencies.

    Example:
        patterns = FilePatterns(
            include=["**/*.md", "**/*.py"],
            exclude=["**/node_modules/**"]
        )
    """
    include: List[str] = Field(default_factory=lambda: ["**/*"])
    exclude: List[str] = Field(default_factory=list)


class RepositoryConfig(BaseModel):
    """
    Configuration for a single repository to be indexed.

    Business Purpose: Defines what and how to index from each repository,
    allowing fine-grained control over indexing behavior.

    Example:
        repo = RepositoryConfig(
            name="MyProject",
            path="/path/to/project",
            enabled=True,
            priority="high"
        )
    """
    name: str
    path: str
    enabled: bool = True
    priority: str = "medium"
    excluded: bool = False
    file_patterns: FilePatterns = Field(default_factory=FilePatterns)

    @validator('path')
    def validate_path_exists(cls, v, values):
        """Validate that repository path exists (only for enabled repositories)."""
        # Skip validation for disabled repositories
        if not values.get('enabled', True):
            return v

        path = Path(v).expanduser()
        if not path.exists():
            raise ValueError(f"Repository path does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Repository path is not a directory: {v}")
        return str(path.absolute())


class RepositoriesConfig(BaseModel):
    """
    Collection of all repository configurations.

    Business Purpose: Manages multiple repositories that should be indexed
    together, enabling cross-project search.
    """
    repositories: List[RepositoryConfig]

    def get_enabled_repositories(self) -> List[RepositoryConfig]:
        """Return only enabled repositories."""
        return [repo for repo in self.repositories if repo.enabled]

    def get_repository_by_name(self, name: str) -> Optional[RepositoryConfig]:
        """Get a specific repository by name."""
        for repo in self.repositories:
            if repo.name == name:
                return repo
        return None


class Settings(BaseSettings):
    """
    Application-wide settings loaded from environment variables.

    Business Purpose: Centralizes all configuration in one place,
    allowing easy customization via environment variables.

    Example:
        settings = Settings()
        print(f"Server running on {settings.host}:{settings.port}")
    """
    # Server Configuration
    host: str = Field(default="localhost", alias="MYRAGDB_HOST")
    port: int = Field(default=3003, alias="MYRAGDB_PORT")
    workers: int = Field(default=4, alias="MYRAGDB_WORKERS")

    # Indexing Configuration
    chunk_size: int = Field(default=1000, alias="MYRAGDB_CHUNK_SIZE")
    batch_size: int = Field(default=100, alias="MYRAGDB_BATCH_SIZE")

    # Search Configuration
    default_limit: int = Field(default=10, alias="MYRAGDB_DEFAULT_LIMIT")
    max_limit: int = Field(default=100, alias="MYRAGDB_MAX_LIMIT")

    # Meilisearch Configuration (keyword search engine)
    meilisearch_host: str = Field(default="http://localhost:7700", alias="MEILISEARCH_HOST")
    meilisearch_api_key: str = Field(default="myragdb_dev_key_2026", alias="MEILISEARCH_API_KEY")
    meilisearch_index: str = Field(default="files", alias="MEILISEARCH_INDEX")

    # Embedding Model
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="MYRAGDB_EMBEDDING_MODEL"
    )
    embedding_device: str = Field(default="cpu", alias="MYRAGDB_EMBEDDING_DEVICE")
    embedding_batch_size: int = Field(default=32, alias="MYRAGDB_EMBEDDING_BATCH_SIZE")

    # Data Paths
    data_dir: str = Field(default="./data", alias="MYRAGDB_DATA_DIR")
    index_dir: str = Field(default="./data/indexes", alias="MYRAGDB_INDEX_DIR")
    metadata_db: str = Field(
        default="./data/metadata/myragdb.sqlite",
        alias="MYRAGDB_METADATA_DB"
    )

    # Logging
    log_level: str = Field(default="INFO", alias="MYRAGDB_LOG_LEVEL")
    log_file: str = Field(default="./data/myragdb.log", alias="MYRAGDB_LOG_FILE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def load_repositories_config(config_path: str = "config/repositories.yaml") -> RepositoriesConfig:
    """
    Load repository configuration from YAML file.

    Business Purpose: Reads the list of repositories to index from
    configuration file, allowing users to manage repositories without
    code changes.

    Args:
        config_path: Path to repositories.yaml file

    Returns:
        RepositoriesConfig with all configured repositories

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid

    Example:
        config = load_repositories_config()
        for repo in config.get_enabled_repositories():
            print(f"Will index: {repo.name}")
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(
            f"Repository configuration not found: {config_path}\n"
            f"Please create config/repositories.yaml"
        )

    with open(config_file, 'r') as f:
        data = yaml.safe_load(f)

    return RepositoriesConfig(**data)


def get_settings() -> Settings:
    """
    Get application settings.

    Business Purpose: Provides single access point for all application
    configuration, loading from environment variables and .env file.

    Returns:
        Settings object with all configuration

    Example:
        settings = get_settings()
        print(f"Embedding model: {settings.embedding_model}")
    """
    return Settings()


# Global instances for easy access
settings = get_settings()
