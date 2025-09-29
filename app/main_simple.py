"""
Simple FastAPI application without AI agents for testing.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from app.config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Medical Assistant API (Basic Mode)")
    yield
    # Shutdown
    logger.info("Shutting down Medical Assistant API")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered medical assistant for doctors to analyze patient visit data",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Medical Assistant API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "running",
        "mode": "basic"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get(f"{settings.API_V1_STR}/patients")
async def list_patients():
    """Placeholder patient endpoint."""
    return {
        "message": "Patient endpoint working",
        "note": "Database and full functionality will be available after PostgreSQL setup"
    }


@app.get(f"{settings.API_V1_STR}/visits")
async def list_visits():
    """Placeholder visits endpoint."""
    return {
        "message": "Visits endpoint working",
        "note": "Database and full functionality will be available after PostgreSQL setup"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
