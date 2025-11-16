"""
Patient service layer for business logic.
"""

import logging
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.sql.functions import count, max
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.patient import Patient, PatientCreate, PatientUpdate, PatientResponse, PatientSummary
from app.utils import calculate_age
from app.utils.pagination import PaginatedResponse, Paginator
from app.models.visit import Visit
from datetime import datetime, date

logger = logging.getLogger(__name__)


class PatientService:
    """Service class for patient-related operations with HIPAA compliance."""

    def __init__(self, db: AsyncSession):
        """Initialize patient service with database session."""
        self.db = db

    async def get_patients(
        self,
        skip: int = 0,
        limit: int = 100,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> PaginatedResponse[PatientSummary] | List[PatientSummary]:
        """
        Get a list of patients with summary information.

        Supports both offset-based pagination (skip/limit) and page-based pagination (page/page_size).
        Returns PaginatedResponse if page-based, List if offset-based for backward compatibility.

        HIPAA Compliance: Patient list access logged for audit trail.
        """
        logger.info("Retrieving patients list - skip: %d, limit: %d, page: %s, page_size: %s",
                    skip, limit, page, page_size)

        try:
            # Determine pagination style
            use_pagination = page is not None and page_size is not None

            if use_pagination:
                skip = (page - 1) * page_size
                limit = page_size

            # Get total count - FETCH IMMEDIATELY to avoid ResourceClosedError
            count_query = select(count(Patient.id))
            count_result = await self.db.execute(count_query)
            total = count_result.scalar() or 0  # Fetch immediately!

            # Get patients
            query = select(Patient).offset(skip).limit(limit)
            result = await self.db.execute(query)
            patients = result.scalars().all()

            # Convert to summary format
            summaries = []
            for patient in patients:
                # Get visit count and last visit - FETCH IMMEDIATELY
                visit_query = select(count(Visit.id), max(Visit.visit_date)).where(
                    Visit.patient_id == patient.id
                )
                visit_result = await self.db.execute(visit_query)
                visit_data = visit_result.first()  # Fetch immediately!
                visit_count = visit_data[0] if visit_data else 0
                last_visit = visit_data[1] if visit_data else None

                # Calculate age
                age = calculate_age(patient.date_of_birth)

                summary = PatientSummary(
                    id=patient.id,
                    patient_id=patient.patient_id,
                    full_name=f"{patient.first_name} {patient.last_name}",
                    age=age,
                    last_visit=last_visit,
                    visit_count=visit_count
                )
                summaries.append(summary)

            logger.info("Retrieved %d patients (total: %d)",
                        len(summaries), total)

            # Return paginated response if page-based, otherwise just the list
            if use_pagination:
                return Paginator.create_paginated_response(
                    items=summaries,
                    total=total,
                    page=page,
                    page_size=page_size
                )

            return summaries

        except Exception as e:
            logger.error("Error retrieving patients: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving patients"
            ) from e

    async def get_patient_by_id(self, patient_db_id: int) -> Optional[PatientResponse]:
        """Get a patient by database ID."""
        logger.info("Retrieving patient by database ID: %d", patient_db_id)

        try:
            query = select(Patient).where(Patient.id == patient_db_id)
            result = await self.db.execute(query)
            patient = result.scalar_one_or_none()

            if patient:
                logger.info("Patient found: %d", patient.id)
                return PatientResponse.model_validate(patient)

            logger.warning(
                "Patient not found with database ID: %d", patient_db_id)
            return None

        except Exception as e:
            logger.error("Error retrieving patient by ID %d: %s",
                         patient_db_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving patient"
            ) from e

    async def get_patient_by_patient_id(self, patient_id: str) -> Optional[PatientResponse]:
        """Get a patient by patient ID."""
        logger.info("Retrieving patient by patient ID: %s", patient_id)

        try:
            query = select(Patient).where(Patient.patient_id == patient_id)
            result = await self.db.execute(query)
            patient = result.scalar_one_or_none()

            if patient:
                logger.info("Patient found: %s", patient.patient_id)
                return PatientResponse.model_validate(patient)

            logger.warning("Patient not found with patient ID: %s", patient_id)
            return None

        except Exception as e:
            logger.error(
                "Error retrieving patient by patient ID %s: %s", patient_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving patient"
            ) from e

    async def create_patient(self, patient: PatientCreate) -> PatientResponse:
        """Create a new patient."""
        logger.info("Creating new patient: %s %s",
                    patient.first_name, patient.last_name)

        try:
            db_patient = Patient(**patient.model_dump())
            self.db.add(db_patient)
            await self.db.flush()  # Ensure ID is generated
            db_patient.patient_id = f"PAT{db_patient.id:06d}"
            await self.db.commit()
            await self.db.refresh(db_patient)

            logger.info("Patient created successfully: %s",
                        db_patient.patient_id)
            return PatientResponse.model_validate(db_patient)

        except Exception as e:
            await self.db.rollback()
            logger.error("Error creating patient: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating patient"
            ) from e

    async def update_patient(self, patient_id: int, patient_update: PatientUpdate) -> PatientResponse:
        """Update an existing patient."""
        logger.info("Updating patient: %d", patient_id)

        try:
            query = select(Patient).where(Patient.id == patient_id)
            result = await self.db.execute(query)
            db_patient = result.scalar_one_or_none()

            if not db_patient:
                logger.warning("Patient not found for update: %d", patient_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Patient with ID {patient_id} not found"
                )

            # Update fields
            update_data = patient_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_patient, field, value)

            db_patient.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(db_patient)

            logger.info("Patient updated successfully: %s", patient_id)
            return PatientResponse.model_validate(db_patient)

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error("Error updating patient %s: %s", patient_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating patient"
            ) from e

    async def delete_patient(self, patient_id: int) -> bool:
        """Delete a patient and all associated visits."""
        logger.info("Deleting patient: %d", patient_id)

        try:
            query = select(Patient).where(Patient.id == patient_id)
            result = await self.db.execute(query)
            db_patient = result.scalar_one_or_none()

            if not db_patient:
                logger.warning(
                    "Patient not found for deletion: %s", patient_id)
                return False

            await self.db.delete(db_patient)
            await self.db.commit()

            logger.info("Patient deleted successfully: %s", patient_id)
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error("Error deleting patient %s: %s", patient_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting patient"
            ) from e

    async def search_patients(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> PaginatedResponse[PatientSummary] | List[PatientSummary]:
        """
        Search patients by name or patient ID.

        Supports both offset-based pagination (skip/limit) and page-based pagination (page/page_size).
        Returns PaginatedResponse if page-based, List if offset-based for backward compatibility.

        HIPAA Compliance: Patient searches logged for audit trail.
        """
        logger.info("Searching patients - term: %s, skip: %d, limit: %d, page: %s, page_size: %s",
                    search_term, skip, limit, page, page_size)

        try:
            search_pattern = f"%{search_term}%"

            # Determine pagination style
            use_pagination = page is not None and page_size is not None

            if use_pagination:
                skip = (page - 1) * page_size
                limit = page_size

            # Get total count for search - FETCH IMMEDIATELY
            count_query = select(count(Patient.id)).where(
                or_(
                    Patient.first_name.ilike(search_pattern),
                    Patient.last_name.ilike(search_pattern),
                    Patient.patient_id.ilike(search_pattern),
                    (Patient.first_name + ' ' +
                     Patient.last_name).ilike(search_pattern)
                )
            )
            count_result = await self.db.execute(count_query)
            total = count_result.scalar() or 0  # Fetch immediately!

            # Search query
            query = select(Patient).where(
                or_(
                    Patient.first_name.ilike(search_pattern),
                    Patient.last_name.ilike(search_pattern),
                    Patient.patient_id.ilike(search_pattern),
                    (Patient.first_name + ' ' +
                     Patient.last_name).ilike(search_pattern)
                )
            ).offset(skip).limit(limit)

            result = await self.db.execute(query)
            patients = result.scalars().all()

            # Convert to summary format
            summaries = []
            for patient in patients:
                # Get visit data - FETCH IMMEDIATELY
                visit_query = select(count(Visit.id), max(Visit.visit_date)).where(
                    Visit.patient_id == patient.id
                )
                visit_result = await self.db.execute(visit_query)
                visit_data = visit_result.first()  # Fetch immediately!
                visit_count = visit_data[0] if visit_data else 0
                last_visit = visit_data[1] if visit_data else None

                age = calculate_age(patient.date_of_birth)

                summary = PatientSummary(
                    id=patient.id,
                    patient_id=patient.patient_id,
                    full_name=f"{patient.first_name} {patient.last_name}",
                    age=age,
                    last_visit=last_visit,
                    visit_count=visit_count
                )
                summaries.append(summary)

            logger.info("Search completed - found %d patients (total matching: %d)",
                        len(summaries), total)

            # Return paginated response if page-based, otherwise just the list
            if use_pagination:
                return Paginator.create_paginated_response(
                    items=summaries,
                    total=total,
                    page=page,
                    page_size=page_size
                )

            return summaries

        except Exception as e:
            logger.error("Error searching patients: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error searching patients"
            ) from e

    async def get_patient_visits(self, patient_id: int, skip: int = 0, limit: int = 50) -> List[Dict]:
        """Get all visits for a patient."""
        logger.info("Retrieving visits for patient: %d", patient_id)

        try:
            # First get the patient's database ID - FETCH IMMEDIATELY
            patient_query = select(Patient.id).where(
                Patient.id == patient_id)
            patient_result = await self.db.execute(patient_query)
            patient_db_id = patient_result.scalar_one_or_none()

            if not patient_db_id:
                logger.warning("Patient not found: %d", patient_id)
                return []

            # Get visits
            query = select(Visit).where(Visit.patient_id == patient_db_id).order_by(
                Visit.visit_date.desc()
            ).offset(skip).limit(limit)

            result = await self.db.execute(query)
            visits = result.scalars().all()

            logger.info("Retrieved %d visits for patient %d",
                        len(visits), patient_id)

            return [
                {
                    "id": visit.id,
                    "visit_id": visit.visit_id,
                    "visit_date": visit.visit_date,
                    "visit_type": visit.visit_type,
                    "chief_complaint": visit.chief_complaint,
                    "diagnosis": visit.diagnosis,
                    "duration_minutes": visit.duration_minutes,
                    "vital_signs": visit.vital_signs,
                    "doctor_notes": visit.doctor_notes
                }
                for visit in visits
            ]

        except Exception as e:
            logger.error(
                "Error retrieving visits for patient %s: %s", patient_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving patient visits"
            ) from e

    async def get_patient_health_summary(self, patient_id: int, recent_visits_count: int = 5) -> Dict:
        """Get a comprehensive health summary for a patient."""
        logger.info("Generating health summary for patient: %d", patient_id)

        try:
            patient = await self.get_patient_by_patient_id(patient_id)
            if not patient:
                logger.warning(
                    "Patient not found for health summary: %s", patient_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Patient with ID {patient_id} not found"
                )

            visits = await self.get_patient_visits(patient_id, limit=recent_visits_count)

            # Calculate age
            age = calculate_age(patient.date_of_birth)

            summary = {
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

            logger.info("Health summary generated for patient: %s", patient_id)
            return summary

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Error generating health summary for patient %s: %s", patient_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error generating patient health summary"
            ) from e
