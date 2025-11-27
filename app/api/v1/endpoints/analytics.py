from app.models.user import User, UserRole
from app.utils.auth import require_role
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.agents.analytics_agent import analytics_agent
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class AnalyticsQuery(BaseModel):
    question: str
    explain: bool = True

class AnalyticsResponse(BaseModel):
    question: str
    sql_query: str
    results: list
    row_count: int
    explanation: Optional[str] = None
    error: Optional[str] = None

@router.post("/query", response_model=AnalyticsResponse)
async def analytics_query(
    query: AnalyticsQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.ADMIN, UserRole.DOCTOR))
):
    """
    Answer analytics questions using AI-generated SQL queries.
    
    Example questions:
    - "How many visits in the last 30 days?"
    - "What's the average visit duration?"
    - "Which patient has the most visits?"
    """
    result = await analytics_agent.answer_analytics_question(
        question=query.question,
        db=db,
        explain=query.explain
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.get("/examples")
async def get_example_questions():
    """Get example analytics questions"""
    return {
        "examples": analytics_agent.get_example_questions()
    }