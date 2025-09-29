"""
Visit summarization agent using PydanticAI.
"""

from typing import List, Optional
from datetime import datetime
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from app.models.visit import VisitResponse
from app.models.patient import PatientResponse


class SummaryContext(BaseModel):
    """Context for summarization agent."""
    visit: VisitResponse
    patient: Optional[PatientResponse] = None
    previous_visits: Optional[List[VisitResponse]] = None


class VisitSummary(BaseModel):
    """Structured visit summary."""
    summary: str
    key_points: List[str]
    recommendations: List[str]
    follow_up_required: bool
    confidence_score: float


# Create the summarization agent
summarizer_agent = Agent(
    'openai:gpt-4o',  # or 'anthropic:claude-3-5-sonnet-20241022'
    result_type=VisitSummary,
    system_prompt="""
    You are a medical assistant AI specializing in summarizing patient visit data for healthcare professionals.
    
    Your role is to:
    1. Create concise, accurate summaries of patient visits
    2. Highlight key medical findings and diagnoses
    3. Identify important follow-up actions
    4. Provide actionable recommendations
    5. Maintain HIPAA compliance and medical confidentiality
    
    Guidelines:
    - Use clear, professional medical terminology
    - Focus on clinically relevant information
    - Highlight any concerning symptoms or findings
    - Suggest appropriate follow-up care when needed
    - Be objective and evidence-based
    - Include confidence assessment for your analysis
    
    Always structure your response with:
    - A comprehensive summary paragraph
    - Key clinical points (3-5 bullet points)
    - Specific recommendations for care
    - Assessment of follow-up necessity
    - Confidence score (0.0-1.0)
    """,
)


async def summarize_visit(
    visit: VisitResponse,
    patient: Optional[PatientResponse] = None,
    previous_visits: Optional[List[VisitResponse]] = None,
    summary_type: str = "comprehensive"
) -> VisitSummary:
    """
    Summarize a patient visit using AI.

    Args:
        visit: The visit to summarize
        patient: Patient information for context
        previous_visits: Previous visits for historical context
        summary_type: Type of summary (brief, comprehensive, detailed)

    Returns:
        Structured visit summary
    """

    # Prepare context
    context = SummaryContext(
        visit=visit,
        patient=patient,
        previous_visits=previous_visits
    )

    # Create prompt based on summary type
    if summary_type == "brief":
        prompt = f"""
        Create a brief summary of this patient visit:
        
        Visit Date: {visit.visit_date}
        Visit Type: {visit.visit_type}
        Chief Complaint: {visit.chief_complaint}
        Diagnosis: {visit.diagnosis}
        Treatment: {visit.treatment_plan}
        
        Focus on the most essential clinical information only.
        """
    elif summary_type == "detailed":
        prompt = f"""
        Create a detailed comprehensive summary of this patient visit including all available information:
        
        Patient: {patient.first_name + ' ' + patient.last_name if patient else 'Unknown'}
        Visit Date: {visit.visit_date}
        Visit Type: {visit.visit_type}
        
        Clinical Information:
        - Chief Complaint: {visit.chief_complaint}
        - Symptoms: {visit.symptoms}
        - Diagnosis: {visit.diagnosis}
        - Treatment Plan: {visit.treatment_plan}
        - Medications: {visit.medications_prescribed}
        - Doctor Notes: {visit.doctor_notes}
        - Vital Signs: {visit.vital_signs}
        - Lab Results: {visit.lab_results}
        - Follow-up: {visit.follow_up_instructions}
        
        {f"Patient History: {patient.medical_history}" if patient and patient.medical_history else ""}
        {f"Allergies: {patient.allergies}" if patient and patient.allergies else ""}
        {f"Current Medications: {patient.current_medications}" if patient and patient.current_medications else ""}
        
        Provide a thorough analysis including clinical reasoning and comprehensive recommendations.
        """
    else:  # comprehensive (default)
        prompt = f"""
        Create a comprehensive summary of this patient visit:
        
        Patient: {patient.first_name + ' ' + patient.last_name if patient else 'Unknown'}
        Visit Date: {visit.visit_date}
        Visit Type: {visit.visit_type}
        Chief Complaint: {visit.chief_complaint}
        Symptoms: {visit.symptoms}
        Diagnosis: {visit.diagnosis}
        Treatment Plan: {visit.treatment_plan}
        Medications Prescribed: {visit.medications_prescribed}
        Follow-up Instructions: {visit.follow_up_instructions}
        Doctor Notes: {visit.doctor_notes}
        
        {f"Relevant Patient History: {patient.medical_history}" if patient and patient.medical_history else ""}
        {f"Known Allergies: {patient.allergies}" if patient and patient.allergies else ""}
        
        Include clinical assessment, key findings, and actionable next steps.
        """

    # Run the agent
    result = await summarizer_agent.run(prompt, deps=context)

    return result.data


async def summarize_multiple_visits(
    visits: List[VisitResponse],
    patient: Optional[PatientResponse] = None
) -> str:
    """
    Create a summary across multiple visits for trend analysis.

    Args:
        visits: List of visits to analyze
        patient: Patient information

    Returns:
        Comprehensive multi-visit summary
    """

    visits_info = []
    for visit in visits:
        visits_info.append(f"""
        Visit {visit.visit_date.strftime('%Y-%m-%d')}:
        - Type: {visit.visit_type}
        - Chief Complaint: {visit.chief_complaint}
        - Diagnosis: {visit.diagnosis}
        - Treatment: {visit.treatment_plan}
        """)

    prompt = f"""
    Analyze the following series of patient visits and provide insights on:
    1. Health trends and patterns
    2. Treatment effectiveness
    3. Recurring issues or concerns
    4. Overall health trajectory
    5. Recommendations for future care
    
    Patient: {patient.first_name + ' ' + patient.last_name if patient else 'Unknown'}
    
    Visits:
    {''.join(visits_info)}
    
    Provide a cohesive analysis focusing on continuity of care and health outcomes.
    """

    result = await summarizer_agent.run(prompt)
    return result.data.summary
