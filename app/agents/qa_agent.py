"""
Question-answering agent using PydanticAI.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from app.models.visit import VisitResponse
from app.models.patient import PatientResponse


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


# Create the Q&A agent
qa_agent = Agent(
    'openai:gpt-4o',  # or 'anthropic:claude-3-5-sonnet-20241022'
    result_type=QAResponse,
    system_prompt="""
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
    
    Always structure your response with:
    - Clear, direct answer to the question
    - Specific sources and references
    - Confidence assessment
    - Context clarification
    """,
)


async def answer_question(
    question: str,
    patient_id: Optional[str] = None,
    visit_id: Optional[str] = None,
    patients: Optional[List[PatientResponse]] = None,
    visits: Optional[List[VisitResponse]] = None
) -> QAResponse:
    """
    Answer a question about patient data using AI.

    Args:
        question: The question to answer
        patient_id: Specific patient ID to focus on
        visit_id: Specific visit ID to focus on
        patients: List of patients for context
        visits: List of visits for context

    Returns:
        Structured Q&A response
    """

    # Filter data based on specific IDs
    specific_patient = None
    specific_visit = None
    relevant_visits = visits or []
    relevant_patients = patients or []

    if patient_id and patients:
        specific_patient = next(
            (p for p in patients if p.patient_id == patient_id), None)
        if specific_patient:
            relevant_visits = [
                v for v in visits if v.patient_id == specific_patient.id] if visits else []

    if visit_id and visits:
        specific_visit = next(
            (v for v in visits if v.visit_id == visit_id), None)
        if specific_visit and patients:
            specific_patient = next(
                (p for p in patients if p.id == specific_visit.patient_id), None)

    # Prepare context
    context = QAContext(
        patients=relevant_patients,
        visits=relevant_visits,
        specific_patient=specific_patient,
        specific_visit=specific_visit
    )

    # Build context information for the prompt
    context_info = []

    if specific_patient:
        context_info.append(f"""
        Patient Information:
        - ID: {specific_patient.patient_id}
        - Name: {specific_patient.first_name} {specific_patient.last_name}
        - DOB: {specific_patient.date_of_birth}
        - Gender: {specific_patient.gender}
        - Medical History: {specific_patient.medical_history}
        - Allergies: {specific_patient.allergies}
        - Current Medications: {specific_patient.current_medications}
        """)

    if specific_visit:
        context_info.append(f"""
        Visit Information:
        - Visit ID: {specific_visit.visit_id}
        - Date: {specific_visit.visit_date}
        - Type: {specific_visit.visit_type}
        - Chief Complaint: {specific_visit.chief_complaint}
        - Symptoms: {specific_visit.symptoms}
        - Diagnosis: {specific_visit.diagnosis}
        - Treatment Plan: {specific_visit.treatment_plan}
        - Medications Prescribed: {specific_visit.medications_prescribed}
        - Doctor Notes: {specific_visit.doctor_notes}
        - Follow-up Instructions: {specific_visit.follow_up_instructions}
        """)
    elif relevant_visits:
        context_info.append("Recent Visits:")
        for visit in relevant_visits[-5:]:  # Last 5 visits
            context_info.append(f"""
            - {visit.visit_date.strftime('%Y-%m-%d')}: {visit.visit_type}
              Chief Complaint: {visit.chief_complaint}
              Diagnosis: {visit.diagnosis}
            """)

    if not context_info:
        context_info.append(
            "No specific patient or visit data provided. Using general medical knowledge.")

    prompt = f"""
    Question: {question}
    
    Available Context:
    {''.join(context_info)}
    
    Please answer the question based on the provided medical data. Be specific about which information you're referencing and provide appropriate sources.
    """

    # Run the agent
    result = await qa_agent.run(prompt, deps=context)

    return result.data


async def get_patient_insights(patient: PatientResponse, visits: List[VisitResponse]) -> str:
    """
    Generate insights about a patient's health based on their visit history.

    Args:
        patient: Patient information
        visits: List of patient visits

    Returns:
        Health insights and trends
    """

    visits_summary = []
    for visit in visits:
        visits_summary.append(f"""
        {visit.visit_date.strftime('%Y-%m-%d')} - {visit.visit_type}:
        - Chief Complaint: {visit.chief_complaint}
        - Diagnosis: {visit.diagnosis}
        - Treatment: {visit.treatment_plan}
        """)

    prompt = f"""
    Analyze the health patterns and provide insights for this patient:
    
    Patient: {patient.first_name} {patient.last_name}
    Medical History: {patient.medical_history}
    Allergies: {patient.allergies}
    Current Medications: {patient.current_medications}
    
    Visit History:
    {''.join(visits_summary)}
    
    Provide insights on:
    1. Health trends and patterns
    2. Risk factors identified
    3. Treatment effectiveness
    4. Recommendations for future care
    5. Areas requiring attention
    """

    result = await qa_agent.run(prompt)
    return result.data.answer


async def compare_visits(visit1: VisitResponse, visit2: VisitResponse) -> str:
    """
    Compare two visits to identify changes and trends.

    Args:
        visit1: First visit (typically earlier)
        visit2: Second visit (typically later)

    Returns:
        Comparison analysis
    """

    prompt = f"""
    Compare these two patient visits and identify changes, improvements, or concerns:
    
    Visit 1 ({visit1.visit_date.strftime('%Y-%m-%d')}):
    - Type: {visit1.visit_type}
    - Chief Complaint: {visit1.chief_complaint}
    - Symptoms: {visit1.symptoms}
    - Diagnosis: {visit1.diagnosis}
    - Treatment: {visit1.treatment_plan}
    
    Visit 2 ({visit2.visit_date.strftime('%Y-%m-%d')}):
    - Type: {visit2.visit_type}
    - Chief Complaint: {visit2.chief_complaint}
    - Symptoms: {visit2.symptoms}
    - Diagnosis: {visit2.diagnosis}
    - Treatment: {visit2.treatment_plan}
    
    Analyze:
    1. Changes in symptoms or conditions
    2. Treatment effectiveness
    3. New concerns or improvements
    4. Recommendations for next steps
    """

    result = await qa_agent.run(prompt)
    return result.data.answer
