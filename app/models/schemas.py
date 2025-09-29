"""
API request and response schemas.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class SummarizeVisitRequest(BaseModel):
    """Request schema for visit summarization."""

    visit_id: str = Field(..., description="Visit ID to summarize")
    include_patient_history: bool = Field(
        default=False, description="Include patient medical history")
    summary_type: str = Field(
        default="comprehensive", description="Type of summary: brief, comprehensive, or detailed")


class SummarizeVisitResponse(BaseModel):
    """Response schema for visit summarization."""

    visit_id: str
    summary: str
    key_points: List[str]
    recommendations: List[str]
    follow_up_required: bool
    confidence_score: float
    generated_at: datetime


class QuestionAnswerRequest(BaseModel):
    """Request schema for Q&A about patient data."""

    question: str = Field(..., description="Question about patient data")
    patient_id: Optional[str] = Field(
        None, description="Specific patient ID to query")
    visit_id: Optional[str] = Field(
        None, description="Specific visit ID to query")
    context_type: str = Field(
        default="all", description="Context type: patient, visit, or all")


class QuestionAnswerResponse(BaseModel):
    """Response schema for Q&A."""

    question: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence_score: float
    context_used: str
    generated_at: datetime


class HealthSummaryRequest(BaseModel):
    """Request schema for patient health summary."""

    patient_id: str = Field(..., description="Patient ID for health summary")
    include_recent_visits: int = Field(
        default=5, description="Number of recent visits to include")
    time_period_days: Optional[int] = Field(
        None, description="Time period in days to consider")


class HealthSummaryResponse(BaseModel):
    """Response schema for patient health summary."""

    patient_id: str
    summary: str
    health_trends: List[str]
    risk_factors: List[str]
    recommendations: List[str]
    recent_visits_count: int
    last_visit_date: Optional[datetime]
    generated_at: datetime


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: datetime


class SuccessResponse(BaseModel):
    """Success response schema."""

    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime
