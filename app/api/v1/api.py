"""
API v1 router initialization.
"""

from fastapi import APIRouter
from .endpoints import patients, visits, agents, auth, users

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(
    patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(visits.router, prefix="/visits", tags=["visits"])
api_router.include_router(agents.router, prefix="/agents", tags=["ai-agents"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
