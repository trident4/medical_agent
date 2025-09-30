"""
Question-answering agent for patient data with fallback system.
"""

import logging
from typing import Optional, List, Dict, Any
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
        - Indicate confidence level in your answers
        - Suggest follow-up questions or actions when appropriate
        - Never make diagnoses or treatment recommendations beyond what's documented
        
        Format your response with:
        - Clear, concise answer
        - Specific sources cited (patient ID, visit date, etc.)
        - Confidence score (0.0-1.0)
        - Context summary
        """

        self.agent = FallbackAgent(system_prompt)
        logger.info("Medical QA Agent initialized with fallback system")

    async def answer_question(
        self,
        question: str,
        context: Optional[QAContext] = None
    ) -> str:
        """
        Answer a question about patient data.

        Args:
            question: The medical question to answer
            context: Optional patient/visit context

        Returns:
            AI-generated answer with provider info
        """
        try:
            # Prepare the input with context
            context_text = ""
            if context:
                if context.patients:
                    context_text += "Available Patients:\n"
                    for patient in context.patients:
                        context_text += f"- {patient.first_name} {patient.last_name} (ID: {patient.id})\n"
                        context_text += f"  DOB: {patient.date_of_birth}, Gender: {patient.gender}\n"
                        if patient.medical_history:
                            context_text += f"  Medical History: {patient.medical_history}\n"
                        context_text += "\n"

                if context.visits:
                    context_text += "Recent Visits:\n"
                    for visit in context.visits:
                        context_text += f"- Visit {visit.id} (Patient {visit.patient_id})\n"
                        context_text += f"  Date: {visit.visit_date}\n"
                        context_text += f"  Type: {visit.visit_type}\n"
                        context_text += f"  Chief Complaint: {visit.chief_complaint}\n"
                        context_text += f"  Diagnosis: {visit.diagnosis}\n"
                        if visit.treatment_plan:
                            context_text += f"  Treatment: {visit.treatment_plan}\n"
                        if visit.notes:
                            context_text += f"  Notes: {visit.notes}\n"
                        context_text += "\n"

                if context.specific_patient:
                    context_text += f"Focus Patient: {context.specific_patient.first_name} {context.specific_patient.last_name}\n"
                    context_text += f"Patient Details: ID {context.specific_patient.id}, "
                    context_text += f"DOB: {context.specific_patient.date_of_birth}, "
                    context_text += f"Gender: {context.specific_patient.gender}\n"
                    if context.specific_patient.medical_history:
                        context_text += f"Medical History: {context.specific_patient.medical_history}\n"
                    context_text += "\n"

                if context.specific_visit:
                    visit = context.specific_visit
                    context_text += f"Focus Visit: {visit.id} on {visit.visit_date}\n"
                    context_text += f"Visit Details: Type: {visit.visit_type}, "
                    context_text += f"Chief Complaint: {visit.chief_complaint}\n"
                    context_text += f"Diagnosis: {visit.diagnosis}\n"
                    if visit.treatment_plan:
                        context_text += f"Treatment Plan: {visit.treatment_plan}\n"
                    if visit.notes:
                        context_text += f"Notes: {visit.notes}\n"
                    context_text += "\n"

            full_input = f"""
            Medical Context:
            {context_text}
            
            Question: {question}
            
            Please provide a comprehensive medical answer based on the context above.
            Be specific about which patient/visit information you're referencing.
            """

            # Get available providers for logging
            available_providers = self.agent.get_available_providers()
            logger.info(f"Available AI providers: {available_providers}")

            # Run the query with fallback
            response = await self.agent.run_async(full_input.strip() if not context_text else full_input)

            logger.info("✅ Medical QA completed successfully")
            return response

        except Exception as e:
            logger.error(f"❌ Medical QA failed: {e}")
            raise Exception(f"Medical QA failed: {str(e)}")

    async def analyze_patient_trends(
        self,
        patient_id: int,
        visits: List[VisitResponse]
    ) -> str:
        """Analyze trends for a specific patient."""
        context_text = f"Patient Trend Analysis for Patient ID: {patient_id}\n\n"
        context_text += "Visit History (chronological):\n"

        # Sort visits by date
        sorted_visits = sorted(visits, key=lambda v: v.visit_date)

        for i, visit in enumerate(sorted_visits, 1):
            context_text += f"{i}. Visit on {visit.visit_date}:\n"
            context_text += f"   Type: {visit.visit_type}\n"
            context_text += f"   Chief Complaint: {visit.chief_complaint}\n"
            context_text += f"   Diagnosis: {visit.diagnosis}\n"
            if visit.treatment_plan:
                context_text += f"   Treatment: {visit.treatment_plan}\n"
            if visit.notes:
                context_text += f"   Notes: {visit.notes}\n"
            context_text += "\n"

        analysis_prompt = f"""
        {context_text}
        
        Please analyze this patient's medical trends:
        1. What patterns do you see in their visits?
        2. Are there recurring issues or improvements?
        3. How effective do the treatments appear to be?
        4. What should healthcare providers watch for in future visits?
        5. Are there any red flags or concerning trends?
        
        Provide a comprehensive analysis with specific references to the visit data.
        """

        try:
            response = await self.agent.run_async(analysis_prompt)
            logger.info("✅ Patient trend analysis completed")
            return response
        except Exception as e:
            logger.error(f"❌ Patient trend analysis failed: {e}")
            raise Exception(f"Patient trend analysis failed: {str(e)}")

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
