from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import uuid
from typing import Callable, Optional
from services.logging_service import LoggingService
from database.session import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from datetime import datetime, timezone

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        logger: LoggingService,
        exclude_paths: Optional[list[str]] = None
    ):
        super().__init__(app)
        self.logger = logger
        self.exclude_paths = exclude_paths or []

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        self.logger.log_request(request_id)

        # Skip middleware for excluded paths
        if request.url.path in self.exclude_paths:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        start_time = time.time()
        try:
            # Process the request
            response = await call_next(request)
            # Log request details
            duration = (time.time() - start_time) * 1000
            self.logger.log_api_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration,
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            # Log the error
            duration = (time.time() - start_time) * 1000
            self.logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=e,
                request_method=request.method,
                request_path=request.url.path,
                duration_ms=duration,
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
            # Return error response
            error_response = JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal Server Error",
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            error_response.headers["X-Request-ID"] = request_id
            return error_response
        finally:
            self.logger.clear_request_context()

class DatabaseErrorHandler(BaseHTTPMiddleware):
    """Middleware for handling database errors."""
    def __init__(self, app: ASGIApp, logger: LoggingService):
        super().__init__(app)
        self.logger = logger

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        db = None
        try:
            # Try to get db from request state if available
            if hasattr(request, 'state') and hasattr(request.state, 'db'):
                db = request.state.db
            response = await call_next(request)
            return response
        except Exception as e:
            self.logger.error(
                "Database error occurred",
                exc_info=e,
                request_method=request.method,
                request_path=request.url.path
            )
            if db:
                db.rollback()
            request_id = str(uuid.uuid4())
            error_response = JSONResponse(
                status_code=500,
                content={
                    "detail": f"Database error: {str(e)}",
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            error_response.headers["X-Request-ID"] = request_id
            return error_response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""
    def __init__(
        self,
        app: ASGIApp,
        logger: LoggingService,
        rate_limit: int = 100,  # requests per minute
        exclude_paths: Optional[list[str]] = None
    ):
        super().__init__(app)
        self.logger = logger
        self.rate_limit = rate_limit
        self.exclude_paths = exclude_paths or []
        self.requests = {}  # Store request counts

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        # Check rate limit
        current_time = time.time()
        if client_ip in self.requests:
            # Clean up old requests
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < 60
            ]
            # Check if rate limit exceeded
            if len(self.requests[client_ip]) >= self.rate_limit:
                self.logger.warning(
                    "Rate limit exceeded",
                    client_ip=client_ip,
                    request_method=request.method,
                    request_path=request.url.path
                )
                request_id = str(uuid.uuid4())
                error_response = JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded. Please try again later.",
                        "request_id": request_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
                error_response.headers["X-Request-ID"] = request_id
                return error_response
        # Add current request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)
        # Process the request
        return await call_next(request) 