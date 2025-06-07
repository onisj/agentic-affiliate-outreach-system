"""
Middleware Package

This package contains all API middleware components.

Modules:
    auth: Authentication middleware
    metrics: Metrics and monitoring middleware
    logging: Logging middleware
    error_handling: Error handling middleware
"""

from fastapi import FastAPI
from .metrics import MetricsMiddleware
from .logging import LoggingMiddleware
from .error_handling import ErrorHandlingMiddleware
from .auth import AuthMiddleware

def add_middleware(app: FastAPI) -> None:
    """Add middleware to the FastAPI application"""
    
    # Add metrics middleware
    app.add_middleware(MetricsMiddleware)
    
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Add error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add auth middleware
    app.add_middleware(AuthMiddleware)
