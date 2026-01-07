# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/error_handling.py
# Description: Error handling and recovery strategies for production
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import logging
import time
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"           # Non-critical, can continue
    MEDIUM = "medium"     # Significant, may need attention
    HIGH = "high"         # Critical, requires immediate action
    CRITICAL = "critical" # System failure, shut down


@dataclass
class ErrorContext:
    """Context information about an error."""
    error_type: str
    severity: ErrorSeverity
    message: str
    operation: str
    attempt: int = 1
    max_retries: int = 3
    is_retryable: bool = True
    original_exception: Optional[Exception] = None


class RetryStrategy(ABC):
    """Base class for retry strategies."""

    @abstractmethod
    def should_retry(self, context: ErrorContext) -> bool:
        """Determine if operation should be retried."""
        pass

    @abstractmethod
    def get_backoff_time(self, context: ErrorContext) -> float:
        """Get backoff time before next retry."""
        pass


class ExponentialBackoffStrategy(RetryStrategy):
    """Exponential backoff retry strategy."""

    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        """
        Initialize exponential backoff strategy.

        Args:
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential calculation
        """
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def should_retry(self, context: ErrorContext) -> bool:
        """Check if operation should be retried."""
        if not context.is_retryable:
            return False
        return context.attempt <= context.max_retries

    def get_backoff_time(self, context: ErrorContext) -> float:
        """Calculate backoff time."""
        backoff = self.initial_delay * (self.exponential_base ** (context.attempt - 1))
        return min(backoff, self.max_delay)


class LinearBackoffStrategy(RetryStrategy):
    """Linear backoff retry strategy."""

    def __init__(self, initial_delay: float = 1.0, step: float = 1.0):
        """
        Initialize linear backoff strategy.

        Args:
            initial_delay: Initial delay in seconds
            step: Increment per retry
        """
        self.initial_delay = initial_delay
        self.step = step

    def should_retry(self, context: ErrorContext) -> bool:
        """Check if operation should be retried."""
        if not context.is_retryable:
            return False
        return context.attempt <= context.max_retries

    def get_backoff_time(self, context: ErrorContext) -> float:
        """Calculate backoff time."""
        return self.initial_delay + (self.step * (context.attempt - 1))


class ErrorRecoveryHandler:
    """
    Handles error recovery with configurable retry strategies.

    Business Purpose: Provides production-grade error handling with automatic
    retries, backoff strategies, and error context tracking for debugging.

    Features:
    - Configurable retry strategies (exponential, linear)
    - Error context tracking for debugging
    - Severity-based error classification
    - Graceful degradation
    - Error logging with full context

    Usage Example:
        handler = ErrorRecoveryHandler()
        result = handler.execute_with_retry(
            operation=risky_operation,
            operation_name="fetch_data",
            max_retries=3,
            retryable_exceptions=(requests.Timeout, requests.ConnectionError),
        )
    """

    def __init__(self, retry_strategy: Optional[RetryStrategy] = None):
        """
        Initialize error recovery handler.

        Args:
            retry_strategy: Strategy for retries. Defaults to exponential backoff.
        """
        self.retry_strategy = retry_strategy or ExponentialBackoffStrategy()

    def execute_with_retry(
        self,
        operation: Callable[[], Any],
        operation_name: str,
        max_retries: int = 3,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        initial_delay: float = 1.0,
    ) -> Any:
        """
        Execute operation with automatic retry on failure.

        Args:
            operation: Callable to execute
            operation_name: Name of operation for logging
            max_retries: Maximum number of retries
            retryable_exceptions: Tuple of exception types to retry on
            initial_delay: Initial delay before first retry

        Returns:
            Result of operation

        Raises:
            The last exception if all retries exhausted
        """
        attempt = 1
        last_exception = None

        while attempt <= max_retries + 1:
            try:
                logger.debug(f"Executing operation: {operation_name} (attempt {attempt})")
                return operation()

            except retryable_exceptions as e:
                last_exception = e
                context = ErrorContext(
                    error_type=type(e).__name__,
                    severity=self._classify_severity(e),
                    message=str(e),
                    operation=operation_name,
                    attempt=attempt,
                    max_retries=max_retries,
                    is_retryable=True,
                    original_exception=e,
                )

                if not self.retry_strategy.should_retry(context):
                    logger.error(
                        f"Operation failed after {attempt} attempts: {operation_name}",
                        extra={'context': {
                            'operation': operation_name,
                            'attempts': attempt,
                            'error': str(e),
                        }},
                    )
                    raise

                backoff_time = self.retry_strategy.get_backoff_time(context)
                logger.warning(
                    f"Operation failed (attempt {attempt}), retrying in {backoff_time}s: {operation_name}",
                    extra={'context': {
                        'operation': operation_name,
                        'attempt': attempt,
                        'backoff': backoff_time,
                        'error': str(e),
                    }},
                )

                time.sleep(backoff_time)
                attempt += 1

        # All retries exhausted
        raise last_exception

    def retry_decorator(
        self,
        max_retries: int = 3,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        """
        Decorator for function retry.

        Args:
            max_retries: Maximum number of retries
            retryable_exceptions: Tuple of exception types to retry on

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.execute_with_retry(
                    operation=lambda: func(*args, **kwargs),
                    operation_name=func.__name__,
                    max_retries=max_retries,
                    retryable_exceptions=retryable_exceptions,
                )
            return wrapper
        return decorator

    @staticmethod
    def _classify_severity(exception: Exception) -> ErrorSeverity:
        """Classify error severity based on exception type."""
        error_name = type(exception).__name__

        if 'Critical' in error_name or 'System' in error_name:
            return ErrorSeverity.CRITICAL
        elif 'Timeout' in error_name or 'Connection' in error_name:
            return ErrorSeverity.MEDIUM
        elif 'NotFound' in error_name or 'Invalid' in error_name:
            return ErrorSeverity.LOW
        else:
            return ErrorSeverity.HIGH
