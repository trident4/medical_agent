"""
Patient management API endpoints with authentication and HIPAA compliance.
"""

import logging
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.patient import PatientCreate, PatientUpdate, PatientResponse, PatientSummary
from app.models.user import User, UserRole
from app.services.patient_service import PatientService
from app.utils.auth import get_current_user, require_role
from app.utils.pagination import PaginatedResponse, PaginationParams

logger = logging.getLogger(__name__)

# Remove prefix/tags since they're defined in api.py
router = APIRouter()


@router.get("/", response_model=Union[List[PatientSummary], PaginatedResponse[PatientSummary]])
async def list_patients(
    skip: int = Query(
        default=0, ge=0, description="Number of patients to skip (offset-based)"),
    limit: int = Query(default=100, ge=1, le=1000,
                       description="Number of patients to return (offset-based)"),
    page: Optional[int] = Query(
        default=None, ge=1, description="Page number (page-based pagination)"),
    page_size: Optional[int] = Query(
        default=None, ge=1, le=100, description="Items per page (page-based pagination)"),
    search: Optional[str] = Query(
        default=None, description="Search term for patient name or ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE))
):
    """
    Retrieve a list of patients with optional search and pagination.

    Supports two pagination modes:
    1. **Offset-based**: Use `skip` and `limit` parameters (default, backward compatible)
    2. **Page-based**: Use `page` and `page_size` parameters (returns paginated response with metadata)

    Page-based pagination returns additional metadata like total pages, has_next, has_previous.

    Requires ADMIN, DOCTOR, or NURSE role for HIPAA compliance.
    """
    logger.info("Listing patients by user: %s (role: %s)",
                current_user.username, current_user.role.value)

    patient_service = PatientService(db)

    if search:
        patients = await patient_service.search_patients(
            search_term=search,
            skip=skip,
            limit=limit,
            page=page,
            page_size=page_size
        )
    else:
        patients = await patient_service.get_patients(
            skip=skip,
            limit=limit,
            page=page,
            page_size=page_size
        )

    return patients


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DOCTOR))
):
    """
    Create a new patient.

    Requires ADMIN or DOCTOR role for HIPAA compliance.
    """
    logger.info("Creating patient by user: %s (role: %s)",
                current_user.username, current_user.role.value)

    patient_service = PatientService(db)

    # Check if patient ID already exists
    # existing_patient = await patient_service.get_patient_by_patient_id(patient.patient_id)
    # if existing_patient:
    #     logger.warning("Patient creation failed: ID %s already exists (attempted by %s)",
    #                   patient.patient_id, current_user.username)
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=f"Patient with ID {patient.patient_id} already exists"
    #     )

    created_patient = await patient_service.create_patient(patient)
    logger.info("Patient created: ID %s by user %s",
                created_patient.patient_id, current_user.username)
    return created_patient


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE))
):
    """
    Retrieve a specific patient by ID.

    Requires ADMIN, DOCTOR, or NURSE role for HIPAA compliance.
    """
    logger.info("Getting patient %d by user: %s (role: %s)",
                patient_id, current_user.username, current_user.role.value)

    patient_service = PatientService(db)
    patient = await patient_service.get_patient_by_id(patient_id)

    if not patient:
        logger.warning("Patient not found: ID %d (requested by %s)",
                       patient_id, current_user.username)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )

    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_update: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DOCTOR))
):
    """
    Update a patient's information.

    Requires ADMIN or DOCTOR role for HIPAA compliance.
    """
    logger.info("Updating patient %d by user: %s (role: %s)",
                patient_id, current_user.username, current_user.role.value)

    patient_service = PatientService(db)

    # Check if patient exists
    existing_patient = await patient_service.get_patient_by_id(patient_id)
    if not existing_patient:
        logger.warning("Patient update failed: ID %d not found (attempted by %s)",
                       patient_id, current_user.username)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )

    updated_patient = await patient_service.update_patient(patient_id, patient_update)
    logger.info("Patient updated: ID %d by user %s",
                patient_id, current_user.username)
    return updated_patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Delete a patient and all associated visits.

    Requires ADMIN role for HIPAA compliance and data protection.
    """
    logger.info("Deleting patient %s by user: %s (role: %s)",
                patient_id, current_user.username, current_user.role.value)

    patient_service = PatientService(db)

    # Check if patient exists
    existing_patient = await patient_service.get_patient_by_id(patient_id)
    if not existing_patient:
        logger.warning("Patient deletion failed: ID %d not found (attempted by %s)",
                       patient_id, current_user.username)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )

    await patient_service.delete_patient(patient_id)
    logger.info("Patient deleted: ID %s by user %s",
                patient_id, current_user.username)


@router.get("/{patient_id}/visits/", response_model=List[dict])
async def get_patient_visits(
    patient_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE))
):
    """
    Retrieve all visits for a specific patient.

    Requires ADMIN, DOCTOR, or NURSE role for HIPAA compliance.
    """
    logger.info("Getting visits for patient %d by user: %s (role: %s)",
                patient_id, current_user.username, current_user.role.value)

    patient_service = PatientService(db)

    # Check if patient exists
    patient = await patient_service.get_patient_by_patient_id(patient_id)
    if not patient:
        logger.warning("Patient visits request failed: ID %s not found (requested by %s)",
                       patient_id, current_user.username)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )

    visits = await patient_service.get_patient_visits(patient_id, skip, limit)
    return visits


@router.get("/{patient_id}/summary", response_model=dict)
async def get_patient_health_summary(
    patient_id: int,
    include_recent_visits: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DOCTOR))
):
    """
    Get a comprehensive health summary for a patient.

    Requires ADMIN or DOCTOR role for HIPAA compliance.
    """
    logger.info("Getting health summary for patient %d by user: %s (role: %s)",
                patient_id, current_user.username, current_user.role.value)

    patient_service = PatientService(db)

    # Check if patient exists
    patient = await patient_service.get_patient_by_id(patient_id)
    if not patient:
        logger.warning("Patient summary request failed: ID %d not found (requested by %s)",
                       patient_id, current_user.username)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )

    summary = await patient_service.get_patient_health_summary(patient_id, include_recent_visits)
    return summary
