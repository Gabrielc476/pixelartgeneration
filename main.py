"""
Sora Pixel Art Generator - Backend API
======================================
FastAPI app for pixel art generation using GPT-4o Images
"""

import os
import time
from pathlib import Path

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.database import create_tables

# Setup
settings = get_settings()
logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="Sora Pixel Art Generator API",
    description="Generate pixel art animations using GPT-4o Images",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup
@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    await create_tables()
    logger.info("Database initialized")

# Create storage directories
def create_directories():
    dirs = ["storage", "storage/uploads", "storage/jobs", "storage/temp"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

create_directories()

# Serve static files in development
if settings.DEBUG:
    app.mount("/static", StaticFiles(directory="storage"), name="static")

# Routes
@app.get("/")
def root():
    return {
        "service": "Sora Pixel Art Generator API",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else None,
        "status": "running"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": time.time()}

# TODO: Add API endpoints
# from app.api.endpoints import generation, jobs, upload
# app.include_router(generation.router, prefix="/api/v1")
# app.include_router(jobs.router, prefix="/api/v1")
# app.include_router(upload.router, prefix="/api/v1")

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# Run server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )