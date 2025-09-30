"""
Visit service layer for business logic.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models.visit import Visit, VisitCreate, VisitUpdate, VisitResponse, VisitSummary
from app.models.patient import Patient, PatientResponse
from datetime import datetime
import json


class VisitService:
    """Service class for visit-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_visits(
        self,
        skip: int = 0,
        limit: int = 100,
        patient_id: Optional[str] = None,
        visit_type: Optional[str] = None
    ) -> List[VisitSummary]:
        """Get a list of visits with optional filtering."""
        query = select(Visit)

        # Apply filters
        conditions = []
        if patient_id:
            # Get patient database ID first
            patient_query = select(Patient.id).where(
                Patient.patient_id == patient_id)
            patient_result = await self.db.execute(patient_query)
            patient_db_id = patient_result.scalar_one_or_none()
            if patient_db_id:
                conditions.append(Visit.patient_id == patient_db_id)

        if visit_type:
            conditions.append(Visit.visit_type == visit_type)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(Visit.visit_date.desc()
                               ).offset(skip).limit(limit)

        result = await self.db.execute(query)
        visits = result.scalars().all()

        # Convert to summary format
        summaries = []
        for visit in visits:
            summary = VisitSummary(
                id=visit.id,
                visit_id=visit.visit_id,
                visit_date=visit.visit_date,
                visit_type=visit.visit_type,
                chief_complaint=visit.chief_complaint,
                diagnosis=visit.diagnosis,
                duration_minutes=visit.duration_minutes
            )
            summaries.append(summary)

        return summaries

    async def get_visit_by_id(self, visit_db_id: int) -> Optional[VisitResponse]:
        """Get a visit by database ID."""
        query = select(Visit).where(Visit.id == visit_db_id)
        result = await self.db.execute(query)
        visit = result.scalar_one_or_none()

        if visit:
            return self._convert_to_response(visit)
        return None

    async def get_visit_by_visit_id(self, visit_id: str) -> Optional[VisitResponse]:
        """Get a visit by visit ID."""
        print("The visit id is:", visit_id)
        query = select(Visit).where(Visit.visit_id == visit_id)
        result = await self.db.execute(query)
        visit = result.scalar_one_or_none()
        print("The visit fetched is:", visit)

        if visit:
            return self._convert_to_response(visit)
        return None

    async def create_visit(self, visit: VisitCreate) -> VisitResponse:
        """Create a new visit."""
        # Convert pydantic models to JSON strings for database storage
        visit_data = visit.model_dump()

        if visit_data.get('vital_signs'):
            visit_data['vital_signs'] = json.dumps(visit_data['vital_signs'])

        if visit_data.get('lab_results'):
            visit_data['lab_results'] = json.dumps(visit_data['lab_results'])

        db_visit = Visit(**visit_data)
        self.db.add(db_visit)
        await self.db.commit()
        await self.db.refresh(db_visit)

        return self._convert_to_response(db_visit)

    async def update_visit(self, visit_id: str, visit_update: VisitUpdate) -> VisitResponse:
        """Update an existing visit."""
        query = select(Visit).where(Visit.visit_id == visit_id)
        result = await self.db.execute(query)
        db_visit = result.scalar_one_or_none()

        if not db_visit:
            raise ValueError(f"Visit with ID {visit_id} not found")

        # Update fields
        update_data = visit_update.model_dump(exclude_unset=True)

        # Handle special fields that need JSON serialization
        if 'vital_signs' in update_data and update_data['vital_signs']:
            update_data['vital_signs'] = json.dumps(update_data['vital_signs'])

        if 'lab_results' in update_data and update_data['lab_results']:
            update_data['lab_results'] = json.dumps(update_data['lab_results'])

        for field, value in update_data.items():
            setattr(db_visit, field, value)

        db_visit.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(db_visit)

        return self._convert_to_response(db_visit)

    async def delete_visit(self, visit_id: str) -> bool:
        """Delete a visit."""
        query = select(Visit).where(Visit.visit_id == visit_id)
        result = await self.db.execute(query)
        db_visit = result.scalar_one_or_none()

        if not db_visit:
            return False

        await self.db.delete(db_visit)
        await self.db.commit()

        return True

    async def get_visit_patient(self, visit_id: str) -> Optional[PatientResponse]:
        """Get the patient associated with a visit."""
        query = select(Visit).options(selectinload(Visit.patient)).where(
            Visit.visit_id == visit_id
        )
        result = await self.db.execute(query)
        visit = result.scalar_one_or_none()

        if visit and visit.patient:
            return PatientResponse.model_validate(visit.patient)
        return None

    async def get_patient_visits_by_db_id(self, patient_db_id: int, skip: int = 0, limit: int = 50) -> List[VisitResponse]:
        """Get all visits for a patient by database ID."""
        query = select(Visit).where(Visit.patient_id == patient_db_id).order_by(
            Visit.visit_date.desc()
        ).offset(skip).limit(limit)

        result = await self.db.execute(query)
        visits = result.scalars().all()

        return [self._convert_to_response(visit) for visit in visits]

    def _convert_to_response(self, visit: Visit) -> VisitResponse:
        """Convert database model to response model."""
        visit_dict = {
            "id": visit.id,
            "visit_id": visit.visit_id,
            "patient_id": visit.patient_id,
            "visit_date": visit.visit_date,
            "visit_type": visit.visit_type,
            "chief_complaint": visit.chief_complaint,
            "symptoms": visit.symptoms,
            "diagnosis": visit.diagnosis,
            "treatment_plan": visit.treatment_plan,
            "medications_prescribed": visit.medications_prescribed,
            "follow_up_instructions": visit.follow_up_instructions,
            "doctor_notes": visit.doctor_notes,
            "duration_minutes": visit.duration_minutes,
            "created_at": visit.created_at,
            "updated_at": visit.updated_at,
        }

        # Parse JSON fields
        try:
            if visit.vital_signs:
                visit_dict["vital_signs"] = json.loads(visit.vital_signs)
            else:
                visit_dict["vital_signs"] = None
        except (json.JSONDecodeError, TypeError):
            visit_dict["vital_signs"] = None

        try:
            if visit.lab_results:
                visit_dict["lab_results"] = json.loads(visit.lab_results)
            else:
                visit_dict["lab_results"] = None
        except (json.JSONDecodeError, TypeError):
            visit_dict["lab_results"] = None

        return VisitResponse(**visit_dict)
