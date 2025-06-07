"""
FastAPI Application Setup

This module configures and initializes the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import routers
from .middleware import add_middleware
from .dependencies import setup_dependencies
from config.settings import settings
from config.logging import configure_logging

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Configure logging
    configure_logging()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.API_TITLE,
        description=settings.API_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    add_middleware(app)
    
    # Setup dependencies
    setup_dependencies(app)
    
    # Include routers
    for router in routers:
        app.include_router(router, prefix=settings.API_PREFIX)
    
    return app

# Create application instance
app = create_app() 