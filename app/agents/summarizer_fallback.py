"""
Visit summarization agent with fallback system.
"""

import logging
from typing import Optional, List
from app.agents.base_agent import FallbackAgent
from app.models.visit import VisitResponse
from app.models.patient import PatientResponse

logger = logging.getLogger(__name__)


class VisitSummarizerAgent:
    """Agent for summarizing patient visit data with AI provider fallback."""

    def __init__(self):
        """Initialize the visit summarizer agent."""
        system_prompt = """
        You are a medical documentation AI that helps healthcare professionals summarize patient visits.
        
        Your role:
        - Create comprehensive yet concise visit summaries
        - Highlight key medical findings and decisions
        - Organize information in a professional medical format
        - Maintain accuracy and medical terminology
        - Ensure HIPAA compliance and confidentiality
        
        Guidelines:
        - Use standard medical documentation format
        - Include all relevant clinical information
        - Highlight important changes or concerns
        - Be objective and factual
        - Use appropriate medical abbreviations when helpful
        - Structure summaries for easy review by other healthcare providers
        
        Summary Format:
        - Patient Demographics
        - Chief Complaint
        - Assessment & Diagnosis
        - Treatment Plan
        - Follow-up Requirements
        - Clinical Notes & Observations
        """

        self.agent = FallbackAgent(system_prompt)
        logger.info("Visit Summarizer Agent initialized with fallback system")

    async def summarize_visit(
        self,
        visit: VisitResponse,
        patient: Optional[PatientResponse] = None
    ) -> str:
        """
        Summarize a single patient visit.

        Args:
            visit: The visit to summarize
            patient: Optional patient information for context

        Returns:
            AI-generated visit summary
        """
        try:
            # Prepare visit information
            visit_info = f"""
            Visit Information:
            - Visit ID: {visit.id}
            - Date: {visit.visit_date}
            - Type: {visit.visit_type}
            - Chief Complaint: {visit.chief_complaint}
            - Diagnosis: {visit.diagnosis}
            """

            if visit.treatment_plan:
                visit_info += f"- Treatment Plan: {visit.treatment_plan}\n"

            if visit.doctor_notes:
                visit_info += f"- Clinical Notes: {visit.doctor_notes}\n"

            # Add patient context if available
            patient_info = ""
            if patient:
                patient_info = f"""
                Patient Information:
                - Name: {patient.first_name} {patient.last_name}
                - ID: {patient.id}
                - DOB: {patient.date_of_birth}
                - Gender: {patient.gender}
                """
                if patient.medical_history:
                    patient_info += f"- Medical History: {patient.medical_history}\n"
                if patient.emergency_contact:
                    patient_info += f"- Emergency Contact: {patient.emergency_contact}\n"

            full_input = f"""
            {patient_info}
            
            {visit_info}
            
            Please create a comprehensive medical visit summary that would be useful for:
            1. Other healthcare providers reviewing this case
            2. Insurance documentation
            3. Medical record continuity
            4. Follow-up planning
            
            Format the summary professionally and include all relevant clinical details.
            """

            # Get available providers for logging
            available_providers = self.agent.get_available_providers()
            logger.info(
                f"Available AI providers for summarization: {available_providers}")

            # Run the query with fallback
            response = await self.agent.run_async(full_input)

            logger.info("✅ Visit summarization completed successfully")
            return response

        except Exception as e:
            logger.error(f"❌ Visit summarization failed: {e}")
            raise Exception(f"Visit summarization failed: {str(e)}")

    async def summarize_visit_stream(
        self,
        visit: VisitResponse,
        patient: Optional[PatientResponse] = None
    ):
        """
        Stream a visit summary in real-time.

        Args:
            visit: The visit to summarize
            patient: Optional patient information for context

        Yields:
            Text chunks of the AI-generated visit summary
        """
        try:
            # Prepare visit information (same as non-streaming version)
            visit_info = f"""
            Visit Information:
            - Visit ID: {visit.id}
            - Date: {visit.visit_date}
            - Type: {visit.visit_type}
            - Chief Complaint: {visit.chief_complaint}
            - Diagnosis: {visit.diagnosis}
            """

            if visit.treatment_plan:
                visit_info += f"- Treatment Plan: {visit.treatment_plan}\n"

            if visit.doctor_notes:
                visit_info += f"- Clinical Notes: {visit.doctor_notes}\n"

            # Add patient context if available
            patient_info = ""
            if patient:
                patient_info = f"""
                Patient Information:
                - Name: {patient.first_name} {patient.last_name}
                - ID: {patient.id}
                - DOB: {patient.date_of_birth}
                - Gender: {patient.gender}
                """
                if patient.medical_history:
                    patient_info += f"- Medical History: {patient.medical_history}\n"
                if patient.emergency_contact:
                    patient_info += f"- Emergency Contact: {patient.emergency_contact}\n"

            full_input = f"""
            {patient_info}
            
            {visit_info}
            
            Please create a comprehensive medical visit summary that would be useful for:
            1. Other healthcare providers reviewing this case
            2. Insurance documentation
            3. Medical record continuity
            4. Follow-up planning
            
            Format the summary professionally and include all relevant clinical details.
            """

            # Get available providers for logging
            available_providers = self.agent.get_available_providers()
            logger.info(
                f"Available AI providers for streaming summarization: {available_providers}")

            # Stream the response with fallback
            async for chunk in self.agent.run_stream(full_input):
                yield chunk

            logger.info("✅ Visit summarization streaming completed successfully")

        except Exception as e:
            logger.error(f"❌ Visit summarization streaming failed: {e}")
            raise Exception(f"Visit summarization streaming failed: {str(e)}")

    async def summarize_patient_history(
        self,
        patient: PatientResponse,
        visits: List[VisitResponse],
        limit: Optional[int] = None
    ) -> str:
        """
        Summarize a patient's visit history.

        Args:
            patient: Patient information
            visits: List of visits to summarize
            limit: Optional limit on number of visits to include

        Returns:
            AI-generated patient history summary
        """
        try:
            # Sort visits by date (most recent first)
            sorted_visits = sorted(
                visits, key=lambda v: v.visit_date, reverse=True)

            if limit:
                sorted_visits = sorted_visits[:limit]

            # Prepare patient information
            patient_info = f"""
            Patient: {patient.first_name} {patient.last_name} (ID: {patient.id})
            DOB: {patient.date_of_birth}
            Gender: {patient.gender}
            """

            if patient.medical_history:
                patient_info += f"Medical History: {patient.medical_history}\n"

            # Prepare visit history
            visit_history = "Visit History (Most Recent First):\n\n"
            for i, visit in enumerate(sorted_visits, 1):
                visit_history += f"{i}. Visit on {visit.visit_date}:\n"
                visit_history += f"   Type: {visit.visit_type}\n"
                visit_history += f"   Chief Complaint: {visit.chief_complaint}\n"
                visit_history += f"   Diagnosis: {visit.diagnosis}\n"

                if visit.treatment_plan:
                    visit_history += f"   Treatment: {visit.treatment_plan}\n"

                if visit.doctor_notes:
                    visit_history += f"   Notes: {visit.doctor_notes}\n"

                visit_history += "\n"

            full_input = f"""
            {patient_info}
            
            {visit_history}
            
            Please create a comprehensive patient history summary that includes:
            1. Patient overview and demographics
            2. Medical history trends and patterns
            3. Recurring issues or chronic conditions
            4. Treatment effectiveness and outcomes
            5. Current health status and ongoing concerns
            6. Recommendations for future care
            
            This summary should be useful for healthcare providers who need to quickly understand
            this patient's medical journey and current status.
            """

            # Run the query with fallback
            response = await self.agent.run_async(full_input)

            logger.info(
                "✅ Patient history summarization completed successfully")
            return response

        except Exception as e:
            logger.error(f"❌ Patient history summarization failed: {e}")
            raise Exception(f"Patient history summarization failed: {str(e)}")

    async def create_discharge_summary(
        self,
        visit: VisitResponse,
        patient: PatientResponse
    ) -> str:
        """
        Create a discharge summary for a visit.

        Args:
            visit: The visit to create discharge summary for
            patient: Patient information

        Returns:
            AI-generated discharge summary
        """
        try:
            full_input = f"""
            Patient: {patient.first_name} {patient.last_name} (ID: {patient.id})
            DOB: {patient.date_of_birth}, Gender: {patient.gender}
            
            Visit Details:
            - Date: {visit.visit_date}
            - Type: {visit.visit_type}
            - Chief Complaint: {visit.chief_complaint}
            - Diagnosis: {visit.diagnosis}
            - Treatment: {visit.treatment_plan or 'Not specified'}
            - Notes: {visit.doctor_notes or 'No additional notes'}
            
            Please create a formal discharge summary including:
            1. Admission reason and chief complaint
            2. Clinical findings and assessment
            3. Treatments provided
            4. Discharge instructions
            5. Follow-up recommendations
            6. Medications prescribed (if mentioned)
            7. Warning signs to watch for
            
            Format this as a professional medical discharge summary.
            """

            response = await self.agent.run_async(full_input)

            logger.info("✅ Discharge summary created successfully")
            return response

        except Exception as e:
            logger.error(f"❌ Discharge summary creation failed: {e}")
            raise Exception(f"Discharge summary creation failed: {str(e)}")

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
visit_summarizer = VisitSummarizerAgent()
