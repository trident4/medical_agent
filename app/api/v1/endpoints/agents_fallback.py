"""
AI agents endpoints with fallback system.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
import structlog

from app.agents.qa_agent_fallback import medical_qa_agent, QAContext
from app.agents.summarizer_fallback import visit_summarizer
from app.database.session import get_db
from app.models.patient import PatientResponse
from app.models.visit import VisitResponse
from app.api.v1.endpoints.patients import get_patient
from app.api.v1.endpoints.visits import get_visit
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter()

# Request/Response models


class QuestionRequest(BaseModel):
    """Request model for asking questions."""
    question: str
    patient_id: Optional[int] = None
    visit_id: Optional[int] = None
    include_patient_history: bool = False


class QuestionResponse(BaseModel):
    """Response model for questions."""
    answer: str
    context_used: str
    available_providers: List[str]
    provider_status: dict


class SummaryRequest(BaseModel):
    """Request model for visit summarization."""
    visit_id: int
    include_patient_context: bool = True


class SummaryResponse(BaseModel):
    """Response model for visit summary."""
    summary: str
    visit_id: int
    patient_id: int
    available_providers: List[str]


class PatientHistoryRequest(BaseModel):
    """Request model for patient history summary."""
    patient_id: int
    max_visits: Optional[int] = 10


class AgentStatusResponse(BaseModel):
    """Response model for agent status."""
    qa_agent: dict
    summarizer_agent: dict
    fallback_enabled: bool
    total_providers: int


@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status():
    """Get the status of all AI agents and providers."""
    try:
        qa_status = medical_qa_agent.get_fallback_info()
        summarizer_status = visit_summarizer.get_fallback_info()

        return AgentStatusResponse(
            qa_agent=qa_status,
            summarizer_agent=summarizer_status,
            fallback_enabled=True,
            total_providers=max(
                len(qa_status["available_providers"]),
                len(summarizer_status["available_providers"])
            )
        )
    except Exception as e:
        logger.error("Failed to get agent status", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent status: {str(e)}")


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ask a question about patient data.

    The system will try multiple AI providers in this order:
    1. X.AI (Grok-3) - Primary
    2. OpenAI (GPT-4o) - Fallback
    3. Anthropic (Claude) - Final fallback
    """
    try:
        context = QAContext()
        context_description = "General medical knowledge"

        # Build context based on request
        if request.patient_id:
            # Get patient information
            patient = await get_patient(request.patient_id, db)
            context.specific_patient = patient
            context_description = f"Patient {patient.first_name} {patient.last_name}"

            if request.include_patient_history:
                # Get patient's recent visits
                from app.services.visit_service import VisitService
                visit_service = VisitService(db)
                visits = await visit_service.get_patient_visits_by_db_id(patient.id)
                context.visits = visits
                context_description += f" with {len(visits)} recent visits"

        if request.visit_id:
            # Get specific visit
            visit = await get_visit(request.visit_id, db)
            context.specific_visit = visit

            # Get patient for this visit if not already loaded
            if not context.specific_patient:
                patient = await get_patient(visit.patient_id, db)
                context.specific_patient = patient

            context_description = f"Visit {visit.id} for patient {context.specific_patient.first_name}"

        # Ask the question
        logger.info(f"Processing question with context: {context_description}")
        answer = await medical_qa_agent.answer_question(request.question, context)

        # Get agent status
        agent_status = medical_qa_agent.get_agent_status()

        return QuestionResponse(
            answer=answer,
            context_used=context_description,
            available_providers=agent_status["available_providers"],
            provider_status=agent_status["provider_status"]
        )

    except Exception as e:
        logger.error("Question answering failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Question answering failed: {str(e)}")


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_visit(
    request: SummaryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Summarize a patient visit.

    The system will try multiple AI providers in this order:
    1. X.AI (Grok-3) - Primary
    2. OpenAI (GPT-4o) - Fallback  
    3. Anthropic (Claude) - Final fallback
    """
    try:
        # Get visit information
        visit = await get_visit(request.visit_id, db)

        # Get patient information if requested
        patient = None
        if request.include_patient_context:
            patient = await get_patient(visit.patient_id, db)

        # Generate summary
        logger.info(f"Summarizing visit {visit.id}")
        summary = await visit_summarizer.summarize_visit(visit, patient)

        # Get agent status
        agent_status = visit_summarizer.get_agent_status()

        return SummaryResponse(
            summary=summary,
            visit_id=visit.id,
            patient_id=visit.patient_id,
            available_providers=agent_status["available_providers"]
        )

    except Exception as e:
        logger.error("Visit summarization failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Visit summarization failed: {str(e)}")


@router.post("/patient-history", response_model=SummaryResponse)
async def summarize_patient_history(
    request: PatientHistoryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Summarize a patient's medical history.

    The system will try multiple AI providers in fallback order.
    """
    try:
        # Get patient information
        patient = await get_patient(request.patient_id, db)

        # Get patient's visits
        from app.services.visit_service import VisitService
        visit_service = VisitService(db)
        visits = await visit_service.get_patient_visits_by_db_id(patient.id)

        if not visits:
            raise HTTPException(
                status_code=404, detail="No visits found for this patient")

        # Limit visits if requested
        if request.max_visits:
            visits = visits[:request.max_visits]

        # Generate patient history summary
        logger.info(
            f"Summarizing history for patient {patient.id} ({len(visits)} visits)")
        summary = await visit_summarizer.summarize_patient_history(patient, visits, request.max_visits)

        # Get agent status
        agent_status = visit_summarizer.get_agent_status()

        return SummaryResponse(
            summary=summary,
            visit_id=0,  # Not applicable for patient history
            patient_id=patient.id,
            available_providers=agent_status["available_providers"]
        )

    except Exception as e:
        logger.error("Patient history summarization failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Patient history summarization failed: {str(e)}")


@router.post("/discharge-summary")
async def create_discharge_summary(
    request: SummaryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a discharge summary for a visit."""
    try:
        # Get visit and patient information
        visit = await get_visit(request.visit_id, db)
        patient = await get_patient(visit.patient_id, db)

        # Generate discharge summary
        logger.info(f"Creating discharge summary for visit {visit.id}")
        summary = await visit_summarizer.create_discharge_summary(visit, patient)

        return {
            "discharge_summary": summary,
            "visit_id": visit.id,
            "patient_id": patient.id,
            "generated_at": visit.visit_date
        }

    except Exception as e:
        logger.error("Discharge summary creation failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Discharge summary creation failed: {str(e)}")


@router.get("/patient/{patient_id}/trends")
async def analyze_patient_trends(
    patient_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Analyze trends for a specific patient."""
    try:
        # Get patient information
        patient = await get_patient(patient_id, db)

        # Get patient's visits
        from app.services.visit_service import VisitService
        visit_service = VisitService(db)
        visits = await visit_service.get_patient_visits_by_db_id(patient_id)

        if not visits:
            raise HTTPException(
                status_code=404, detail="No visits found for this patient")

        # Analyze trends
        logger.info(
            f"Analyzing trends for patient {patient_id} ({len(visits)} visits)")
        analysis = await medical_qa_agent.analyze_patient_trends(patient_id, visits)

        return {
            "patient_id": patient_id,
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "total_visits": len(visits),
            "trend_analysis": analysis,
            "date_range": {
                "earliest": min(visit.visit_date for visit in visits),
                "latest": max(visit.visit_date for visit in visits)
            }
        }

    except Exception as e:
        logger.error("Patient trend analysis failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Patient trend analysis failed: {str(e)}")


@router.get("/test")
async def test_ai_providers():
    """Test all available AI providers."""
    try:
        test_question = "What is a normal blood pressure reading?"

        # Test QA agent
        qa_status = medical_qa_agent.get_agent_status()
        answer = await medical_qa_agent.answer_question(test_question)

        # Test summarizer
        summarizer_status = visit_summarizer.get_agent_status()

        return {
            "test_question": test_question,
            "test_answer": answer[:200] + "..." if len(answer) > 200 else answer,
            "qa_agent_status": qa_status,
            "summarizer_status": summarizer_status,
            "all_providers_tested": True
        }

    except Exception as e:
        logger.error("AI provider test failed", error=str(e))
        return {
            "test_question": "What is a normal blood pressure reading?",
            "test_answer": "Test failed - see error",
            "error": str(e),
            "qa_agent_status": medical_qa_agent.get_agent_status(),
            "summarizer_status": visit_summarizer.get_agent_status(),
            "all_providers_tested": False
        }
