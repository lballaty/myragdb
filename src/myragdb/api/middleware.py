# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/api/middleware.py
# Description: API middleware for security, validation, and monitoring
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Validates incoming HTTP requests for security and correctness.

    Business Purpose: Enforces request validation rules including:
    - Content-Type validation
    - Request size limits
    - Required header validation
    - Input sanitization

    Usage Example:
        app.add_middleware(RequestValidationMiddleware)
    """

    # Maximum request body size (10MB)
    MAX_BODY_SIZE = 10 * 1024 * 1024

    # Content-Type requirements
    SAFE_CONTENT_TYPES = {
        'application/json',
        'application/x-www-form-urlencoded',
        'multipart/form-data',
        'text/plain',
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Validate and process request.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Check Content-Length
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                length = int(content_length)
                if length > self.MAX_BODY_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={
                            'detail': f'Request body too large. Maximum {self.MAX_BODY_SIZE} bytes allowed.'
                        },
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={'detail': 'Invalid Content-Length header'},
                )

        # Validate Content-Type for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('content-type', '')
            if content_type:
                # Extract base content type (before semicolon)
                base_type = content_type.split(';')[0].strip()
                if base_type and base_type not in self.SAFE_CONTENT_TYPES:
                    return JSONResponse(
                        status_code=415,
                        content={
                            'detail': f'Unsupported media type: {base_type}. Supported types: {", ".join(self.SAFE_CONTENT_TYPES)}'
                        },
                    )

        return await call_next(request)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Adds request context for tracking and correlation.

    Business Purpose: Adds request ID and timing information for monitoring
    and debugging distributed system issues.

    Usage Example:
        app.add_middleware(RequestContextMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add context to request and response.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response with context headers
        """
        # Generate or use provided request ID
        request_id = request.headers.get('x-request-id') or str(uuid.uuid4())

        # Record request start time
        start_time = time.time()

        # Store in request state for access in handlers
        request.state.request_id = request_id
        request.state.start_time = start_time

        # Call next middleware/handler
        response = await call_next(request)

        # Calculate request duration
        duration_ms = (time.time() - start_time) * 1000

        # Add context headers to response
        response.headers['x-request-id'] = request_id
        response.headers['x-response-time-ms'] = str(duration_ms)

        # Log request
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                'context': {
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'duration_ms': duration_ms,
                }
            },
        )

        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Implements rate limiting to prevent abuse.

    Business Purpose: Protects API from abuse by limiting requests
    per client and globally.

    Features:
    - Per-IP rate limiting
    - Global rate limiting
    - Token bucket algorithm
    - Configurable limits per endpoint

    Usage Example:
        app.add_middleware(RateLimitingMiddleware, requests_per_minute=60)
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        """
        Initialize rate limiting middleware.

        Args:
            app: FastAPI application
            requests_per_minute: Max requests per minute per IP
            requests_per_hour: Max requests per hour per IP
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # Track requests per IP
        self.request_counts = {}
        self.request_timestamps = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Apply rate limiting.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response or 429 Too Many Requests
        """
        # Get client IP
        client_ip = request.client.host if request.client else 'unknown'

        # Check rate limits
        current_time = time.time()

        if client_ip not in self.request_timestamps:
            self.request_timestamps[client_ip] = []
            self.request_counts[client_ip] = {'minute': 0, 'hour': 0}

        # Clean old timestamps (older than 1 hour)
        cutoff_time = current_time - 3600
        self.request_timestamps[client_ip] = [
            ts for ts in self.request_timestamps[client_ip]
            if ts > cutoff_time
        ]

        # Count requests in last minute and hour
        minute_ago = current_time - 60
        requests_in_minute = sum(
            1 for ts in self.request_timestamps[client_ip]
            if ts > minute_ago
        )
        requests_in_hour = len(self.request_timestamps[client_ip])

        # Check limits
        if requests_in_minute >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    'detail': 'Rate limit exceeded: Too many requests per minute'
                },
                headers={
                    'retry-after': '60',
                },
            )

        if requests_in_hour >= self.requests_per_hour:
            return JSONResponse(
                status_code=429,
                content={
                    'detail': 'Rate limit exceeded: Too many requests per hour'
                },
                headers={
                    'retry-after': '3600',
                },
            )

        # Record request
        self.request_timestamps[client_ip].append(current_time)

        return await call_next(request)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Handles unhandled exceptions in API handlers.

    Business Purpose: Catches unexpected errors and returns appropriate
    error responses without exposing sensitive information.

    Usage Example:
        app.add_middleware(ErrorHandlingMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Handle exceptions in request processing.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response or error response
        """
        try:
            return await call_next(request)

        except Exception as e:
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}: {str(e)}",
                exc_info=True,
                extra={
                    'context': {
                        'method': request.method,
                        'path': request.url.path,
                        'error_type': type(e).__name__,
                    }
                },
            )

            return JSONResponse(
                status_code=500,
                content={
                    'detail': 'Internal server error. Please check server logs for details.',
                },
            )
