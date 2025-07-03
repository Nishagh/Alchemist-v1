"""
Knowledge Vault Routes Registration

This module registers all API routes for the Knowledge Vault service.
"""

from fastapi import FastAPI
from . import files, vectors


def register_routes(app: FastAPI):
    """Register all routes with the FastAPI app"""
    
    # Include file management routes
    app.include_router(files.router, prefix="/api", tags=["files"])
    
    # Include vector/search routes  
    app.include_router(vectors.router, prefix="/api", tags=["vectors"])