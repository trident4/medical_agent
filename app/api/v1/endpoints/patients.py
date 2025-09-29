"""
Patient management API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.models.patient import PatientCreate, PatientUpdate, PatientResponse, PatientSummary
from app.services.patient_service import PatientService

router = APIRouter()


@router.get("/", response_model=List[PatientSummary])
async def list_patients(
    skip: int = Query(
        default=0, ge=0, description="Number of patients to skip"),
    limit: int = Query(default=100, ge=1, le=1000,
                       description="Number of patients to return"),
    search: Optional[str] = Query(
        default=None, description="Search term for patient name or ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of patients with optional search and pagination.
    """
    patient_service = PatientService(db)

    if search:
        patients = await patient_service.search_patients(search, skip, limit)
    else:
        patients = await patient_service.get_patients(skip, limit)

    return patients


@router.post("/", response_model=PatientResponse, status_code=201)
async def create_patient(
    patient: PatientCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new patient.
    """
    patient_service = PatientService(db)

    # Check if patient ID already exists
    existing_patient = await patient_service.get_patient_by_patient_id(patient.patient_id)
    if existing_patient:
        raise HTTPException(
            status_code=400,
            detail=f"Patient with ID {patient.patient_id} already exists"
        )

    created_patient = await patient_service.create_patient(patient)
    return created_patient


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific patient by ID.
    """
    patient_service = PatientService(db)
    patient = await patient_service.get_patient_by_patient_id(patient_id)

    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Patient with ID {patient_id} not found"
        )

    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_update: PatientUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a patient's information.
    """
    patient_service = PatientService(db)

    # Check if patient exists
    existing_patient = await patient_service.get_patient_by_patient_id(patient_id)
    if not existing_patient:
        raise HTTPException(
            status_code=404,
            detail=f"Patient with ID {patient_id} not found"
        )

    updated_patient = await patient_service.update_patient(patient_id, patient_update)
    return updated_patient


@router.delete("/{patient_id}", status_code=204)
async def delete_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a patient and all associated visits.
    """
    patient_service = PatientService(db)

    # Check if patient exists
    existing_patient = await patient_service.get_patient_by_patient_id(patient_id)
    if not existing_patient:
        raise HTTPException(
            status_code=404,
            detail=f"Patient with ID {patient_id} not found"
        )

    await patient_service.delete_patient(patient_id)


@router.get("/{patient_id}/visits/", response_model=List[dict])
async def get_patient_visits(
    patient_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all visits for a specific patient.
    """
    patient_service = PatientService(db)

    # Check if patient exists
    patient = await patient_service.get_patient_by_patient_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Patient with ID {patient_id} not found"
        )

    visits = await patient_service.get_patient_visits(patient_id, skip, limit)
    return visits


@router.get("/{patient_id}/summary", response_model=dict)
async def get_patient_health_summary(
    patient_id: str,
    include_recent_visits: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a comprehensive health summary for a patient.
    """
    patient_service = PatientService(db)

    # Check if patient exists
    patient = await patient_service.get_patient_by_patient_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Patient with ID {patient_id} not found"
        )

    summary = await patient_service.get_patient_health_summary(patient_id, include_recent_visits)
    return summary
