"""
Patient service layer for business logic.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from app.models.patient import Patient, PatientCreate, PatientUpdate, PatientResponse, PatientSummary
from app.models.visit import Visit
from datetime import datetime


class PatientService:
    """Service class for patient-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_patients(self, skip: int = 0, limit: int = 100) -> List[PatientSummary]:
        """Get a list of patients with summary information."""
        query = select(Patient).offset(skip).limit(limit)
        result = await self.db.execute(query)
        patients = result.scalars().all()

        # Convert to summary format
        summaries = []
        for patient in patients:
            # Get visit count and last visit
            visit_query = select(func.count(Visit.id), func.max(Visit.visit_date)).where(
                Visit.patient_id == patient.id
            )
            visit_result = await self.db.execute(visit_query)
            visit_count, last_visit = visit_result.first()

            # Calculate age
            age = (datetime.now().date() - patient.date_of_birth).days // 365

            summary = PatientSummary(
                id=patient.id,
                patient_id=patient.patient_id,
                full_name=f"{patient.first_name} {patient.last_name}",
                age=age,
                last_visit=last_visit,
                visit_count=visit_count or 0
            )
            summaries.append(summary)

        return summaries

    async def get_patient_by_id(self, patient_db_id: int) -> Optional[PatientResponse]:
        """Get a patient by database ID."""
        query = select(Patient).where(Patient.id == patient_db_id)
        result = await self.db.execute(query)
        patient = result.scalar_one_or_none()

        if patient:
            return PatientResponse.model_validate(patient)
        return None

    async def get_patient_by_patient_id(self, patient_id: str) -> Optional[PatientResponse]:
        """Get a patient by patient ID."""
        query = select(Patient).where(Patient.patient_id == patient_id)
        result = await self.db.execute(query)
        patient = result.scalar_one_or_none()

        if patient:
            return PatientResponse.model_validate(patient)
        return None

    async def create_patient(self, patient: PatientCreate) -> PatientResponse:
        """Create a new patient."""
        db_patient = Patient(**patient.model_dump())
        self.db.add(db_patient)
        await self.db.commit()
        await self.db.refresh(db_patient)

        return PatientResponse.model_validate(db_patient)

    async def update_patient(self, patient_id: str, patient_update: PatientUpdate) -> PatientResponse:
        """Update an existing patient."""
        query = select(Patient).where(Patient.patient_id == patient_id)
        result = await self.db.execute(query)
        db_patient = result.scalar_one_or_none()

        if not db_patient:
            raise ValueError(f"Patient with ID {patient_id} not found")

        # Update fields
        update_data = patient_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_patient, field, value)

        db_patient.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(db_patient)

        return PatientResponse.model_validate(db_patient)

    async def delete_patient(self, patient_id: str) -> bool:
        """Delete a patient and all associated visits."""
        query = select(Patient).where(Patient.patient_id == patient_id)
        result = await self.db.execute(query)
        db_patient = result.scalar_one_or_none()

        if not db_patient:
            return False

        await self.db.delete(db_patient)
        await self.db.commit()

        return True

    async def search_patients(self, search_term: str, skip: int = 0, limit: int = 100) -> List[PatientSummary]:
        """Search patients by name or patient ID."""
        search_pattern = f"%{search_term}%"

        query = select(Patient).where(
            or_(
                Patient.first_name.ilike(search_pattern),
                Patient.last_name.ilike(search_pattern),
                Patient.patient_id.ilike(search_pattern),
                func.concat(Patient.first_name, ' ',
                            Patient.last_name).ilike(search_pattern)
            )
        ).offset(skip).limit(limit)

        result = await self.db.execute(query)
        patients = result.scalars().all()

        # Convert to summary format (similar to get_patients)
        summaries = []
        for patient in patients:
            visit_query = select(func.count(Visit.id), func.max(Visit.visit_date)).where(
                Visit.patient_id == patient.id
            )
            visit_result = await self.db.execute(visit_query)
            visit_count, last_visit = visit_result.first()

            age = (datetime.now().date() - patient.date_of_birth).days // 365

            summary = PatientSummary(
                id=patient.id,
                patient_id=patient.patient_id,
                full_name=f"{patient.first_name} {patient.last_name}",
                age=age,
                last_visit=last_visit,
                visit_count=visit_count or 0
            )
            summaries.append(summary)

        return summaries

    async def get_patient_visits(self, patient_id: str, skip: int = 0, limit: int = 50) -> List[dict]:
        """Get all visits for a patient."""
        # First get the patient's database ID
        patient_query = select(Patient.id).where(
            Patient.patient_id == patient_id)
        patient_result = await self.db.execute(patient_query)
        patient_db_id = patient_result.scalar_one_or_none()

        if not patient_db_id:
            return []

        # Get visits
        query = select(Visit).where(Visit.patient_id == patient_db_id).order_by(
            Visit.visit_date.desc()
        ).offset(skip).limit(limit)

        result = await self.db.execute(query)
        visits = result.scalars().all()

        return [
            {
                "id": visit.id,
                "visit_id": visit.visit_id,
                "visit_date": visit.visit_date,
                "visit_type": visit.visit_type,
                "chief_complaint": visit.chief_complaint,
                "diagnosis": visit.diagnosis
            }
            for visit in visits
        ]

    async def get_patient_health_summary(self, patient_id: str, recent_visits_count: int = 5) -> dict:
        """Get a comprehensive health summary for a patient."""
        patient = await self.get_patient_by_patient_id(patient_id)
        if not patient:
            raise ValueError(f"Patient with ID {patient_id} not found")

        visits = await self.get_patient_visits(patient_id, limit=recent_visits_count)

        # Calculate age
        age = (datetime.now().date() - patient.date_of_birth).days // 365

        return {
            "patient": {
                "id": patient.patient_id,
                "name": f"{patient.first_name} {patient.last_name}",
                "age": age,
                "gender": patient.gender
            },
            "medical_history": patient.medical_history,
            "allergies": patient.allergies,
            "current_medications": patient.current_medications,
            "recent_visits": visits,
            "total_visits": len(visits),
            "last_visit": visits[0]["visit_date"] if visits else None
        }
