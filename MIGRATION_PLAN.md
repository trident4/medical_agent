# Agentic RAG Pipeline Migration Plan

> **Goal**: Convert Doctor's Assistant from independent agents to a unified Agentic RAG Pipeline with intent classification, structured extraction, and session state management.

---

## Phase 0: Upgrade to OpenAIResponsesModel (1 day)

**Goal**: Switch from `OpenAIChatModel` to `OpenAIResponsesModel` for better structured output support.

### [MODIFY] `app/agents/base_agent.py`

```python
# Update import
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIResponsesModel

# For OpenAI - use Responses API (structured outputs)
openai_model = OpenAIResponsesModel(
    'gpt-4o-mini',
    api_key=settings.OPENAI_API_KEY
)
agents['openai'] = Agent(openai_model, system_prompt=self.system_prompt)

# For X.AI/Grok - keep Chat Completions API (compatible)
xai_model = OpenAIChatModel(
    'grok-2-1212',
    provider=GrokProvider(api_key=settings.XAI_API_KEY)
)
```

**Why**: `OpenAIResponsesModel` provides better structured output extraction needed for Phase 1's `ExtractionResult` schema.

---

## Phase 1: Create Extraction Schema (2-3 days)

**Goal**: Define what the LLM should extract from user queries.

### [NEW] `app/schemas/extraction.py`

```python
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from datetime import date

class IntentType(str, Enum):
    SEARCH = "search"           # Find appointments/patients/records
    DETAIL = "detail"           # More info about specific item
    ACTION = "action"           # Schedule, cancel, reschedule
    SUMMARIZE = "summarize"     # Summarize visit/history
    ANALYTICS = "analytics"     # Analytics questions (SQL-based)
    CHITCHAT = "chitchat"       # Greetings, help, off-topic

class MedicalFilters(BaseModel):
    patient_name: Optional[str] = Field(None, description="Patient's name if mentioned")
    patient_id: Optional[int] = Field(None, description="Resolved patient ID")
    doctor_name: Optional[str] = Field(None, description="Doctor's name if mentioned")
    date_start: Optional[date] = Field(None, description="Start of date range")
    date_end: Optional[date] = Field(None, description="End of date range")
    visit_type: Optional[str] = Field(None, description="Type: checkup, follow-up, etc.")
    diagnosis: Optional[str] = Field(None, description="Diagnosis or condition mentioned")

class ExtractionResult(BaseModel):
    intent: IntentType
    filters: MedicalFilters
    reference_index: Optional[int] = Field(None, description="1-indexed position in last results")
    entity_to_resolve: Optional[str] = Field(None, description="Name/term needing ID lookup")
    raw_question: str = Field(..., description="Original user query for context")
```

---

## Phase 2: Build Pipeline Orchestrator (5-7 days)

**Goal**: Create central controller that runs Steps A→B→C→D.

### [NEW] `app/pipeline.py`

```python
class MedicalPipeline:
    """Orchestrates the 4-step Agentic RAG pipeline."""

    def __init__(self):
        self.extractor = IntentExtractor()
        self.resolver = EntityResolver()
        self.narrator = FallbackAgent(system_prompt="...")

    async def run_stream(self, query: str, session_id: str, db: AsyncSession):
        state = get_session_state(session_id)

        # Step A: Intent + Extraction
        yield {"type": "status", "step": "extracting"}
        extraction = await self.extractor.extract(query, state.filters, state.last_results)

        # Route based on intent
        match extraction.intent:
            case IntentType.CHITCHAT: ...
            case IntentType.ANALYTICS: ...

        # Step B: Entity Resolution
        if extraction.entity_to_resolve:
            yield {"type": "status", "step": "resolving"}
            extraction.filters.patient_id = await self.resolver.resolve_patient(...)

        # Step C: Database Query
        yield {"type": "status", "step": "searching"}
        results = await self._query_database(extraction.filters, db)
        yield {"type": "data", "results": results}

        # Step D: Narration
        yield {"type": "status", "step": "narrating"}
        async for chunk in self.narrator.run_stream(...):
            yield {"type": "text", "content": chunk}

        # Save state
        save_session_state(session_id, state)
        yield {"type": "done"}
```

---

## Phase 3: Implement Steps A-D (5-7 days)

### Step A: Intent Extractor

**[NEW] `app/agents/intent_extractor.py`**

```python
class IntentExtractor:
    """Classify intent and extract structured filters in ONE LLM call."""

    async def extract(self, query, current_filters, last_results) -> ExtractionResult:
        # Single LLM call with structured output
```

### Step B: Entity Resolution

**[NEW] `app/services/resolver.py`**

```python
class EntityResolver:
    async def resolve_patient(self, name: str, db) -> Optional[int]:
        """Fuzzy match patient name to patient_id."""
```

### Step C: Database Query

**[MODIFY] `app/agents/analytics_agent.py`**

```python
async def search_with_filters(self, filters: MedicalFilters, db) -> list:
    """Execute parameterized query based on extracted filters."""
```

### Step D: Narrator

No changes - `FallbackAgent.run_stream()` already handles this.

---

## Phase 4: Add Session State (2-3 days)

**Goal**: Enable multi-turn conversations with context preservation.

### [NEW] `app/state.py`

```python
@dataclass
class SessionState:
    filters: Dict[str, Any] = field(default_factory=dict)
    last_results: List[Dict] = field(default_factory=list)
    history: List[Dict[str, str]] = field(default_factory=list)

_sessions: Dict[str, SessionState] = {}  # Use Redis for production

def get_session_state(session_id: str) -> SessionState: ...
def save_session_state(session_id: str, state: SessionState): ...
def clear_session(session_id: str): ...
```

---

## Phase 5: Wire Up the API (1-2 days)

**Goal**: Create unified `/chat` endpoint using the pipeline.

### [NEW] `app/api/v1/endpoints/chat.py`

```python
@router.post("/chat")
async def chat(request: ChatRequest, db = Depends(get_db)):
    async def stream_generator():
        async for event in pipeline.run_stream(request.message, request.session_id, db):
            yield f"data: {json.dumps(event)}\n\n"
    return StreamingResponse(stream_generator(), media_type="text/event-stream")
```

### [MODIFY] `app/api/v1/api.py`

```python
from app.api.v1.endpoints import chat
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
```

---

## Summary

| Phase | Focus                 | Effort   | New Files                            |
| ----- | --------------------- | -------- | ------------------------------------ |
| 0     | OpenAIResponsesModel  | 1 day    | -                                    |
| 1     | Extraction Schema     | 2-3 days | `app/schemas/extraction.py`          |
| 2     | Pipeline Orchestrator | 5-7 days | `app/pipeline.py`                    |
| 3     | Steps A-D             | 5-7 days | `intent_extractor.py`, `resolver.py` |
| 4     | Session State         | 2-3 days | `app/state.py`                       |
| 5     | Unified API           | 1-2 days | `app/api/v1/endpoints/chat.py`       |

**Total**: ~16-23 days

---

## Backward Compatibility

> [!IMPORTANT]
> All existing endpoints remain functional. The new `/chat` endpoint is additive.

Existing endpoints preserved:

- `POST /api/v1/agents/summarize`
- `POST /api/v1/agents/ask`
- `POST /api/v1/analytics/query`
