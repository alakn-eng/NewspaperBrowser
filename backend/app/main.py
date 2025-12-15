"""
FastAPI application entry point for Time Browser backend.

This is the main application file that sets up routes, middleware, and CORS.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import issues, pages


# Create FastAPI app
app = FastAPI(
    title="Time Browser API",
    description="Historical newspaper exploration and search API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(issues.router)
app.include_router(pages.router)


@app.get("/")
def root():
    """Root endpoint - API health check."""
    return {
        "service": "Time Browser API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}
