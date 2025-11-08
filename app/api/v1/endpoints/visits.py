"""
Visit management API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.models.visit import VisitCreate, VisitUpdate, VisitResponse, VisitSummary
from app.services.visit_service import VisitService

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
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of visits with optional filtering and pagination.
    """
    visit_service = VisitService(db)
    visits = await visit_service.get_visits(skip, limit, patient_id, visit_type)
    return visits


@router.post("/", response_model=VisitResponse, status_code=201)
async def create_visit(
    visit: VisitCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new visit.
    """
    visit_service = VisitService(db)

    # Check if visit ID already exists
    # existing_visit = await visit_service.get_visit_by_visit_id(visit.visit_id)
    # if existing_visit:
    #     raise HTTPException(
    #         status_code=400,
    #         detail=f"Visit with ID {visit.visit_id} already exists"
    #     )

    created_visit = await visit_service.create_visit(visit)
    return created_visit


@router.get("/{visit_id}", response_model=VisitResponse)
async def get_visit(
    visit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific visit by ID.
    """
    visit_service = VisitService(db)
    visit = await visit_service.get_visit_by_visit_id(visit_id)

    if not visit:
        raise HTTPException(
            status_code=404,
            detail=f"Visit with ID {visit_id} not found"
        )

    return visit


@router.put("/{visit_id}", response_model=VisitResponse)
async def update_visit(
    visit_id: str,
    visit_update: VisitUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a visit's information.
    """
    visit_service = VisitService(db)

    # Check if visit exists
    existing_visit = await visit_service.get_visit_by_visit_id(visit_id)
    if not existing_visit:
        raise HTTPException(
            status_code=404,
            detail=f"Visit with ID {visit_id} not found"
        )

    updated_visit = await visit_service.update_visit(visit_id, visit_update)
    return updated_visit


@router.delete("/{visit_id}", status_code=204)
async def delete_visit(
    visit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a visit.
    """
    visit_service = VisitService(db)

    # Check if visit exists
    existing_visit = await visit_service.get_visit_by_visit_id(visit_id)
    if not existing_visit:
        raise HTTPException(
            status_code=404,
            detail=f"Visit with ID {visit_id} not found"
        )

    await visit_service.delete_visit(visit_id)


@router.get("/{visit_id}/patient", response_model=dict)
async def get_visit_patient(
    visit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the patient information for a specific visit.
    """
    visit_service = VisitService(db)

    # Check if visit exists
    visit = await visit_service.get_visit_by_visit_id(visit_id)
    if not visit:
        raise HTTPException(
            status_code=404,
            detail=f"Visit with ID {visit_id} not found"
        )

    patient = await visit_service.get_visit_patient(visit_id)
    return patient
