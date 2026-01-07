# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/logging_config.py
# Description: Structured logging configuration for production environment
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import logging
import logging.handlers
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
import sys


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info),
            }

        # Add extra context if present
        if hasattr(record, 'context'):
            log_data['context'] = record.context

        return json.dumps(log_data)


class LoggingConfig:
    """
    Centralized logging configuration for MyRAGDB.

    Business Purpose: Provides structured logging across the entire platform
    with support for file rotation, JSON formatting, and environment-specific
    configurations (development, production, testing).

    Features:
    - Structured JSON logging for machine-readable logs
    - File rotation to prevent log files from growing too large
    - Separate handlers for different log levels
    - Context tracking for request/operation correlation
    - Production-safe defaults with configurable verbosity

    Usage Example:
        # Initialize logging
        LoggingConfig.initialize()

        # Get logger in module
        logger = logging.getLogger(__name__)

        # Log with context
        logger.info("Processing request", extra={'context': {
            'request_id': 'abc123',
            'user_id': 'user456'
        }})
    """

    # Default log directory
    DEFAULT_LOG_DIR = Path.home() / '.myragdb' / 'logs'

    # Log levels
    PRODUCTION_LEVEL = logging.INFO
    DEVELOPMENT_LEVEL = logging.DEBUG
    TESTING_LEVEL = logging.WARNING

    @classmethod
    def initialize(
        cls,
        environment: str = 'development',
        log_dir: Optional[Path] = None,
        log_level: Optional[int] = None,
    ) -> None:
        """
        Initialize logging configuration.

        Args:
            environment: Deployment environment ('development', 'production', 'testing')
            log_dir: Directory to store log files. Defaults to ~/.myragdb/logs
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                      If None, uses environment-specific default
        """
        if log_dir is None:
            log_dir = cls.DEFAULT_LOG_DIR

        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Set default log level based on environment
        if log_level is None:
            if environment == 'production':
                log_level = cls.PRODUCTION_LEVEL
            elif environment == 'testing':
                log_level = cls.TESTING_LEVEL
            else:
                log_level = cls.DEVELOPMENT_LEVEL

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Console handler (human-readable format for development)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        if environment == 'production':
            console_formatter = JSONFormatter()
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # File handler (rotating, JSON format for all environments)
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'myragdb.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8',
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

        # Error file handler (errors and above)
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'myragdb_error.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8',
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(error_handler)

    @classmethod
    def get_logger(cls, name: str) -> logging.LoggerAdapter:
        """
        Get a logger instance with context support.

        Args:
            name: Logger name (typically __name__)

        Returns:
            LoggerAdapter for context-aware logging
        """
        logger = logging.getLogger(name)
        return logging.LoggerAdapter(logger, {})

    @classmethod
    def log_with_context(
        cls,
        logger: logging.LoggerAdapter,
        level: int,
        message: str,
        context: Optional[dict] = None,
    ) -> None:
        """
        Log message with context information.

        Args:
            logger: Logger instance
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Message to log
            context: Dictionary with context information
        """
        extra_data = {}
        if context:
            extra_data['context'] = context

        logger.log(level, message, extra=extra_data)
