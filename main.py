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

# Import routers
from app.api.endpoints.generation import router as generation_router
from app.api.endpoints.jobs import router as jobs_router

# Setup
settings = get_settings()
logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="Sora Pixel Art Generator API",
    description="""
    ## Sora Pixel Art Generator
    
    API para geração de sprite sheets e frames individuais de pixel art usando GPT-4o Images.
    
    ### Funcionalidades
    
    - **Geração por Prompt**: Crie animações baseadas em descrições de texto
    - **Dual Output**: Escolha entre sprite sheets ou frames individuais
    - **Estilos Variados**: 8-bit, 16-bit, Game Boy, NES e outros
    - **Processamento Assíncrono**: Acompanhe progresso via polling HTTP
    - **Preview Animado**: GIFs de preview automáticos
    - **Otimização**: Compressão e otimização para games
    
    ### Formatos de Output
    
    - **Sprite Sheet**: Todos os frames em uma única imagem (ideal para game engines)
    - **Individual Frames**: Frames separados (ideal para editores como Aseprite)
    
    ### Fluxo Básico
    
    1. Criar geração com `POST /api/v1/generation/create`
    2. Acompanhar progresso com `GET /api/v1/jobs/{job_id}`
    3. Baixar arquivos quando concluído
    
    ### Status dos Jobs
    
    - `created`: Job criado, aguardando processamento
    - `processing`: Preparando geração
    - `generating`: Gerando frames com IA
    - `post_processing`: Processando e organizando arquivos
    - `completed`: Concluído com sucesso
    - `failed`: Falhou (verifique error_message)
    """,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
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
    try:
        await create_tables()
        logger.info("Database initialized successfully")

        # Create storage directories
        create_directories()
        logger.info("Storage directories created")

    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise

# Create storage directories
def create_directories():
    """Create necessary storage directories"""
    dirs = [
        "storage",
        "storage/uploads",
        "storage/jobs",
        "storage/temp",
        "storage/exports",
        "storage/cache"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

# Serve static files in development
if settings.DEBUG:
    app.mount("/static", StaticFiles(directory="storage"), name="static")

# Include routers
app.include_router(
    generation_router,
    prefix="/api/v1",
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

app.include_router(
    jobs_router,
    prefix="/api/v1",
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

# Root endpoint
@app.get("/", tags=["root"])
def root():
    """Root endpoint with API information"""
    return {
        "service": "Sora Pixel Art Generator API",
        "version": "1.0.0",
        "description": "Generate pixel art animations using GPT-4o Images",
        "docs": "/docs" if settings.DEBUG else None,
        "endpoints": {
            "generation": "/api/v1/generation",
            "jobs": "/api/v1/jobs",
            "health": "/health"
        },
        "features": [
            "Prompt-based generation",
            "Dual output formats (sprite sheets & individual frames)",
            "Multiple pixel art styles",
            "Asynchronous processing",
            "Animated previews"
        ],
        "status": "running"
    }

@app.get("/health", tags=["health"])
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "storage": "available",
            "openai": "configured"
        }
    }

@app.get("/api/v1", tags=["api"])
def api_root():
    """API v1 root endpoint"""
    return {
        "version": "1.0.0",
        "endpoints": {
            "generation": {
                "create": "POST /api/v1/generation/create",
                "prompt": "POST /api/v1/generation/prompt",
                "presets": "GET /api/v1/generation/presets/{type}",
                "validate": "POST /api/v1/generation/validate",
                "limits": "GET /api/v1/generation/limits"
            },
            "jobs": {
                "status": "GET /api/v1/jobs/{job_id}",
                "list": "GET /api/v1/jobs",
                "progress": "GET /api/v1/jobs/{job_id}/progress",
                "retry": "POST /api/v1/jobs/{job_id}/retry",
                "files": "GET /api/v1/jobs/{job_id}/files",
                "stats": "GET /api/v1/jobs/stats/summary"
            }
        },
        "documentation": "/docs" if settings.DEBUG else "Contact support for API documentation"
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": time.time()
        }
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": "Endpoint not found",
            "error_code": "NOT_FOUND",
            "available_endpoints": {
                "generation": "/api/v1/generation",
                "jobs": "/api/v1/jobs",
                "docs": "/docs" if settings.DEBUG else None
            },
            "timestamp": time.time()
        }
    )

# Development middleware
if settings.DEBUG:
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all requests in development"""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            "Request processed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time=round(process_time, 4)
        )

        return response

# Run server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
        access_log=settings.DEBUG
    )