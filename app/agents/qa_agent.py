"""
Question-answering agent using fallback system with Grok-3 primary.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from app.agents.base_agent import FallbackAgent
from app.models.visit import VisitResponse
from app.models.patient import PatientResponse

logger = logging.getLogger(__name__)


class QAContext(BaseModel):
    """Context for Q&A agent."""
    patients: Optional[List[PatientResponse]] = None
    visits: Optional[List[VisitResponse]] = None
    specific_patient: Optional[PatientResponse] = None
    specific_visit: Optional[VisitResponse] = None


class QAResponse(BaseModel):
    """Structured Q&A response."""
    answer: str
    sources: List[Dict[str, Any]]
    confidence_score: float
    context_used: str
    provider_used: str  # Which AI provider was used


class MedicalQAAgent:
    """Agent for answering questions about patient data with AI provider fallback."""

    def __init__(self):
        """Initialize the medical QA agent."""
        system_prompt = """
        You are a medical assistant AI that helps healthcare professionals find information about patients and their visits.
        
        Your role is to:
        1. Answer questions about patient medical data accurately
        2. Provide relevant medical insights and analysis
        3. Reference specific sources for your answers
        4. Maintain medical confidentiality and HIPAA compliance
        5. Acknowledge limitations and suggest when human expertise is needed
        
        Guidelines:
        - Only use information provided in the context
        - Be precise and evidence-based in your responses
        - Cite specific visits, dates, and findings when relevant
        - Use appropriate medical terminology
        - Indicate confidence level in your answers (0.0-1.0)
        - Suggest follow-up questions or actions when appropriate
        - Never make diagnoses or treatment recommendations beyond what's documented
        - Always maintain patient privacy and confidentiality
        
        Always structure your response with:
        - Clear, direct answer to the question
        - Specific sources and references
        - Confidence assessment
        - Context clarification
        """

        self.agent = FallbackAgent(system_prompt)
        logger.info("Medical QA Agent initialized with fallback system")

    async def answer_question(
        self,
        question: str,
        patient_id: Optional[str] = None,
        visit_id: Optional[str] = None,
        patients: Optional[List[PatientResponse]] = None,
        visits: Optional[List[VisitResponse]] = None
    ) -> str:
        """
        Answer a question about patient data using AI.

        Args:
            question: The question to answer
            patient_id: Optional patient ID for context
            visit_id: Optional visit ID for context
            patients: List of patient data for context
            visits: List of visit data for context

        Returns:
            AI-generated answer string
        """
        # Build context information
        context_parts = [f"Question: {question}"]

        def safe_get_attr(obj, attr_name, default="Unknown"):
            """Safely get attribute from either dict or object."""
            if hasattr(obj, attr_name):
                return getattr(obj, attr_name, default)
            elif isinstance(obj, dict):
                return obj.get(attr_name, default)
            else:
                return default

        if patients:
            context_parts.append("Patient Information:")
            # Limit to 5 patients to avoid token limits
            for patient in patients[:5]:
                first_name = safe_get_attr(patient, 'first_name')
                last_name = safe_get_attr(patient, 'last_name')
                date_of_birth = safe_get_attr(patient, 'date_of_birth')
                medical_history = safe_get_attr(
                    patient, 'medical_history', None)
                allergies = safe_get_attr(patient, 'allergies', None)
                current_medications = safe_get_attr(
                    patient, 'current_medications', None)

                context_parts.append(
                    f"- Patient {first_name} {last_name} (DOB: {date_of_birth})")
                if medical_history:
                    context_parts.append(
                        f"  Medical History: {medical_history}")
                if allergies:
                    context_parts.append(f"  Allergies: {allergies}")
                if current_medications:
                    context_parts.append(
                        f"  Current Medications: {current_medications}")

        if visits:
            context_parts.append("Visit Information:")
            for visit in visits[:10]:  # Limit to 10 visits
                visit_date = safe_get_attr(visit, 'visit_date')
                visit_type = safe_get_attr(visit, 'visit_type')
                chief_complaint = safe_get_attr(
                    visit, 'chief_complaint', 'N/A')
                diagnosis = safe_get_attr(visit, 'diagnosis', 'N/A')
                treatment_plan = safe_get_attr(visit, 'treatment_plan', 'N/A')
                vital_signs = safe_get_attr(visit, 'vital_signs', 'N/A')
                doctor_notes = safe_get_attr(visit, 'doctor_notes', None)

                context_parts.append(f"- Visit {visit_date} ({visit_type})")
                context_parts.append(f"  Chief Complaint: {chief_complaint}")
                context_parts.append(f"  Diagnosis: {diagnosis}")
                context_parts.append(f"  Treatment: {treatment_plan}")
                context_parts.append(f"  Vital Signs: {vital_signs}")
                if doctor_notes:
                    context_parts.append(f"  Notes: {doctor_notes}")

        context_parts.append(
            "\nPlease answer the question based on the provided medical data. Be specific about which information you're referencing and provide appropriate sources.")

        full_prompt = "\n".join(context_parts)

        try:
            # Use the fallback agent (Grok-3 -> OpenAI -> Anthropic)
            response = await self.agent.run_async(full_prompt)
            logger.info(
                f"QA Agent successfully answered question about patient {patient_id}")
            return response
        except Exception as e:
            logger.error(f"Error in QA agent: {e}")
            return f"I apologize, but I encountered an error while processing your question. Please try again or contact support. Error: {str(e)}"

    def get_agent_status(self) -> dict:
        """Get the status of all available AI providers."""
        return {
            "available_providers": self.agent.get_available_providers(),
            "provider_status": self.agent.get_status()
        }

    def get_fallback_info(self) -> dict:
        """Get information about the fallback system."""
        status = self.get_agent_status()
        return {
            "fallback_enabled": True,
            "provider_order": ["xai", "openai", "anthropic"],
            "available_providers": status["available_providers"],
            "provider_status": status["provider_status"],
            "total_available": len(status["available_providers"])
        }


# Global instance
medical_qa_agent = MedicalQAAgent()


# Legacy functions for backward compatibility
async def answer_question(
    question: str,
    patient_id: Optional[str] = None,
    visit_id: Optional[str] = None,
    patients: Optional[List[PatientResponse]] = None,
    visits: Optional[List[VisitResponse]] = None
) -> QAResponse:
    """
    Legacy function for backward compatibility.
    """
    try:
        answer = await medical_qa_agent.answer_question(
            question=question,
            patient_id=patient_id,
            visit_id=visit_id,
            patients=patients,
            visits=visits
        )

        # Create a structured response for backward compatibility
        return QAResponse(
            answer=answer,
            sources=[{"type": "ai_analysis",
                      "content": "Generated using AI fallback system"}],
            confidence_score=0.8,  # Default confidence
            context_used=f"Patients: {len(patients) if patients else 0}, Visits: {len(visits) if visits else 0}",
            provider_used=medical_qa_agent.agent.get_available_providers(
            )[0] if medical_qa_agent.agent.get_available_providers() else "none"
        )
    except Exception as e:
        logger.error(f"Error in legacy answer_question: {e}")
        return QAResponse(
            answer=f"Error: {str(e)}",
            sources=[],
            confidence_score=0.0,
            context_used="error",
            provider_used="none"
        )


async def get_patient_insights(
    patient: PatientResponse,
    visits: List[VisitResponse]
) -> str:
    """
    Get AI insights about a patient's health trends and patterns.
    """
    question = f"Please analyze the health trends and patterns for patient {patient.first_name} {patient.last_name} based on their visit history. Provide insights about their overall health trajectory, any concerning patterns, and recommendations for continued care."

    return await medical_qa_agent.answer_question(
        question=question,
        patient_id=patient.patient_id,
        patients=[patient],
        visits=visits
    )


async def compare_visits(
    visit1: VisitResponse,
    visit2: VisitResponse
) -> str:
    """
    Compare two visits to identify changes and improvements.
    """
    question = f"Please compare these two visits and identify key changes, improvements, or concerning developments between visit {visit1.visit_date} and visit {visit2.visit_date}."

    return await medical_qa_agent.answer_question(
        question=question,
        visits=[visit1, visit2]
    )
