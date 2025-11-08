# Adding New Endpoints - Complete Step-by-Step Guide

A comprehensive guide to adding new REST API endpoints to the Medical Assistant project using FastAPI, SQLAlchemy, and best practices.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Layers](#architecture-layers)
3. [Step-by-Step Tutorial](#step-by-step-tutorial)
4. [Example: Adding Prescriptions Feature](#example-adding-prescriptions-feature)
5. [Testing Your Endpoint](#testing-your-endpoint)
6. [Best Practices](#best-practices)
7. [Common Patterns](#common-patterns)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### What We'll Build

In this guide, we'll add a complete **Prescriptions** feature to our medical assistant, including:

- ✅ Database model
- ✅ Pydantic schemas for validation
- ✅ Service layer for business logic
- ✅ API endpoints for CRUD operations
- ✅ Database migration
- ✅ Tests

### The Process

```
1. Define Database Model (SQLAlchemy)
   ↓
2. Create Pydantic Schemas (Validation)
   ↓
3. Generate Migration (Alembic)
   ↓
4. Build Service Layer (Business Logic)
   ↓
5. Create API Endpoints (FastAPI)
   ↓
6. Register Router (Main App)
   ↓
7. Write Tests
   ↓
8. Document API
```

**Time Required:** ~30-45 minutes for a complete feature

---

## Architecture Layers

Before we start, let's understand the layers we'll work with:

```
┌─────────────────────────────────────────┐
│         API Layer (FastAPI)             │
│     app/api/v1/endpoints/               │
│  - Route handlers                       │
│  - Request/Response models              │
│  - HTTP status codes                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│       Service Layer                     │
│     app/services/                       │
│  - Business logic                       │
│  - Data validation                      │
│  - Orchestration                        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Database Layer (SQLAlchemy)         │
│     app/models/                         │
│  - ORM models                           │
│  - Database operations                  │
│  - Relationships                        │
└─────────────────────────────────────────┘
               │
               ▼
         PostgreSQL
```

**Why This Architecture?**

- **Separation of Concerns**: Each layer has one responsibility
- **Testability**: Can test each layer independently
- **Reusability**: Services can be used by multiple endpoints
- **Maintainability**: Changes in one layer don't affect others

---

## Step-by-Step Tutorial

### Step 1: Define Database Model

**File: `app/models/prescription.py`**

```python
# filepath: app/models/prescription.py
"""
Database models for prescriptions.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class Prescription(Base):
    """
    Database model for medication prescriptions.

    Attributes:
        id: Internal database ID
        prescription_id: External identifier (e.g., RX001)
        patient_id: Foreign key to patient
        visit_id: Foreign key to visit (optional)
        medication_name: Name of prescribed medication
        dosage: Dosage information (e.g., "500mg")
        frequency: How often to take (e.g., "twice daily")
        duration_days: Number of days to take medication
        quantity: Total quantity prescribed
        refills: Number of refills allowed
        instructions: Special instructions for patient
        prescribing_doctor: Name of prescribing physician
        is_active: Whether prescription is currently active
        start_date: When to start taking medication
        end_date: When prescription ends
        created_at: When record was created
        updated_at: When record was last updated
    """
    __tablename__ = "prescriptions"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Identifiers
    prescription_id = Column(String, unique=True, index=True, nullable=False)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False, index=True)
    visit_id = Column(String, ForeignKey("visits.visit_id"), nullable=True)

    # Medication details
    medication_name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    duration_days = Column(Integer)
    quantity = Column(Integer)
    refills = Column(Integer, default=0)

    # Instructions and notes
    instructions = Column(Text)
    prescribing_doctor = Column(String)

    # Status
    is_active = Column(Boolean, default=True)

    # Dates
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    visit = relationship("Visit", back_populates="prescriptions")


# Update Patient model to include relationship
# filepath: app/models/patient.py
class Patient(Base):
    # ... existing code ...

    # Add this relationship
    prescriptions = relationship("Prescription", back_populates="patient")


# Update Visit model to include relationship
# filepath: app/models/visit.py
class Visit(Base):
    # ... existing code ...

    # Add this relationship
    prescriptions = relationship("Prescription", back_populates="visit")
```

**Key Points:**

- ✅ Use descriptive column names
- ✅ Add proper indexes for foreign keys
- ✅ Include audit fields (created_at, updated_at)
- ✅ Add docstrings explaining the model
- ✅ Define relationships to other models

---

### Step 2: Create Pydantic Schemas

**File: `app/models/prescription.py` (add to same file)**

```python
# filepath: app/models/prescription.py
"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional


class PrescriptionBase(BaseModel):
    """Base schema with common fields."""
    medication_name: str = Field(..., description="Name of medication", min_length=1, max_length=200)
    dosage: str = Field(..., description="Dosage (e.g., 500mg)", min_length=1, max_length=100)
    frequency: str = Field(..., description="How often to take (e.g., twice daily)", min_length=1, max_length=100)
    duration_days: Optional[int] = Field(None, description="Duration in days", ge=1, le=365)
    quantity: Optional[int] = Field(None, description="Total quantity", ge=1)
    refills: int = Field(0, description="Number of refills", ge=0, le=12)
    instructions: Optional[str] = Field(None, description="Special instructions")
    prescribing_doctor: Optional[str] = Field(None, description="Prescribing physician name")
    start_date: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Start date")
    end_date: Optional[datetime] = None


class PrescriptionCreate(PrescriptionBase):
    """Schema for creating a new prescription."""
    prescription_id: str = Field(..., description="Unique prescription ID (e.g., RX001)", regex=r'^RX\d{6}$')
    patient_id: str = Field(..., description="Patient identifier")
    visit_id: Optional[str] = Field(None, description="Associated visit ID")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Ensure end_date is after start_date."""
        if v and 'start_date' in values and v < values['start_date']:
            raise ValueError("end_date must be after start_date")
        return v

    @validator('prescription_id')
    def validate_prescription_id(cls, v):
        """Ensure prescription_id follows format RX######."""
        if not v.startswith('RX'):
            raise ValueError("prescription_id must start with 'RX'")
        return v


class PrescriptionUpdate(BaseModel):
    """Schema for updating an existing prescription."""
    medication_name: Optional[str] = Field(None, min_length=1, max_length=200)
    dosage: Optional[str] = Field(None, min_length=1, max_length=100)
    frequency: Optional[str] = Field(None, min_length=1, max_length=100)
    duration_days: Optional[int] = Field(None, ge=1, le=365)
    quantity: Optional[int] = Field(None, ge=1)
    refills: Optional[int] = Field(None, ge=0, le=12)
    instructions: Optional[str] = None
    is_active: Optional[bool] = None
    end_date: Optional[datetime] = None


class PrescriptionResponse(PrescriptionBase):
    """Schema for API responses."""
    id: int
    prescription_id: str
    patient_id: str
    visit_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True  # Allows reading from ORM models


class PrescriptionSummary(BaseModel):
    """Lightweight schema for listing prescriptions."""
    prescription_id: str
    medication_name: str
    dosage: str
    frequency: str
    is_active: bool
    start_date: datetime

    class Config:
        from_attributes = True
```

**Key Points:**

- ✅ Separate schemas for create, update, and response
- ✅ Use Field() for validation and documentation
- ✅ Add custom validators where needed
- ✅ Include Config class for ORM compatibility
- ✅ Create summary schemas for list endpoints

---

### Step 3: Generate Database Migration

```bash
# Generate migration automatically
alembic revision --autogenerate -m "Create prescriptions table"

# Review the generated migration
cat alembic/versions/YYYYMMDD_HHMM_*_create_prescriptions_table.py

# Apply the migration
alembic upgrade head
```

**Generated Migration Example:**

```python
# filepath: alembic/versions/20251108_1600_abc123_create_prescriptions_table.py
"""Create prescriptions table

Revision ID: abc123
Revises: xyz789
Create Date: 2025-11-08 16:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = 'xyz789'


def upgrade():
    """Create prescriptions table."""
    op.create_table(
        'prescriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prescription_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('visit_id', sa.String(), nullable=True),
        sa.Column('medication_name', sa.String(), nullable=False),
        sa.Column('dosage', sa.String(), nullable=False),
        sa.Column('frequency', sa.String(), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('refills', sa.Integer(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('prescribing_doctor', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id']),
        sa.ForeignKeyConstraint(['visit_id'], ['visits.visit_id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_prescriptions_prescription_id', 'prescriptions', ['prescription_id'], unique=True)
    op.create_index('ix_prescriptions_patient_id', 'prescriptions', ['patient_id'], unique=False)


def downgrade():
    """Drop prescriptions table."""
    op.drop_index('ix_prescriptions_patient_id', table_name='prescriptions')
    op.drop_index('ix_prescriptions_prescription_id', table_name='prescriptions')
    op.drop_table('prescriptions')
```

---

### Step 4: Build Service Layer

**File: `app/services/prescription_service.py`**

```python
# filepath: app/services/prescription_service.py
"""
Service layer for prescription-related business logic.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import datetime
import logging

from app.models.prescription import (
    Prescription,
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionResponse,
    PrescriptionSummary
)

logger = logging.getLogger(__name__)


class PrescriptionService:
    """Service class for prescription operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    async def create_prescription(
        self,
        prescription_data: PrescriptionCreate
    ) -> PrescriptionResponse:
        """
        Create a new prescription.

        Args:
            prescription_data: Prescription creation data

        Returns:
            Created prescription

        Raises:
            HTTPException: If prescription_id already exists
        """
        logger.info(f"Creating prescription {prescription_data.prescription_id}")

        # Check if prescription_id already exists
        existing = await self.get_prescription_by_id(prescription_data.prescription_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Prescription {prescription_data.prescription_id} already exists"
            )

        # Create new prescription
        db_prescription = Prescription(**prescription_data.model_dump())
        self.db.add(db_prescription)

        try:
            await self.db.commit()
            await self.db.refresh(db_prescription)
            logger.info(f"Successfully created prescription {prescription_data.prescription_id}")
            return PrescriptionResponse.model_validate(db_prescription)
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating prescription: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create prescription"
            )

    async def get_prescription_by_id(
        self,
        prescription_id: str
    ) -> Optional[PrescriptionResponse]:
        """
        Get prescription by prescription_id.

        Args:
            prescription_id: Unique prescription identifier

        Returns:
            Prescription if found, None otherwise
        """
        query = select(Prescription).where(
            Prescription.prescription_id == prescription_id
        )
        result = await self.db.execute(query)
        prescription = result.scalar_one_or_none()

        if prescription:
            return PrescriptionResponse.model_validate(prescription)
        return None

    async def get_prescriptions(
        self,
        skip: int = 0,
        limit: int = 100,
        patient_id: Optional[str] = None,
        visit_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        medication_name: Optional[str] = None
    ) -> List[PrescriptionSummary]:
        """
        Get prescriptions with optional filtering.

        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            patient_id: Filter by patient ID
            visit_id: Filter by visit ID
            is_active: Filter by active status
            medication_name: Filter by medication name (partial match)

        Returns:
            List of prescriptions
        """
        query = select(Prescription)

        # Apply filters
        conditions = []
        if patient_id:
            conditions.append(Prescription.patient_id == patient_id)
        if visit_id:
            conditions.append(Prescription.visit_id == visit_id)
        if is_active is not None:
            conditions.append(Prescription.is_active == is_active)
        if medication_name:
            conditions.append(Prescription.medication_name.ilike(f"%{medication_name}%"))

        if conditions:
            query = query.where(and_(*conditions))

        # Apply sorting and pagination
        query = query.order_by(Prescription.start_date.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        prescriptions = result.scalars().all()

        return [PrescriptionSummary.model_validate(p) for p in prescriptions]

    async def update_prescription(
        self,
        prescription_id: str,
        prescription_data: PrescriptionUpdate
    ) -> PrescriptionResponse:
        """
        Update an existing prescription.

        Args:
            prescription_id: Prescription to update
            prescription_data: Updated prescription data

        Returns:
            Updated prescription

        Raises:
            HTTPException: If prescription not found
        """
        logger.info(f"Updating prescription {prescription_id}")

        # Get existing prescription
        query = select(Prescription).where(
            Prescription.prescription_id == prescription_id
        )
        result = await self.db.execute(query)
        db_prescription = result.scalar_one_or_none()

        if not db_prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prescription {prescription_id} not found"
            )

        # Update fields (only non-None values)
        update_data = prescription_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_prescription, field, value)

        try:
            await self.db.commit()
            await self.db.refresh(db_prescription)
            logger.info(f"Successfully updated prescription {prescription_id}")
            return PrescriptionResponse.model_validate(db_prescription)
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating prescription: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update prescription"
            )

    async def deactivate_prescription(
        self,
        prescription_id: str
    ) -> PrescriptionResponse:
        """
        Deactivate a prescription (soft delete).

        Args:
            prescription_id: Prescription to deactivate

        Returns:
            Deactivated prescription
        """
        logger.info(f"Deactivating prescription {prescription_id}")

        return await self.update_prescription(
            prescription_id,
            PrescriptionUpdate(is_active=False, end_date=datetime.utcnow())
        )

    async def delete_prescription(
        self,
        prescription_id: str
    ) -> bool:
        """
        Permanently delete a prescription (hard delete).

        Args:
            prescription_id: Prescription to delete

        Returns:
            True if deleted successfully

        Raises:
            HTTPException: If prescription not found
        """
        logger.info(f"Deleting prescription {prescription_id}")

        query = select(Prescription).where(
            Prescription.prescription_id == prescription_id
        )
        result = await self.db.execute(query)
        db_prescription = result.scalar_one_or_none()

        if not db_prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prescription {prescription_id} not found"
            )

        try:
            await self.db.delete(db_prescription)
            await self.db.commit()
            logger.info(f"Successfully deleted prescription {prescription_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting prescription: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete prescription"
            )

    async def get_patient_active_prescriptions(
        self,
        patient_id: str
    ) -> List[PrescriptionResponse]:
        """
        Get all active prescriptions for a patient.

        Args:
            patient_id: Patient identifier

        Returns:
            List of active prescriptions
        """
        query = select(Prescription).where(
            and_(
                Prescription.patient_id == patient_id,
                Prescription.is_active == True
            )
        ).order_by(Prescription.start_date.desc())

        result = await self.db.execute(query)
        prescriptions = result.scalars().all()

        return [PrescriptionResponse.model_validate(p) for p in prescriptions]
```

**Key Points:**

- ✅ All business logic in service layer
- ✅ Proper error handling with HTTPException
- ✅ Comprehensive logging
- ✅ Type hints for all methods
- ✅ Docstrings explaining parameters and returns
- ✅ Transaction management (commit/rollback)

---

### Step 5: Create API Endpoints

**File: `app/api/v1/endpoints/prescriptions.py`**

```python
# filepath: app/api/v1/endpoints/prescriptions.py
"""
API endpoints for prescription management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.prescription_service import PrescriptionService
from app.models.prescription import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionResponse,
    PrescriptionSummary
)

# Create router
router = APIRouter()


@router.post(
    "/",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new prescription",
    description="Create a new medication prescription for a patient"
)
async def create_prescription(
    prescription: PrescriptionCreate,
    db: AsyncSession = Depends(get_db)
) -> PrescriptionResponse:
    """
    Create a new prescription.

    - **prescription_id**: Unique identifier (format: RX######)
    - **patient_id**: Patient this prescription is for
    - **medication_name**: Name of medication
    - **dosage**: Dosage information (e.g., 500mg)
    - **frequency**: How often to take (e.g., twice daily)

    Returns the created prescription with all details.
    """
    service = PrescriptionService(db)
    return await service.create_prescription(prescription)


@router.get(
    "/{prescription_id}",
    response_model=PrescriptionResponse,
    summary="Get prescription by ID",
    description="Retrieve detailed information about a specific prescription"
)
async def get_prescription(
    prescription_id: str,
    db: AsyncSession = Depends(get_db)
) -> PrescriptionResponse:
    """
    Get a prescription by its ID.

    Args:
        prescription_id: Unique prescription identifier

    Returns:
        Prescription details

    Raises:
        404: If prescription not found
    """
    service = PrescriptionService(db)
    prescription = await service.get_prescription_by_id(prescription_id)

    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription {prescription_id} not found"
        )

    return prescription


@router.get(
    "/",
    response_model=List[PrescriptionSummary],
    summary="List prescriptions",
    description="Get a list of prescriptions with optional filtering"
)
async def list_prescriptions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    visit_id: Optional[str] = Query(None, description="Filter by visit ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    medication_name: Optional[str] = Query(None, description="Filter by medication name"),
    db: AsyncSession = Depends(get_db)
) -> List[PrescriptionSummary]:
    """
    List prescriptions with optional filters.

    Query parameters:
    - **skip**: Pagination offset
    - **limit**: Maximum results to return
    - **patient_id**: Filter by patient
    - **visit_id**: Filter by visit
    - **is_active**: Filter by active status
    - **medication_name**: Search by medication name

    Returns list of prescription summaries.
    """
    service = PrescriptionService(db)
    return await service.get_prescriptions(
        skip=skip,
        limit=limit,
        patient_id=patient_id,
        visit_id=visit_id,
        is_active=is_active,
        medication_name=medication_name
    )


@router.put(
    "/{prescription_id}",
    response_model=PrescriptionResponse,
    summary="Update prescription",
    description="Update an existing prescription"
)
async def update_prescription(
    prescription_id: str,
    prescription_data: PrescriptionUpdate,
    db: AsyncSession = Depends(get_db)
) -> PrescriptionResponse:
    """
    Update an existing prescription.

    Only provided fields will be updated.

    Args:
        prescription_id: Prescription to update
        prescription_data: Fields to update

    Returns:
        Updated prescription
    """
    service = PrescriptionService(db)
    return await service.update_prescription(prescription_id, prescription_data)


@router.post(
    "/{prescription_id}/deactivate",
    response_model=PrescriptionResponse,
    summary="Deactivate prescription",
    description="Mark a prescription as inactive (soft delete)"
)
async def deactivate_prescription(
    prescription_id: str,
    db: AsyncSession = Depends(get_db)
) -> PrescriptionResponse:
    """
    Deactivate a prescription (soft delete).

    Sets is_active=False and end_date to current time.
    The prescription remains in the database for historical records.

    Args:
        prescription_id: Prescription to deactivate

    Returns:
        Deactivated prescription
    """
    service = PrescriptionService(db)
    return await service.deactivate_prescription(prescription_id)


@router.delete(
    "/{prescription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete prescription",
    description="Permanently delete a prescription (hard delete)"
)
async def delete_prescription(
    prescription_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Permanently delete a prescription (hard delete).

    ⚠️ Warning: This cannot be undone!
    Consider using deactivate endpoint for soft delete instead.

    Args:
        prescription_id: Prescription to delete

    Returns:
        204 No Content on success
    """
    service = PrescriptionService(db)
    await service.delete_prescription(prescription_id)
    return None


@router.get(
    "/patient/{patient_id}/active",
    response_model=List[PrescriptionResponse],
    summary="Get patient's active prescriptions",
    description="Get all active prescriptions for a specific patient"
)
async def get_patient_active_prescriptions(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
) -> List[PrescriptionResponse]:
    """
    Get all active prescriptions for a patient.

    Useful for checking current medications.

    Args:
        patient_id: Patient identifier

    Returns:
        List of active prescriptions
    """
    service = PrescriptionService(db)
    return await service.get_patient_active_prescriptions(patient_id)
```

**Key Points:**

- ✅ RESTful URL patterns
- ✅ Proper HTTP status codes
- ✅ Query parameters for filtering
- ✅ Comprehensive docstrings
- ✅ Response models for validation
- ✅ Dependency injection for database

---

### Step 6: Register Router in Main App

**File: `app/main.py`**

```python
# filepath: app/main.py
"""
Main FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.api.v1.endpoints import agents, patients, visits, prescriptions

# Create FastAPI app
app = FastAPI(
    title="Medical Assistant API",
    description="AI-powered medical assistant for doctors",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    agents.router,
    prefix="/api/v1/agents",
    tags=["AI Agents"]
)

app.include_router(
    patients.router,
    prefix="/api/v1/patients",
    tags=["Patients"]
)

app.include_router(
    visits.router,
    prefix="/api/v1/visits",
    tags=["Visits"]
)

# 👇 NEW: Register prescriptions router
app.include_router(
    prescriptions.router,
    prefix="/api/v1/prescriptions",
    tags=["Prescriptions"]
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "medical-assistant-api",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Medical Assistant API",
        "docs": "/docs",
        "health": "/health"
    }
```

---

### Step 7: Write Tests

**File: `tests/test_prescriptions.py`**

```python
# filepath: tests/test_prescriptions.py
"""
Tests for prescription endpoints.
"""
import pytest
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"


class TestPrescriptionsAPI:
    """Test suite for prescriptions API."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data."""
        self.test_prescription = {
            "prescription_id": "RX000001",
            "patient_id": "PAT001",
            "medication_name": "Metformin",
            "dosage": "500mg",
            "frequency": "Twice daily",
            "duration_days": 30,
            "quantity": 60,
            "refills": 3,
            "instructions": "Take with food",
            "prescribing_doctor": "Dr. Smith"
        }

    def test_01_create_prescription(self):
        """Test creating a new prescription."""
        response = requests.post(
            f"{API_BASE}/prescriptions/",
            json=self.test_prescription
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["prescription_id"] == "RX000001"
        assert data["medication_name"] == "Metformin"
        assert data["is_active"] == True
        print(f"\n✅ Created prescription: {data['prescription_id']}")

    def test_02_get_prescription(self):
        """Test retrieving a prescription by ID."""
        response = requests.get(
            f"{API_BASE}/prescriptions/RX000001"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["medication_name"] == "Metformin"
        assert data["dosage"] == "500mg"
        print(f"\n✅ Retrieved prescription: {data['prescription_id']}")

    def test_03_list_prescriptions(self):
        """Test listing prescriptions."""
        response = requests.get(
            f"{API_BASE}/prescriptions/",
            params={"limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"\n✅ Listed {len(data)} prescriptions")

    def test_04_filter_by_patient(self):
        """Test filtering prescriptions by patient."""
        response = requests.get(
            f"{API_BASE}/prescriptions/",
            params={"patient_id": "PAT001"}
        )

        assert response.status_code == 200
        data = response.json()
        assert all(p["patient_id"] == "PAT001" for p in data)
        print(f"\n✅ Filtered {len(data)} prescriptions for PAT001")

    def test_05_update_prescription(self):
        """Test updating a prescription."""
        update_data = {
            "dosage": "1000mg",
            "instructions": "Take with food in the morning"
        }

        response = requests.put(
            f"{API_BASE}/prescriptions/RX000001",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["dosage"] == "1000mg"
        assert "morning" in data["instructions"]
        print(f"\n✅ Updated prescription dosage")

    def test_06_deactivate_prescription(self):
        """Test deactivating a prescription."""
        response = requests.post(
            f"{API_BASE}/prescriptions/RX000001/deactivate"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False
        assert data["end_date"] is not None
        print(f"\n✅ Deactivated prescription")

    def test_07_get_patient_active_prescriptions(self):
        """Test getting active prescriptions for a patient."""
        # Create a new active prescription
        new_prescription = {
            "prescription_id": "RX000002",
            "patient_id": "PAT001",
            "medication_name": "Lisinopril",
            "dosage": "10mg",
            "frequency": "Once daily",
            "duration_days": 90,
            "quantity": 90,
            "refills": 3
        }
        requests.post(f"{API_BASE}/prescriptions/", json=new_prescription)

        # Get active prescriptions
        response = requests.get(
            f"{API_BASE}/prescriptions/patient/PAT001/active"
        )

        assert response.status_code == 200
        data = response.json()
        assert all(p["is_active"] for p in data)
        print(f"\n✅ Found {len(data)} active prescriptions")

    def test_08_validation_errors(self):
        """Test validation errors."""
        # Invalid prescription_id format
        invalid_prescription = {
            **self.test_prescription,
            "prescription_id": "INVALID123"
        }

        response = requests.post(
            f"{API_BASE}/prescriptions/",
            json=invalid_prescription
        )

        assert response.status_code == 422  # Validation error
        print(f"\n✅ Validation correctly rejected invalid data")

    def test_09_delete_prescription(self):
        """Test deleting a prescription."""
        response = requests.delete(
            f"{API_BASE}/prescriptions/RX000002"
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = requests.get(
            f"{API_BASE}/prescriptions/RX000002"
        )
        assert get_response.status_code == 404
        print(f"\n✅ Successfully deleted prescription")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

**Run Tests:**

```bash
# Start your FastAPI server first
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

# In another terminal, run tests
pytest tests/test_prescriptions.py -v

# Or run specific test
pytest tests/test_prescriptions.py::TestPrescriptionsAPI::test_01_create_prescription -v -s
```

---

## Example: Complete Feature in Action

Let's see how everything works together:

### 1. Start Server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### 2. Visit API Documentation

Open browser: `http://localhost:8001/docs`

You'll see your new `/api/v1/prescriptions/` endpoints with:

- Interactive "Try it out" buttons
- Request/response schemas
- Example values
- HTTP status codes

### 3. Create a Prescription

```bash
curl -X POST "http://localhost:8001/api/v1/prescriptions/" \
  -H "Content-Type: application/json" \
  -d '{
    "prescription_id": "RX000001",
    "patient_id": "PAT001",
    "medication_name": "Metformin",
    "dosage": "500mg",
    "frequency": "Twice daily with meals",
    "duration_days": 30,
    "quantity": 60,
    "refills": 3,
    "instructions": "Take with food. Monitor blood sugar levels.",
    "prescribing_doctor": "Dr. Sarah Johnson"
  }'
```

**Response:**

```json
{
  "id": 1,
  "prescription_id": "RX000001",
  "patient_id": "PAT001",
  "visit_id": null,
  "medication_name": "Metformin",
  "dosage": "500mg",
  "frequency": "Twice daily with meals",
  "duration_days": 30,
  "quantity": 60,
  "refills": 3,
  "instructions": "Take with food. Monitor blood sugar levels.",
  "prescribing_doctor": "Dr. Sarah Johnson",
  "is_active": true,
  "start_date": "2025-11-08T16:00:00Z",
  "end_date": null,
  "created_at": "2025-11-08T16:00:00Z",
  "updated_at": "2025-11-08T16:00:00Z"
}
```

### 4. List Prescriptions

```bash
curl "http://localhost:8001/api/v1/prescriptions/?patient_id=PAT001&is_active=true"
```

### 5. Update Prescription

```bash
curl -X PUT "http://localhost:8001/api/v1/prescriptions/RX000001" \
  -H "Content-Type: application/json" \
  -d '{
    "dosage": "1000mg",
    "refills": 5
  }'
```

---

## Best Practices

### 1. Follow RESTful Conventions

```python
# Good: RESTful URL structure
GET    /api/v1/prescriptions/              # List all
POST   /api/v1/prescriptions/              # Create new
GET    /api/v1/prescriptions/{id}          # Get one
PUT    /api/v1/prescriptions/{id}          # Update
DELETE /api/v1/prescriptions/{id}          # Delete

# Bad: Non-RESTful
GET    /api/v1/get-prescriptions
POST   /api/v1/create-prescription
POST   /api/v1/update-prescription/{id}
```

### 2. Use Proper HTTP Status Codes

```python
# 200 OK - Successful GET, PUT
# 201 Created - Successful POST
# 204 No Content - Successful DELETE
# 400 Bad Request - Validation error
# 404 Not Found - Resource doesn't exist
# 500 Internal Server Error - Server error

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_resource(...):
    pass

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(...):
    pass
```

### 3. Add Comprehensive Documentation

```python
@router.get(
    "/{id}",
    response_model=PrescriptionResponse,
    summary="Get prescription by ID",  # 👈 Shows in OpenAPI
    description="Retrieve detailed information...",  # 👈 More details
    responses={
        200: {"description": "Prescription found"},
        404: {"description": "Prescription not found"}
    }
)
async def get_prescription(...):
    """
    Detailed docstring explaining:
    - What the endpoint does
    - Parameters
    - Return values
    - Possible errors
    """
    pass
```

### 4. Use Dependency Injection

```python
# Good: Dependencies injected
async def create_prescription(
    data: PrescriptionCreate,
    db: AsyncSession = Depends(get_db),  # 👈 Injected
    current_user: User = Depends(get_current_user)  # 👈 Can add auth
):
    service = PrescriptionService(db)
    return await service.create_prescription(data)

# Bad: Global variables
db_session = create_session()  # Global state

async def create_prescription(data: PrescriptionCreate):
    service = PrescriptionService(db_session)  # Hard to test
```

### 5. Validate Input Data

```python
class PrescriptionCreate(BaseModel):
    prescription_id: str = Field(..., regex=r'^RX\d{6}$')  # 👈 Format validation
    dosage: str = Field(..., min_length=1, max_length=100)  # 👈 Length validation
    refills: int = Field(0, ge=0, le=12)  # 👈 Range validation

    @validator('end_date')
    def validate_end_date(cls, v, values):  # 👈 Custom validation
        if v and v < values.get('start_date'):
            raise ValueError("end_date must be after start_date")
        return v
```

### 6. Handle Errors Gracefully

```python
async def get_prescription(prescription_id: str, db: AsyncSession):
    service = PrescriptionService(db)
    prescription = await service.get_prescription_by_id(prescription_id)

    if not prescription:
        raise HTTPException(  # 👈 Proper error response
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription {prescription_id} not found"
        )

    return prescription
```

### 7. Add Logging

```python
import logging

logger = logging.getLogger(__name__)

async def create_prescription(data: PrescriptionCreate):
    logger.info(f"Creating prescription {data.prescription_id}")  # 👈 Log actions

    try:
        result = await service.create_prescription(data)
        logger.info(f"Successfully created {data.prescription_id}")
        return result
    except Exception as e:
        logger.error(f"Error creating prescription: {e}")  # 👈 Log errors
        raise
```

### 8. Use Type Hints

```python
# Good: Type hints everywhere
async def get_prescription(
    prescription_id: str,  # 👈 Type hint
    db: AsyncSession  # 👈 Type hint
) -> Optional[PrescriptionResponse]:  # 👈 Return type hint
    pass

# Bad: No type hints
async def get_prescription(prescription_id, db):
    pass
```

---

## Common Patterns

### Pattern 1: Pagination

```python
@router.get("/")
async def list_resources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List with pagination."""
    query = select(Resource).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
```

### Pattern 2: Filtering

```python
@router.get("/")
async def list_resources(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List with filters."""
    query = select(Resource)

    if status:
        query = query.where(Resource.status == status)
    if category:
        query = query.where(Resource.category == category)

    result = await db.execute(query)
    return result.scalars().all()
```

### Pattern 3: Search

```python
@router.get("/search")
async def search_resources(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db)
):
    """Search resources."""
    query = select(Resource).where(
        or_(
            Resource.name.ilike(f"%{q}%"),
            Resource.description.ilike(f"%{q}%")
        )
    )
    result = await db.execute(query)
    return result.scalars().all()
```

### Pattern 4: Nested Resources

```python
@router.get("/patients/{patient_id}/prescriptions")
async def get_patient_prescriptions(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get prescriptions for a specific patient."""
    query = select(Prescription).where(
        Prescription.patient_id == patient_id
    )
    result = await db.execute(query)
    return result.scalars().all()
```

### Pattern 5: Bulk Operations

```python
@router.post("/bulk")
async def bulk_create(
    items: List[PrescriptionCreate],
    db: AsyncSession = Depends(get_db)
):
    """Create multiple prescriptions at once."""
    service = PrescriptionService(db)
    results = []

    for item in items:
        result = await service.create_prescription(item)
        results.append(result)

    return results
```

---

## Troubleshooting

### Issue 1: Import Errors

```bash
# Error: ModuleNotFoundError: No module named 'app.models.prescription'

# Solution: Check imports in __init__.py
# app/models/__init__.py
from .prescription import Prescription, PrescriptionCreate, PrescriptionResponse

# Or import directly
from app.models.prescription import Prescription
```

### Issue 2: Pydantic Validation Errors

```bash
# Error: validation error for PrescriptionCreate

# Solution: Check your request data matches schema
# Make sure required fields are present
# Check field types match (str, int, etc.)
```

### Issue 3: Database Errors

```bash
# Error: relation "prescriptions" does not exist

# Solution: Run migrations
alembic upgrade head
```

### Issue 4: Router Not Found

```bash
# Error: 404 Not Found on /api/v1/prescriptions/

# Solution: Check router is registered in main.py
app.include_router(
    prescriptions.router,
    prefix="/api/v1/prescriptions",
    tags=["Prescriptions"]
)
```

### Issue 5: Type Errors

```python
# Error: Expected AsyncSession but got None

# Solution: Make sure you're using async def and await
async def my_endpoint(db: AsyncSession = Depends(get_db)):
    result = await db.execute(query)  # 👈 Don't forget await
```

---

## Summary

### Checklist for Adding New Endpoint

- [ ] 1. Create database model (SQLAlchemy)
- [ ] 2. Create Pydantic schemas (validation)
- [ ] 3. Generate and apply migration
- [ ] 4. Build service layer (business logic)
- [ ] 5. Create API endpoints (FastAPI)
- [ ] 6. Register router in main app
- [ ] 7. Write tests
- [ ] 8. Document API (docstrings)
- [ ] 9. Test manually with `/docs`
- [ ] 10. Commit changes

### Key Files Created

```
app/
├── models/
│   └── prescription.py          # Database model + Pydantic schemas
├── services/
│   └── prescription_service.py  # Business logic
├── api/v1/endpoints/
│   └── prescriptions.py         # API endpoints
└── main.py                      # Register router

alembic/versions/
└── YYYYMMDD_HHMM_*_create_prescriptions_table.py  # Migration

tests/
└── test_prescriptions.py        # Tests
```

### Time Estimates

- Database model: 10 minutes
- Pydantic schemas: 10 minutes
- Migration: 2 minutes
- Service layer: 15 minutes
- API endpoints: 15 minutes
- Tests: 15 minutes
- **Total: ~45 minutes**

---

## Next Steps

Now that you know how to add endpoints, you can:

1. **Add more features**: appointments, lab orders, referrals
2. **Add authentication**: protect endpoints with JWT tokens
3. **Add authorization**: role-based access control
4. **Add caching**: Redis for frequently accessed data
5. **Add background tasks**: Celery for async operations
6. **Add real-time updates**: WebSockets for live notifications

---

_This guide provides a complete blueprint for adding new endpoints to your Medical Assistant project. Follow this pattern for consistency and maintainability!_
