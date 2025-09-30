"""
Development version of main.py that works without AI API keys.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
import os

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
    logger.info("Starting Medical Assistant API (Development Mode)")

    # Only try to create database tables if we have a real database URL
    if not settings.DATABASE_URL.startswith("postgresql://username:password"):
        try:
            from app.database.session import engine
            from app.database.base import Base

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database tables created successfully")
        except Exception as e:
            logger.warning("Database setup skipped", error=str(e))
    else:
        logger.info("Database setup skipped - using placeholder URL")

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

# Include API routes (some features may be disabled without API keys)
try:
    # Import patient and visit routes
    from fastapi import APIRouter
    from app.api.v1.endpoints import patients, visits

    # Create our own API router for development
    api_router = APIRouter()
    api_router.include_router(
        patients.router, prefix="/patients", tags=["patients"])
    api_router.include_router(visits.router, prefix="/visits", tags=["visits"])

    # Only include AI agents if we have at least one API key
    ai_keys_available = []
    if (settings.OPENAI_API_KEY and
        settings.OPENAI_API_KEY != "your-openai-api-key" and
            not settings.OPENAI_API_KEY.startswith("dummy")):
        ai_keys_available.append("OpenAI")

    if (settings.XAI_API_KEY and
            settings.XAI_API_KEY != "your-xai-api-key-here"):
        ai_keys_available.append("X.AI")

    if (settings.ANTHROPIC_API_KEY and
            settings.ANTHROPIC_API_KEY != "your-anthropic-api-key"):
        ai_keys_available.append("Anthropic")

    if ai_keys_available:
        try:
            from app.api.v1.endpoints import agents_fallback as agents
            api_router.include_router(
                agents.router, prefix="/ai", tags=["ai-agents"])
            ai_enabled = True
            logger.info(
                f"AI features enabled with providers: {', '.join(ai_keys_available)}")
        except Exception as e:
            logger.warning(
                "AI features disabled - API import issue", error=str(e))
            ai_enabled = False
    else:
        logger.info("AI features disabled - no valid API keys found")
        ai_enabled = False

    app.include_router(api_router, prefix=settings.API_V1_STR)
    api_enabled = True

except Exception as e:
    logger.warning("API routes disabled", error=str(e))
    api_enabled = False
    ai_enabled = False

# Basic endpoints


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Medical Assistant API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "running",
        "mode": "development",
        "ai_enabled": ai_enabled,
        "api_enabled": api_enabled,
        "database_configured": not settings.DATABASE_URL.startswith("postgresql://username:password")
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "ai_enabled": ai_enabled,
        "api_enabled": api_enabled
    }


# Setup status endpoint
@app.get(f"{settings.API_V1_STR}/setup-status")
async def setup_status():
    """Check what's needed to enable full functionality."""
    return {
        "api_routes": "✅ Enabled" if api_enabled else "❌ Disabled",
        "openai_api_key": "✅ Set" if ai_enabled else "❌ Not set - AI features disabled",
        "database_url": "✅ Configured" if not settings.DATABASE_URL.startswith("postgresql://username:password") else "❌ Using placeholder",
        "next_steps": [] if ai_enabled else [
            "Set OPENAI_API_KEY in .env file to enable AI features",
            "All other features are working normally"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_dev:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
