"""
Visit service layer for business logic.
"""

import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from app.models.visit import Visit, VisitCreate, VisitUpdate, VisitResponse, VisitSummary
from app.models.patient import Patient, PatientResponse
from datetime import datetime

logger = logging.getLogger(__name__)


class VisitService:
    """Service class for visit-related operations with HIPAA compliance."""

    def __init__(self, db: AsyncSession):
        """Initialize visit service with database session."""
        self.db = db

    async def get_visits(
        self,
        skip: int = 0,
        limit: int = 100,
        patient_id: Optional[str] = None,
        visit_type: Optional[str] = None
    ) -> List[VisitSummary]:
        """Get a list of visits with optional filtering."""
        logger.info("Retrieving visits - skip: %d, limit: %d, patient_id: %s, visit_type: %s",
                    skip, limit, patient_id, visit_type)

        try:
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

            query = query.order_by(
                Visit.visit_date.desc()).offset(skip).limit(limit)

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

            logger.info("Retrieved %d visits", len(summaries))
            return summaries

        except Exception as e:
            logger.error("Error retrieving visits: %s", str(e))
            raise HTTPException(
                status_code=500,
                detail="Error retrieving visits"
            ) from e

    async def get_visit_by_id(self, visit_db_id: int) -> Optional[VisitResponse]:
        """Get a visit by database ID."""
        logger.info("Retrieving visit by DB ID: %d", visit_db_id)

        try:
            query = select(Visit).where(Visit.id == visit_db_id)
            result = await self.db.execute(query)
            visit = result.scalar_one_or_none()

            if visit:
                logger.info("Visit found: %s", visit.visit_id)
                # Direct conversion with JSONB
                return VisitResponse.model_validate(visit)
            else:
                logger.warning("Visit not found: DB ID %d", visit_db_id)
                return None

        except Exception as e:
            logger.error("Error retrieving visit by ID %d: %s",
                         visit_db_id, str(e))
            raise HTTPException(
                status_code=500,
                detail="Error retrieving visit"
            ) from e

    async def get_visit_by_visit_id(self, visit_id: str) -> Optional[VisitResponse]:
        """Get a visit by visit ID."""
        logger.info("Retrieving visit by visit ID: %s", visit_id)

        try:
            query = select(Visit).where(Visit.visit_id == visit_id)
            result = await self.db.execute(query)
            visit = result.scalar_one_or_none()

            if visit:
                logger.info("Visit found: %s", visit.visit_id)
                # Direct conversion with JSONB
                return VisitResponse.model_validate(visit)
            else:
                logger.warning("Visit not found: visit ID %s", visit_id)
                return None

        except Exception as e:
            logger.error(
                "Error retrieving visit by visit ID %s: %s", visit_id, str(e))
            raise HTTPException(
                status_code=500,
                detail="Error retrieving visit"
            ) from e

    async def create_visit(self, visit: VisitCreate) -> VisitResponse:
        """Create a new visit."""
        logger.info("Creating new visit for patient ID: %d", visit.patient_id)

        try:
            # No manual JSON serialization needed with JSONB
            visit_data = visit.model_dump()
            visit_data.pop('visit_id', None)  # Remove auto-generated field

            db_visit = Visit(**visit_data)
            self.db.add(db_visit)
            await self.db.flush()

            # Generate visit_id
            db_visit.visit_id = f"VIS{db_visit.id:06d}"

            await self.db.commit()
            await self.db.refresh(db_visit)

            logger.info("Visit created successfully: %s", db_visit.visit_id)
            # Direct conversion with JSONB
            return VisitResponse.model_validate(db_visit)

        except Exception as e:
            await self.db.rollback()
            logger.error("Error creating visit: %s", str(e))
            raise HTTPException(
                status_code=500,
                detail="Error creating visit"
            ) from e

    async def update_visit(self, db_id: int, visit_update: VisitUpdate) -> VisitResponse:
        """Update an existing visit."""
        logger.info("Updating visit DB ID: %d", db_id)

        try:
            query = select(Visit).where(Visit.id == db_id)
            result = await self.db.execute(query)
            db_visit = result.scalar_one_or_none()

            if not db_visit:
                logger.warning("Visit not found for update: DB ID %d", db_id)
                raise HTTPException(
                    status_code=404,
                    detail=f"Visit with ID {db_id} not found"
                )

            # Update fields - no manual JSON handling needed with JSONB
            update_data = visit_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(db_visit, field):
                    setattr(db_visit, field, value)

            db_visit.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(db_visit)

            logger.info("Visit updated successfully: %s", db_visit.visit_id)
            # Direct conversion with JSONB
            return VisitResponse.model_validate(db_visit)

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error("Error updating visit DB ID %d: %s", db_id, str(e))
            raise HTTPException(
                status_code=500,
                detail="Error updating visit"
            ) from e

    async def delete_visit(self, db_id: int) -> bool:
        """Delete a visit."""
        logger.info("Deleting visit DB ID: %d", db_id)

        try:
            query = select(Visit).where(Visit.id == db_id)
            result = await self.db.execute(query)
            db_visit = result.scalar_one_or_none()

            if not db_visit:
                logger.warning("Visit not found for deletion: DB ID %d", db_id)
                return False

            await self.db.delete(db_visit)
            await self.db.commit()

            logger.info("Visit deleted successfully: %s", db_visit.visit_id)
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error("Error deleting visit DB ID %d: %s", db_id, str(e))
            raise HTTPException(
                status_code=500,
                detail="Error deleting visit"
            ) from e

    async def get_visit_patient(self, db_id: int) -> Optional[PatientResponse]:
        """Get the patient associated with a visit."""
        logger.info("Retrieving patient for visit DB ID: %d", db_id)

        try:
            query = select(Visit).options(selectinload(
                Visit.patient)).where(Visit.id == db_id)
            result = await self.db.execute(query)
            visit = result.scalar_one_or_none()

            if visit and visit.patient:
                logger.info("Patient found for visit: %s",
                            visit.patient.patient_id)
                return PatientResponse.model_validate(visit.patient)
            else:
                logger.warning("No patient found for visit DB ID: %d", db_id)
                return None

        except Exception as e:
            logger.error(
                "Error retrieving patient for visit DB ID %d: %s", db_id, str(e))
            raise HTTPException(
                status_code=500,
                detail="Error retrieving visit patient"
            ) from e

    async def get_patient_visits_by_db_id(self, patient_db_id: int, skip: int = 0, limit: int = 50) -> List[VisitResponse]:
        """Get all visits for a patient by database ID."""
        logger.info("Retrieving visits for patient DB ID: %d", patient_db_id)

        try:
            query = select(Visit).where(Visit.patient_id == patient_db_id).order_by(
                Visit.visit_date.desc()
            ).offset(skip).limit(limit)

            result = await self.db.execute(query)
            visits = result.scalars().all()

            logger.info("Retrieved %d visits for patient DB ID: %d",
                        len(visits), patient_db_id)
            # Direct conversion with JSONB
            return [VisitResponse.model_validate(visit) for visit in visits]

        except Exception as e:
            logger.error(
                "Error retrieving visits for patient DB ID %d: %s", patient_db_id, str(e))
            raise HTTPException(
                status_code=500,
                detail="Error retrieving patient visits"
            ) from e
