"""
Chat API endpoints using LangGraph pipeline.

Provides unified chat endpoints with:
- Authentication (ADMIN/DOCTOR role required)
- SSE streaming support
- Persistent conversation state via LangGraph checkpointer
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.graph.pipeline import get_compiled_graph
from app.graph.state import ConversationState
from app.database.session import get_db
from app.models.user import User, UserRole
from app.utils.auth import require_role
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    """Request schema for chat endpoints."""

    message: str
    session_id: str


class ChatResponse(BaseModel):
    """Response schema for non-streaming chat endpoint."""

    response: str
    intent: str
    results_count: int


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DOCTOR)),
):
    """
    Unified chat endpoint with LangGraph pipeline.

    Requires ADMIN or DOCTOR role.
    Uses session_id for persistent conversation context.
    """
    graph = await get_compiled_graph()

    # State contains only serializable data
    initial_state: ConversationState = {
        "query": request.message,
        "session_id": request.session_id,
        "intent": None,
        "filters": {},
        "entity_to_resolve": None,
        "resolved_ids": {},
        "results": [],
        "response": "",
        "messages": [],
        "error": None,
    }

    # Pass db via config, NOT in state
    config = {
        "configurable": {
            "thread_id": request.session_id,
            "db": db,  # Database session passed here
        }
    }

    try:
        logger.info(f"Processing chat request for session: {request.session_id}")
        final_state = await graph.ainvoke(initial_state, config)

        return ChatResponse(
            response=final_state.get("response", ""),
            intent=final_state.get("intent") or "unknown",
            results_count=len(final_state.get("results", [])),
        )
    except Exception as e:
        logger.error(f"Chat pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DOCTOR)),
):
    """
    Streaming chat endpoint with node-level events.

    Uses Server-Sent Events (SSE) to stream pipeline progress.
    Each node completion emits an event with node name and output.
    """
    graph = await get_compiled_graph()

    initial_state: ConversationState = {
        "query": request.message,
        "session_id": request.session_id,
        "intent": None,
        "filters": {},
        "entity_to_resolve": None,
        "resolved_ids": {},
        "results": [],
        "response": "",
        "messages": [],
        "error": None,
    }

    config = {
        "configurable": {
            "thread_id": request.session_id,
            "db": db,
        }
    }

    async def stream_generator():
        try:
            logger.info(f"Starting stream for session: {request.session_id}")

            async for event in graph.astream(
                initial_state, config, stream_mode="updates"
            ):
                for node_name, node_output in event.items():
                    # Don't send db session in output (not serializable)
                    safe_output = {k: v for k, v in node_output.items() if k != "db"}
                    yield f"data: {json.dumps({'node': node_name, 'data': safe_output})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            logger.info(f"Stream completed for session: {request.session_id}")

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
