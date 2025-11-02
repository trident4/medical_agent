"""
Patient data models.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Text, Date
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from app.database.base import Base


# SQLAlchemy Models
class Patient(Base):
    """Patient database model."""

    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), unique=True, index=True, nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20))
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    emergency_contact = Column(String(200))
    medical_history = Column(Text)
    allergies = Column(Text)
    current_medications = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    visits = relationship("Visit", back_populates="patient")


# Pydantic Models (API Schemas)
class PatientBase(BaseModel):
    """Base patient schema."""

    # patient_id: str = Field(..., description="Unique patient identifier")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: datetime
    gender: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    emergency_contact: Optional[str] = Field(None, max_length=200)
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None


class PatientCreate(PatientBase):
    """Schema for creating a patient."""
    pass


class PatientUpdate(BaseModel):
    """Schema for updating a patient."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    emergency_contact: Optional[str] = Field(None, max_length=200)
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None


class PatientResponse(PatientBase):
    """Schema for patient response."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PatientSummary(BaseModel):
    """Schema for patient summary."""

    id: int
    patient_id: str
    full_name: str
    age: int
    last_visit: Optional[datetime] = None
    visit_count: int = 0

    class Config:
        from_attributes = True
