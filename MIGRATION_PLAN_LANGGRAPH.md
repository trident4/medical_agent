# Agentic RAG Pipeline Migration Plan (LangGraph)

> **Goal**: Convert Doctor's Assistant to a unified Agentic RAG Pipeline using **LangGraph** for orchestration and persistent state management.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│   FastAPI + SSE Streaming                                   │
│        │                                                    │
│        ▼                                                    │
│   LangGraph StateGraph (compiled once at startup)           │
│        │                                                    │
│        ├── extract_intent (Step A)                          │
│        ├── resolve_entities (Step B)                        │
│        ├── query_database (Step C) ─── AnalyticsAgent cache │
│        └── generate_response (Step D) ─── Token streaming   │
│                │                                            │
│                ▼                                            │
│   PostgresSaver (same DB, separate tables)                  │
│                                                             │
│   Existing Agents (FallbackAgent, AnalyticsAgent)           │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Add Dependencies (1 day)

### Install LangGraph

```bash
pip install langgraph langgraph-checkpoint-postgres "psycopg[binary,pool]"
```

### Update `requirements.txt`

```
langgraph>=0.2.0
langgraph-checkpoint-postgres>=1.0.0
psycopg[binary,pool]>=3.1.0
```

> [!WARNING]
> LangGraph's PostgresSaver requires `psycopg3`, not `psycopg2`. Your existing `asyncpg` works for SQLAlchemy, but LangGraph needs `psycopg`.

---

## Phase 1: Create State Schema (1-2 days)

### [NEW] `app/graph/__init__.py`

```python
"""LangGraph pipeline components."""
```

### [NEW] `app/graph/state.py`

> [!IMPORTANT]
>
> - LangGraph requires `TypedDict`, not Pydantic `BaseModel` for state.
> - **DO NOT put `db` session in state** - it cannot be serialized by checkpointer.
> - Use `str` for intent, not `Enum` (serialization issues).

```python
from typing import Optional, List, Dict, Any, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


# Intent as string constants (avoids Enum serialization issues)
INTENT_SEARCH = "search"
INTENT_DETAIL = "detail"
INTENT_SUMMARIZE = "summarize"
INTENT_ANALYTICS = "analytics"
INTENT_CHITCHAT = "chitchat"

VALID_INTENTS = {INTENT_SEARCH, INTENT_DETAIL, INTENT_SUMMARIZE, INTENT_ANALYTICS, INTENT_CHITCHAT}


class ConversationState(TypedDict):
    """
    LangGraph state - must be TypedDict, not BaseModel.

    IMPORTANT: Do NOT include database session here.
    Pass db via config["configurable"]["db"] instead.
    """
    # Input
    query: str
    session_id: str

    # Step A output
    intent: Optional[str]  # Use str, not Enum (serialization safe)
    filters: Dict[str, Any]
    entity_to_resolve: Optional[str]

    # Step B output
    resolved_ids: Dict[str, int]

    # Step C output
    results: List[Dict[str, Any]]

    # Step D output
    response: str

    # Conversation history (auto-accumulated by LangGraph)
    messages: Annotated[list, add_messages]

    # Error tracking
    error: Optional[str]
```

---

## Phase 2: Build Graph Nodes (3-4 days)

### [NEW] `app/graph/nodes.py`

> [!IMPORTANT]
> Database session is accessed via `config["configurable"]["db"]`, NOT from state.

```python
from typing import Any
from langgraph.types import RunnableConfig
from app.graph.state import (
    ConversationState,
    INTENT_SEARCH, INTENT_DETAIL, INTENT_SUMMARIZE,
    INTENT_ANALYTICS, INTENT_CHITCHAT, VALID_INTENTS
)
from app.agents.base_agent import FallbackAgent
from app.agents.analytics_agent import analytics_agent
import json
import logging

logger = logging.getLogger(__name__)

# Agents initialized once (singleton pattern)
intent_agent = FallbackAgent(system_prompt="""
You are an intent classifier for a medical assistant.
Given a user query, extract:
1. intent: One of "search", "detail", "summarize", "analytics", "chitchat"
2. filters: Relevant filters like patient_name, date_start, date_end, diagnosis
3. entity_to_resolve: Any name that needs to be looked up (e.g., "John Smith")

Return ONLY valid JSON:
{"intent": "search", "filters": {"patient_name": "..."}, "entity_to_resolve": null}
""")

narrator_agent = FallbackAgent(system_prompt="""
You are a helpful medical assistant for doctors.
Generate professional, concise responses based on query results.
Always cite specific data from results when available.
""")


async def extract_intent(state: ConversationState, config: RunnableConfig) -> dict:
    """Step A: Intent + Filter extraction."""
    try:
        recent_messages = state.get("messages", [])[-5:]
        context = f"Query: {state['query']}\nRecent conversation: {recent_messages}"

        result = await intent_agent.run_async(context)

        # Parse JSON response
        parsed = json.loads(result)
        intent = parsed.get("intent", INTENT_CHITCHAT)

        # Validate intent
        if intent not in VALID_INTENTS:
            intent = INTENT_CHITCHAT

        return {
            "intent": intent,
            "filters": parsed.get("filters", {}),
            "entity_to_resolve": parsed.get("entity_to_resolve"),
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse intent JSON: {e}")
        return {"intent": INTENT_CHITCHAT, "filters": {}, "entity_to_resolve": None}
    except Exception as e:
        logger.error(f"Intent extraction failed: {e}")
        return {"error": f"Intent extraction failed: {str(e)}"}


async def resolve_entities(state: ConversationState, config: RunnableConfig) -> dict:
    """Step B: Resolve names to database IDs."""
    if state.get("error"):
        return {}  # Skip if previous step failed

    try:
        entity = state.get("entity_to_resolve")
        if not entity:
            return {"resolved_ids": {}}

        # Get db from config, NOT from state
        db = config["configurable"]["db"]

        from sqlalchemy import select, or_
        from app.models.patient import Patient

        # Search both first_name and last_name (Patient has no 'name' field)
        result = await db.execute(
            select(Patient).where(
                or_(
                    Patient.first_name.ilike(f"%{entity}%"),
                    Patient.last_name.ilike(f"%{entity}%")
                )
            ).limit(1)
        )
        patient = result.scalar_one_or_none()

        if patient:
            return {"resolved_ids": {"patient_id": patient.id}}
        return {"resolved_ids": {}}

    except Exception as e:
        logger.error(f"Entity resolution failed: {e}")
        return {"error": f"Entity resolution failed: {str(e)}"}


async def query_database(state: ConversationState, config: RunnableConfig) -> dict:
    """Step C: Execute database query with caching."""
    if state.get("error"):
        return {}

    try:
        # Get db from config
        db = config["configurable"]["db"]
        intent = state.get("intent")

        # Use AnalyticsAgent for analytics queries (has cache + templates)
        if intent == INTENT_ANALYTICS:
            result = await analytics_agent.answer_analytics_question(
                question=state["query"],
                db=db,
                explain=False  # We'll explain in Step D
            )
            return {"results": result.get("results", [])}

        # For SEARCH/DETAIL, use filters
        filters = state.get("filters", {})
        resolved = state.get("resolved_ids", {})

        from sqlalchemy import select
        from app.models.visit import Visit

        query = select(Visit)

        if resolved.get("patient_id"):
            query = query.where(Visit.patient_id == resolved["patient_id"])

        # Add date filters if present
        if filters.get("date_start"):
            query = query.where(Visit.visit_date >= filters["date_start"])
        if filters.get("date_end"):
            query = query.where(Visit.visit_date <= filters["date_end"])

        result = await db.execute(query.order_by(Visit.visit_date.desc()).limit(20))
        visits = result.scalars().all()

        return {
            "results": [
                {"id": v.id, "date": str(v.visit_date), "chief_complaint": v.chief_complaint}
                for v in visits
            ]
        }

    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return {"error": f"Database query failed: {str(e)}"}


async def generate_response(state: ConversationState, config: RunnableConfig) -> dict:
    """Step D: Generate natural language response."""
    # Handle errors gracefully
    if state.get("error"):
        error_msg = f"I encountered an issue: {state['error']}. Please try rephrasing your question."
        return {
            "response": error_msg,
            "messages": [
                {"role": "user", "content": state["query"]},
                {"role": "assistant", "content": error_msg}
            ]
        }

    try:
        results = state.get("results", [])
        results_summary = f"{len(results)} results found" if results else "No results found"

        prompt = f"""
User Query: {state['query']}
Intent: {state.get('intent')}
Results: {results[:10]}  # Limit to first 10 for context
Summary: {results_summary}

Generate a helpful, professional response for a medical professional.
If there are results, summarize them clearly. If no results, suggest alternatives.
"""
        response = await narrator_agent.run_async(prompt)

        return {
            "response": response,
            "messages": [
                {"role": "user", "content": state["query"]},
                {"role": "assistant", "content": response}
            ]
        }
    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        fallback = "I apologize, but I couldn't generate a response. Please try again."
        return {
            "response": fallback,
            "messages": [
                {"role": "user", "content": state["query"]},
                {"role": "assistant", "content": fallback}
            ],
            "error": str(e)
        }
```

---

## Phase 3: Create the Graph (2-3 days)

### [NEW] `app/graph/pipeline.py`

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.graph.state import (
    ConversationState,
    INTENT_CHITCHAT, INTENT_ANALYTICS
)
from app.graph.nodes import (
    extract_intent, resolve_entities,
    query_database, generate_response
)
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Singleton instances
_checkpointer: AsyncPostgresSaver = None
_compiled_graph = None


def route_by_intent(state: ConversationState) -> str:
    """Conditional routing based on intent."""
    # Handle errors - go straight to response
    if state.get("error"):
        return "generate_response"

    intent = state.get("intent")

    if intent == INTENT_CHITCHAT:
        return "generate_response"  # Skip B, C

    if intent == INTENT_ANALYTICS:
        return "query_database"  # Skip B (no entity resolution needed)

    return "resolve_entities"


def build_graph() -> StateGraph:
    """Build the LangGraph state machine."""
    graph = StateGraph(ConversationState)

    # Add nodes
    graph.add_node("extract_intent", extract_intent)
    graph.add_node("resolve_entities", resolve_entities)
    graph.add_node("query_database", query_database)
    graph.add_node("generate_response", generate_response)

    # Add edges with conditional routing
    graph.set_entry_point("extract_intent")

    # Conditional edges from extract_intent
    graph.add_conditional_edges(
        "extract_intent",
        route_by_intent,
        {
            "resolve_entities": "resolve_entities",
            "query_database": "query_database",
            "generate_response": "generate_response",
        }
    )

    graph.add_edge("resolve_entities", "query_database")
    graph.add_edge("query_database", "generate_response")
    graph.add_edge("generate_response", END)

    return graph


async def get_checkpointer() -> AsyncPostgresSaver:
    """Get or create singleton checkpointer."""
    global _checkpointer
    if _checkpointer is None:
        # LangGraph needs psycopg3 connection string format
        # Convert from asyncpg format if needed
        db_url = settings.DATABASE_URL

        # If using asyncpg format, convert for psycopg
        if "asyncpg" in db_url:
            db_url = db_url.replace("postgresql+asyncpg", "postgresql")

        _checkpointer = await AsyncPostgresSaver.from_conn_string(db_url)

        # Create checkpoint tables if they don't exist
        await _checkpointer.setup()
        logger.info("✅ PostgreSQL checkpointer initialized")

    return _checkpointer


async def get_compiled_graph():
    """Get or create singleton compiled graph."""
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_graph()
        checkpointer = await get_checkpointer()
        _compiled_graph = graph.compile(checkpointer=checkpointer)
        logger.info("✅ LangGraph pipeline compiled with PostgreSQL checkpointer")
    return _compiled_graph
```

---

## Phase 4: Wire Up API with Auth (1-2 days)

### [NEW] `app/api/v1/endpoints/chat.py`

> [!IMPORTANT]
> Database session is passed via `config["configurable"]["db"]`, not in state.

```python
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
    message: str
    session_id: str


class ChatResponse(BaseModel):
    response: str
    intent: str
    results_count: int


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DOCTOR))
):
    """
    Unified chat endpoint with LangGraph pipeline.
    Requires ADMIN or DOCTOR role.
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
        final_state = await graph.ainvoke(initial_state, config)

        return ChatResponse(
            response=final_state.get("response", ""),
            intent=final_state.get("intent") or "unknown",
            results_count=len(final_state.get("results", []))
        )
    except Exception as e:
        logger.error(f"Chat pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DOCTOR))
):
    """
    Streaming chat endpoint with node-level events.
    Uses Server-Sent Events (SSE).
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
            async for event in graph.astream(initial_state, config, stream_mode="updates"):
                for node_name, node_output in event.items():
                    # Don't send db session in output
                    safe_output = {k: v for k, v in node_output.items() if k != "db"}
                    yield f"data: {json.dumps({'node': node_name, 'data': safe_output})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

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
        }
    )
```

### [MODIFY] `app/api/v1/api.py`

```python
from app.api.v1.endpoints import chat

api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
```

---

## Phase 5: Add Observability (1 day)

### [MODIFY] `app/config.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # LangSmith (optional observability)
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "doctors-assistant"
```

### [MODIFY] `app/main.py`

```python
# Add at startup (in lifespan or before app creation)
import os
if settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    logger.info("✅ LangSmith tracing enabled")
```

---

## File Summary

| Phase | File                           | Action |
| ----- | ------------------------------ | ------ |
| 0     | `requirements.txt`             | MODIFY |
| 1     | `app/graph/__init__.py`        | NEW    |
| 1     | `app/graph/state.py`           | NEW    |
| 2     | `app/graph/nodes.py`           | NEW    |
| 3     | `app/graph/pipeline.py`        | NEW    |
| 4     | `app/api/v1/endpoints/chat.py` | NEW    |
| 4     | `app/api/v1/api.py`            | MODIFY |
| 5     | `app/config.py`                | MODIFY |
| 5     | `app/main.py`                  | MODIFY |

---

## Database Configuration

> [!TIP] > **Use your existing PostgreSQL database** (`doctors_assistant`).
>
> LangGraph's `AsyncPostgresSaver.setup()` creates its own tables:
>
> - `checkpoints` - Stores graph state
> - `checkpoint_blobs` - Stores large binary data
> - `checkpoint_writes` - Transaction log
>
> These won't conflict with your existing tables.

> [!WARNING] > **DATABASE_URL Format**: LangGraph uses `psycopg3`, not `asyncpg`.
>
> The pipeline automatically converts `postgresql+asyncpg://` to `postgresql://` when initializing the checkpointer.

---

## Error Handling Strategy

The plan uses **graceful degradation**:

1. **Step-level errors**: Each node catches exceptions and sets `state["error"]`
2. **Routing**: The router checks for errors and skips to `generate_response`
3. **User-friendly response**: `generate_response` returns helpful error message
4. **Logging**: All errors logged for debugging

```
User Query → extract_intent (error!) → route → generate_response → "I couldn't understand..."
```

---

## Streaming Strategy

**Standard approach**: Node-level events via SSE

| Event Type | When                | Example                                                    |
| ---------- | ------------------- | ---------------------------------------------------------- |
| `node`     | Each step completes | `{"node": "extract_intent", "data": {"intent": "search"}}` |
| `done`     | Pipeline complete   | `{"type": "done"}`                                         |
| `error`    | On failure          | `{"type": "error", "error": "..."}`                        |

---

## Timeline Summary

| Phase | Focus         | Effort   |
| ----- | ------------- | -------- |
| 0     | Dependencies  | 1 day    |
| 1     | State Schema  | 1-2 days |
| 2     | Graph Nodes   | 3-4 days |
| 3     | Build Graph   | 2-3 days |
| 4     | API + Auth    | 1-2 days |
| 5     | Observability | 1 day    |

**Total: 9-13 days**

---

## Backward Compatibility

> [!IMPORTANT]
> All existing endpoints remain functional.

- `POST /api/v1/agents/summarize` → Unchanged
- `POST /api/v1/agents/ask` → Unchanged
- `POST /api/v1/analytics/query` → Unchanged (still uses cached AnalyticsAgent)
- **NEW**: `POST /api/v1/chat` → LangGraph pipeline (requires auth)
- **NEW**: `POST /api/v1/chat/stream` → SSE streaming version
