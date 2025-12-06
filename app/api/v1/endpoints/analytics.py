from app.models.user import User, UserRole
from app.utils.auth import require_role
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.agents.analytics_agent import analytics_agent
from app.utils.streaming_utils import stream_response
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)
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

@router.post("/query/stream")
async def analytics_query_stream(
    query: AnalyticsQuery,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.ADMIN, UserRole.DOCTOR))
):
    """
    Stream analytics query results and explanation.
    First returns metadata (question, SQL, results), then streams the explanation.
    """
    async def generate_stream():
        try:
            # Get raw stream from analytics agent
            content_stream = analytics_agent.answer_analytics_question_stream(
                question=query.question,
                db=db
            )
            
            # Wrap with SSE formatting
            async for sse_message in stream_response(content_stream):
                yield sse_message
            
            # Log the query
            background_tasks.add_task(
                logger.info,
                f"Analytics query answered (streaming): {query.question}"
            )
        
        except Exception as e:
            logger.error("Error streaming analytics query",
                         question=query.question, error=str(e))
            yield f"data: {{\"type\": \"error\", \"error\": \"{str(e)}\"}}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/examples")
async def get_example_questions():
    """Get example analytics questions"""
    return {
        "examples": analytics_agent.get_example_questions()
    }