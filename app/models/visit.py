"""
Visit data models.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from app.database.base import Base


# SQLAlchemy Models
class Visit(Base):
    """Visit database model."""

    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(String(50), unique=True, index=True, nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    visit_date = Column(DateTime, nullable=False)
    # routine, emergency, follow-up, etc.
    visit_type = Column(String(50), nullable=False)
    chief_complaint = Column(Text)
    symptoms = Column(Text)
    diagnosis = Column(Text)
    treatment_plan = Column(Text)
    medications_prescribed = Column(Text)
    follow_up_instructions = Column(Text)
    doctor_notes = Column(Text)
    vital_signs = Column(Text)  # JSON string for vital signs
    lab_results = Column(Text)  # JSON string for lab results
    duration_minutes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="visits")


# Pydantic Models (API Schemas)
class VitalSigns(BaseModel):
    """Vital signs schema."""

    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None


class LabResult(BaseModel):
    """Lab result schema."""

    test_name: str
    value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    status: Optional[str] = None  # normal, abnormal, critical


class VisitBase(BaseModel):
    """Base visit schema."""

    # visit_id: str = Field(..., description="Unique visit identifier")
    patient_id: int = Field(..., description="Patient ID")
    visit_date: datetime
    visit_type: str = Field(..., description="Type of visit")
    chief_complaint: Optional[str] = None
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    medications_prescribed: Optional[str] = None
    follow_up_instructions: Optional[str] = None
    doctor_notes: Optional[str] = None
    vital_signs: Optional[VitalSigns] = None
    lab_results: Optional[List[LabResult]] = None
    duration_minutes: Optional[int] = None


class VisitCreate(VisitBase):
    """Schema for creating a visit."""
    pass


class VisitUpdate(BaseModel):
    """Schema for updating a visit."""

    visit_date: Optional[datetime] = None
    visit_type: Optional[str] = None
    chief_complaint: Optional[str] = None
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    medications_prescribed: Optional[str] = None
    follow_up_instructions: Optional[str] = None
    doctor_notes: Optional[str] = None
    vital_signs: Optional[VitalSigns] = None
    lab_results: Optional[List[LabResult]] = None
    duration_minutes: Optional[int] = None


class VisitResponse(VisitBase):
    """Schema for visit response."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VisitSummary(BaseModel):
    """Schema for visit summary."""

    id: int
    visit_id: str
    visit_date: datetime
    visit_type: str
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    duration_minutes: Optional[int] = None

    class Config:
        from_attributes = True
