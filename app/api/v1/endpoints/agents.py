"""
AI agents API endpoints for summarization and Q&A.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.models.schemas import (
    SummarizeVisitRequest,
    SummarizeVisitResponse,
    QuestionAnswerRequest,
    QuestionAnswerResponse,
    HealthSummaryRequest,
    HealthSummaryResponse,
    ErrorResponse
)
from app.services.visit_service import VisitService
from app.services.patient_service import PatientService
from app.agents.summarizer import summarize_visit, summarize_multiple_visits
from app.agents.qa_agent import answer_question, get_patient_insights, compare_visits
from datetime import datetime
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.post("/summarize", response_model=SummarizeVisitResponse)
async def summarize_visit_endpoint(
    request: SummarizeVisitRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate an AI-powered summary of a patient visit.
    """
    try:
        visit_service = VisitService(db)
        patient_service = PatientService(db)

        # Get visit information
        visit = await visit_service.get_visit_by_visit_id(request.visit_id)
        if not visit:
            raise HTTPException(
                status_code=404,
                detail=f"Visit with ID {request.visit_id} not found"
            )

        # Get patient information if requested
        patient = None
        previous_visits = None

        if request.include_patient_history:
            patient = await patient_service.get_patient_by_id(visit.patient_id)
            previous_visits = await patient_service.get_patient_visits(
                patient.patient_id, skip=0, limit=10
            )

        # Generate summary using AI
        summary_result = await summarize_visit(
            visit=visit,
            patient=patient,
            previous_visits=previous_visits,
            summary_type=request.summary_type
        )

        # Log the summarization request
        background_tasks.add_task(
            logger.info,
            "Visit summarized",
            visit_id=request.visit_id,
            summary_type=request.summary_type,
            include_history=request.include_patient_history
        )

        return SummarizeVisitResponse(
            visit_id=request.visit_id,
            summary=summary_result.summary,
            key_points=summary_result.key_points,
            recommendations=summary_result.recommendations,
            follow_up_required=summary_result.follow_up_required,
            confidence_score=summary_result.confidence_score,
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error("Error summarizing visit",
                     visit_id=request.visit_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error generating visit summary: {str(e)}"
        )


@router.post("/ask", response_model=QuestionAnswerResponse)
async def ask_question_endpoint(
    request: QuestionAnswerRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Ask questions about patient data and get AI-powered answers.
    """
    try:
        visit_service = VisitService(db)
        patient_service = PatientService(db)

        patients = []
        visits = []

        # Get relevant data based on context
        if request.patient_id:
            patient = await patient_service.get_patient_by_patient_id(request.patient_id)
            if patient:
                patients = [patient]
                visits = await patient_service.get_patient_visits(request.patient_id)

        if request.visit_id:
            visit = await visit_service.get_visit_by_visit_id(request.visit_id)
            if visit:
                visits = [visit]
                if not patients:
                    patient = await patient_service.get_patient_by_id(visit.patient_id)
                    if patient:
                        patients = [patient]

        if not request.patient_id and not request.visit_id and request.context_type == "all":
            # Get recent data for general questions
            patients = await patient_service.get_patients(skip=0, limit=50)
            visits = await visit_service.get_visits(skip=0, limit=100)

        # Generate answer using AI
        qa_result = await answer_question(
            question=request.question,
            patient_id=request.patient_id,
            visit_id=request.visit_id,
            patients=patients,
            visits=visits
        )

        # Log the Q&A request
        background_tasks.add_task(
            logger.info,
            "Question answered",
            question=request.question,
            patient_id=request.patient_id,
            visit_id=request.visit_id,
            context_type=request.context_type
        )

        return QuestionAnswerResponse(
            question=request.question,
            answer=qa_result.answer,
            sources=qa_result.sources,
            confidence_score=qa_result.confidence_score,
            context_used=qa_result.context_used,
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error("Error answering question",
                     question=request.question, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error generating answer: {str(e)}"
        )


@router.post("/health-summary", response_model=HealthSummaryResponse)
async def get_health_summary_endpoint(
    request: HealthSummaryRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a comprehensive health summary for a patient.
    """
    try:
        patient_service = PatientService(db)

        # Get patient information
        patient = await patient_service.get_patient_by_patient_id(request.patient_id)
        if not patient:
            raise HTTPException(
                status_code=404,
                detail=f"Patient with ID {request.patient_id} not found"
            )

        # Get recent visits
        visits = await patient_service.get_patient_visits(
            request.patient_id,
            skip=0,
            limit=request.include_recent_visits
        )

        # Generate insights using AI
        insights = await get_patient_insights(patient, visits)

        # Parse insights (this would be more sophisticated in a real implementation)
        health_trends = ["Overall health stable",
                         "Regular follow-ups maintained"]
        risk_factors = ["Monitor blood pressure",
                        "Continue medication compliance"]
        recommendations = ["Schedule annual physical",
                           "Update vaccination records"]

        # Log the health summary request
        background_tasks.add_task(
            logger.info,
            "Health summary generated",
            patient_id=request.patient_id,
            visits_included=len(visits)
        )

        return HealthSummaryResponse(
            patient_id=request.patient_id,
            summary=insights,
            health_trends=health_trends,
            risk_factors=risk_factors,
            recommendations=recommendations,
            recent_visits_count=len(visits),
            last_visit_date=visits[0].visit_date if visits else None,
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error("Error generating health summary",
                     patient_id=request.patient_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error generating health summary: {str(e)}"
        )


@router.post("/compare-visits", response_model=dict)
async def compare_visits_endpoint(
    visit_id_1: str,
    visit_id_2: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Compare two visits to identify changes and trends.
    """
    try:
        visit_service = VisitService(db)

        # Get both visits
        visit1 = await visit_service.get_visit_by_visit_id(visit_id_1)
        visit2 = await visit_service.get_visit_by_visit_id(visit_id_2)

        if not visit1:
            raise HTTPException(
                status_code=404,
                detail=f"Visit with ID {visit_id_1} not found"
            )

        if not visit2:
            raise HTTPException(
                status_code=404,
                detail=f"Visit with ID {visit_id_2} not found"
            )

        # Generate comparison using AI
        comparison = await compare_visits(visit1, visit2)

        # Log the comparison request
        background_tasks.add_task(
            logger.info,
            "Visits compared",
            visit_id_1=visit_id_1,
            visit_id_2=visit_id_2
        )

        return {
            "visit_1": visit_id_1,
            "visit_2": visit_id_2,
            "comparison": comparison,
            "generated_at": datetime.utcnow()
        }

    except Exception as e:
        logger.error("Error comparing visits", visit_id_1=visit_id_1,
                     visit_id_2=visit_id_2, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing visits: {str(e)}"
        )
