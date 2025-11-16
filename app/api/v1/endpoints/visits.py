"""
Visit management API endpoints with authentication and HIPAA compliance.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.visit import VisitCreate, VisitUpdate, VisitResponse, VisitSummary
from app.models.user import User, UserRole
from app.services.visit_service import VisitService
from app.utils.auth import get_current_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[VisitSummary])
async def list_visits(
    skip: int = Query(default=0, ge=0, description="Number of visits to skip"),
    limit: int = Query(default=100, ge=1, le=1000,
                       description="Number of visits to return"),
    patient_id: Optional[str] = Query(
        default=None, description="Filter by patient ID"),
    visit_type: Optional[str] = Query(
        default=None, description="Filter by visit type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE))
):
    """
    Retrieve a list of visits with optional filtering and pagination.

    Requires ADMIN, DOCTOR, or NURSE role for HIPAA compliance.
    """
    logger.info("Listing visits by user: %s (role: %s)",
                current_user.username, current_user.role.value)

    visit_service = VisitService(db)
    visits = await visit_service.get_visits(skip, limit, patient_id, visit_type)
    return visits


@router.post("/", response_model=VisitResponse, status_code=201)
async def create_visit(
    visit: VisitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DOCTOR))
):
    """
    Create a new visit.

    Requires ADMIN or DOCTOR role for HIPAA compliance.
    """
    logger.info("Creating visit by user: %s (role: %s)",
                current_user.username, current_user.role.value)

    visit_service = VisitService(db)

    # Check if visit ID already exists
    # existing_visit = await visit_service.get_visit_by_visit_id(visit.visit_id)
    # if existing_visit:
    #     raise HTTPException(
    #         status_code=400,
    #         detail=f"Visit with ID {visit.visit_id} already exists"
    #     )

    created_visit = await visit_service.create_visit(visit)
    logger.info("Visit created: ID %s by user %s",
                created_visit.visit_id, current_user.username)
    return created_visit


@router.get("/{db_id}", response_model=VisitResponse)
async def get_visit_by_db_id(
    db_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE))
):
    """
    Retrieve a specific visit by database ID.

    Requires ADMIN, DOCTOR, or NURSE role for HIPAA compliance.
    """
    logger.info("Getting visit by DB ID %d by user: %s (role: %s)", db_id,
                current_user.username, current_user.role.value)

    visit_service = VisitService(db)
    visit = await visit_service.get_visit_by_id(db_id)

    if not visit:
        logger.warning("Visit not found: DB ID %d (requested by %s)",
                       db_id, current_user.username)
        raise HTTPException(
            status_code=404,
            detail=f"Visit with DB ID {db_id} not found"
        )

    return visit


@router.put("/{db_id}", response_model=VisitResponse)
async def update_visit(
    db_id: int,
    visit_update: VisitUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DOCTOR))
):
    """
    Update a visit's information.

    Requires ADMIN or DOCTOR role for HIPAA compliance.
    """
    logger.info("Updating visit %d by user: %s (role: %s)",
                db_id, current_user.username, current_user.role.value)

    visit_service = VisitService(db)

    # Check if visit exists
    existing_visit = await visit_service.get_visit_by_id(db_id)
    if not existing_visit:
        logger.warning("Visit update failed: ID %d not found (attempted by %s)",
                       db_id, current_user.username)
        raise HTTPException(
            status_code=404,
            detail=f"Visit with ID {db_id} not found"
        )

    updated_visit = await visit_service.update_visit(db_id, visit_update)
    logger.info("Visit updated: ID %d by user %s",
                db_id, current_user.username)
    return updated_visit


@router.delete("/{db_id}", status_code=204)
async def delete_visit(
    db_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Delete a visit.

    Requires ADMIN role for HIPAA compliance and data protection.
    """
    logger.info("Deleting visit %d by user: %s (role: %s)",
                db_id, current_user.username, current_user.role.value)

    visit_service = VisitService(db)

    # Check if visit exists
    existing_visit = await visit_service.get_visit_by_id(db_id)
    if not existing_visit:
        logger.warning("Visit deletion failed: ID %d not found (attempted by %s)",
                       db_id, current_user.username)
        raise HTTPException(
            status_code=404,
            detail=f"Visit with ID {db_id} not found"
        )

    await visit_service.delete_visit(db_id)
    logger.info("Visit deleted: ID %d by user %s",
                db_id, current_user.username)


@router.get("/{db_id}/patient", response_model=dict)
async def get_visit_patient(
    db_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE))
):
    """
    Get the patient information for a specific visit.

    Requires ADMIN, DOCTOR, or NURSE role for HIPAA compliance.
    """
    logger.info("Getting patient for visit %d by user: %s (role: %s)",
                db_id, current_user.username, current_user.role.value)

    visit_service = VisitService(db)

    # Check if visit exists
    visit = await visit_service.get_visit_by_id(db_id)
    if not visit:
        logger.warning("Visit patient request failed: ID %d not found (requested by %s)",
                       db_id, current_user.username)
        raise HTTPException(
            status_code=404,
            detail=f"Visit with ID {db_id} not found"
        )

    patient = await visit_service.get_visit_patient(db_id)
    return patient
