# Skill: Agentic RAG Pipeline Architecture

> **How to use this file**: Copy this file into your project root. Then ask your AI assistant:
> "Read skill.md and assess this project against the Agentic RAG Pipeline pattern. Create an assessment report."

---

## Agent Prompt

```
You are assessing a codebase to determine if it follows the "Agentic RAG Pipeline" architecture.

STEP 1: READ THIS FILE
Understand the architecture pattern described below.

STEP 2: EXPLORE THE PROJECT
- Find the main API entry point (look for FastAPI app, /chat endpoints)
- Identify all LLM calls (search for openai, anthropic, llm, generate, chat_completion)
- Find database queries (search for SELECT, execute, fetch, query)
- Check for session/state management (search for session, state, history, context)

STEP 3: CREATE ASSESSMENT REPORT
Create a file called `ARCHITECTURE_ASSESSMENT.md` with:
1. Current Architecture Summary (what does the project do today?)
2. Assessment Checklist (use Part 1 below, mark ✅ or ❌)
3. Gap Analysis (what's missing from the ideal pattern?)
4. Migration Recommendations (ordered by priority)
5. Estimated Effort (which changes are quick vs. significant?)

STEP 4: IF USER WANTS MIGRATION
Follow the Phase 1-5 migration guide below to convert the project step by step.
```

---

A step-by-step guide to assess if a project follows the **Agentic RAG Pipeline** pattern and how to convert it if it doesn't.

---

## Part 1: Architecture Assessment Checklist

Use this checklist to evaluate any conversational AI + database project.

### Core Pattern Components

| #   | Component                 | Question                                                                                        | ✅/❌ |
| --- | ------------------------- | ----------------------------------------------------------------------------------------------- | ----- |
| 1   | **Intent Classification** | Does the system classify user queries into distinct intents (search, detail, action, chitchat)? |       |
| 2   | **Structured Extraction** | Does an LLM extract structured data (filters, entities) from natural language?                  |       |
| 3   | **Step-Based Pipeline**   | Are processing steps separated (extract → resolve → query → generate)?                          |       |
| 4   | **Session State**         | Does the system maintain conversation context across turns?                                     |       |
| 5   | **SSE Streaming**         | Does the UI receive real-time updates during processing?                                        |       |

### Step-by-Step Breakdown

| Step                            | What It Should Do                                                       | Your Project Has It? |
| ------------------------------- | ----------------------------------------------------------------------- | -------------------- |
| **Step A: Intent + Extraction** | LLM classifies intent AND extracts structured entities in ONE call      |                      |
| **Step B: Entity Resolution**   | Converts names/locations to IDs, geocodes addresses, validates entities |                      |
| **Step C: Database Query**      | Executes parameterized SQL/API calls with extracted filters             |                      |
| **Step D: Response Generation** | LLM generates natural language from query results                       |                      |

### Red Flags (Anti-Patterns)

- [ ] ❌ LLM is called for every database query (wasteful)
- [ ] ❌ Intent detection and filter extraction are separate LLM calls
- [ ] ❌ No session state - each query is independent
- [ ] ❌ Full response generated before sending to frontend (no streaming)
- [ ] ❌ LLM generates SQL directly (security risk + fragile)
- [ ] ❌ Hardcoded if/else for intent detection instead of LLM

---

## Part 2: Assessment Questions

Run through these questions to understand your project's current state:

### 1. Entry Point Analysis

```bash
# Find your main API endpoint
grep -r "async def" --include="*.py" | grep -E "(chat|query|ask|message)"
```

**Questions:**

- Where does the user query enter the system?
- Is there one endpoint or multiple?
- Does it use SSE/WebSocket or simple request/response?

### 2. LLM Usage Mapping

```bash
# Find all LLM calls
grep -r "openai\|anthropic\|llm\|chat_completion\|generate" --include="*.py"
```

**Questions:**

- How many places call the LLM?
- What does each call do? (intent? extraction? response? all-in-one?)
- Is there a sub-agent pattern or single monolithic agent?

### 3. State Management

```bash
# Find session/state handling
grep -r "session\|state\|context\|history" --include="*.py"
```

**Questions:**

- How is conversation history stored?
- Are previous filters/entities preserved across turns?
- What happens when user says "under $500k" after "farms in Iowa"?

### 4. Database Integration

```bash
# Find database queries
grep -r "SELECT\|INSERT\|execute\|query\|fetch" --include="*.py"
```

**Questions:**

- How are query parameters passed? (parameterized or string concat?)
- Who builds the SQL - LLM or code?
- Is there a dedicated database layer?

---

## Part 3: Migration Guide

### Phase 1: Create the Extraction Schema

**Goal:** Define what the LLM should extract from user queries.

#### Step 1.1: Identify Your Entities

List all things users might mention:

```python
# Example for Doctor's Assistant
class DoctorAssistantFilters(BaseModel):
    """Filters extractable from user queries."""

    # Patient identification
    patient_name: Optional[str] = Field(None, description="Patient's name if mentioned")
    patient_id: Optional[int] = Field(None, description="Resolved patient ID")

    # Time filters
    date_start: Optional[date] = Field(None, description="Start of date range")
    date_end: Optional[date] = Field(None, description="End of date range")

    # Doctor filters
    doctor_name: Optional[str] = Field(None, description="Doctor's name if mentioned")
    specialty: Optional[str] = Field(None, description="Medical specialty")

    # Appointment filters
    appointment_type: Optional[str] = Field(None, description="Type: checkup, follow-up, etc.")
    status: Optional[str] = Field(None, description="Status: scheduled, completed, cancelled")
```

#### Step 1.2: Define Your Intents

```python
class IntentType(str, Enum):
    SEARCH = "search"           # Find appointments/patients/records
    DETAIL = "detail"           # More info about specific item
    ACTION = "action"           # Schedule, cancel, reschedule
    CHITCHAT = "chitchat"       # Greetings, help, off-topic
```

#### Step 1.3: Create Extraction Result

```python
class ExtractionResult(BaseModel):
    """Output from Step A: Intent + Filter Extraction."""

    intent: IntentType
    filters: DoctorAssistantFilters

    # For detail/action intents
    reference_index: Optional[int] = Field(
        None,
        description="1-indexed position in last results, e.g. 'the 2nd appointment'"
    )

    # For resolution in Step B
    entity_to_resolve: Optional[str] = Field(
        None,
        description="Name/term that needs ID lookup, e.g. 'Dr. Smith'"
    )
```

---

### Phase 2: Build the Pipeline Orchestrator

**Goal:** Create the central controller that runs Steps A→B→C→D.

```python
# app/pipeline.py

class AssistantPipeline:
    """Orchestrates the 4-step pipeline."""

    def __init__(self):
        self.extractor = IntentExtractor()
        self.narrator = NarrativeAgent()

    async def run_stream(
        self,
        query: str,
        session_id: str,
    ) -> AsyncGenerator[dict, None]:
        """Execute pipeline with SSE streaming."""

        # Load session state
        state = get_session_state(session_id)

        # === STEP A: Intent + Extraction ===
        yield {"type": "status", "step": "extracting"}
        extraction = await self.extractor.extract(
            query=query,
            current_filters=state.filters,
            last_results=state.last_results,
            conversation_history=state.history,
        )

        # Route based on intent
        if extraction.intent == IntentType.CHITCHAT:
            async for event in self._handle_chitchat(query, state):
                yield event
            return

        if extraction.intent == IntentType.DETAIL:
            async for event in self._handle_detail(extraction, state):
                yield event
            return

        # === STEP B: Entity Resolution (if needed) ===
        if extraction.entity_to_resolve:
            yield {"type": "status", "step": "resolving"}
            resolved = await self._resolve_entity(extraction.entity_to_resolve)
            extraction.filters.patient_id = resolved.id  # Example

        # === STEP C: Database Query ===
        yield {"type": "status", "step": "searching"}
        results = await self._query_database(extraction.filters)

        # Emit results immediately
        yield {
            "type": "data",
            "results": [r.dict() for r in results],
            "count": len(results),
        }

        # === STEP D: Narration ===
        yield {"type": "status", "step": "narrating"}
        async for chunk in self.narrator.stream(results, extraction.filters, query):
            yield {"type": "text", "content": chunk}

        # Save state
        state.filters = extraction.filters
        state.last_results = results
        state.history.append({"role": "user", "content": query})
        save_session_state(session_id, state)

        yield {"type": "done", "intent": extraction.intent}
```

---

### Phase 3: Implement Each Step

#### Step A: Intent Extractor

```python
# app/agents/intent_extractor.py

class IntentExtractor:
    """Step A: Classify intent and extract structured filters."""

    def __init__(self):
        self.model = get_model()

    async def extract(
        self,
        query: str,
        current_filters: Optional[Filters],
        last_results: Optional[list],
        conversation_history: Optional[list],
    ) -> ExtractionResult:

        # Build context prompt
        prompt = self._build_prompt(query, current_filters, last_results, conversation_history)

        # Single LLM call with structured output
        result = await self.model.generate(
            prompt=prompt,
            response_model=ExtractionResult,  # pydantic model
        )

        return result

    def _build_prompt(self, query, filters, results, history) -> str:
        parts = []

        if history:
            parts.append("CONVERSATION HISTORY:")
            for msg in history[-5:]:  # Last 5 turns
                parts.append(f"{msg['role'].upper()}: {msg['content']}")

        if results:
            parts.append("\nLAST RESULTS:")
            for i, r in enumerate(results[:5], 1):
                parts.append(f"{i}. {r.title}")

        if filters:
            parts.append(f"\nCURRENT FILTERS: {filters.model_dump_json()}")

        parts.append(f"\nUSER QUERY: {query}")

        return "\n".join(parts)
```

#### Step C: Database Query

```python
# app/database/queries.py

async def search_appointments(filters: Filters) -> list[Appointment]:
    """Execute parameterized query based on extracted filters."""

    pool = await get_pool()

    # Build dynamic WHERE clause
    conditions = ["1=1"]  # Always true base
    params = []
    param_idx = 1

    if filters.patient_id:
        conditions.append(f"patient_id = ${param_idx}")
        params.append(filters.patient_id)
        param_idx += 1

    if filters.date_start:
        conditions.append(f"appointment_date >= ${param_idx}")
        params.append(filters.date_start)
        param_idx += 1

    if filters.date_end:
        conditions.append(f"appointment_date <= ${param_idx}")
        params.append(filters.date_end)
        param_idx += 1

    # ... more filters

    query = f"""
        SELECT * FROM appointments
        WHERE {' AND '.join(conditions)}
        ORDER BY appointment_date
        LIMIT 20
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [transform_row(r) for r in rows]
```

#### Step D: Narrator

```python
# app/agents/narrator.py

class NarrativeAgent:
    """Step D: Generate natural language response."""

    SYSTEM_PROMPT = """You are a medical assistant. Be professional, clear, and helpful.
    - Lead with the count: "You have 3 appointments..."
    - Use provided data only - never invent details
    - Be concise but complete
    """

    async def stream(
        self,
        results: list,
        filters: Filters,
        query: str,
    ) -> AsyncGenerator[str, None]:

        # Build data prompt
        prompt = self._format_results(results, filters, query)

        # Stream response
        async for chunk in self.model.stream(
            system=self.SYSTEM_PROMPT,
            user=prompt,
        ):
            yield chunk
```

---

### Phase 4: Add Session State

```python
# app/state.py

@dataclass
class SessionState:
    filters: Filters = field(default_factory=Filters)
    last_results: list = field(default_factory=list)
    history: list = field(default_factory=list)

# In-memory store (use Redis for production)
_sessions: dict[str, SessionState] = {}

def get_session_state(session_id: str) -> SessionState:
    if session_id not in _sessions:
        _sessions[session_id] = SessionState()
    return _sessions[session_id]

def save_session_state(session_id: str, state: SessionState):
    _sessions[session_id] = state
```

---

### Phase 5: Wire Up the API

```python
# app/main.py

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()
pipeline = AssistantPipeline()

@app.post("/chat")
async def chat(request: ChatRequest):
    """SSE streaming chat endpoint."""

    async def stream_generator():
        async for event in pipeline.run_stream(
            query=request.message,
            session_id=request.session_id,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream"
    )
```

---

## Part 4: Migration Checklist

Track your progress converting an existing project:

### Preparation

- [ ] Map current LLM calls and their purposes
- [ ] Identify all extractable entities/filters
- [ ] Document current state management approach
- [ ] List all database tables/APIs involved

### Implementation

- [ ] Create extraction schema (`ExtractionResult`)
- [ ] Build pipeline orchestrator (`Pipeline.run_stream()`)
- [ ] Implement Step A: Intent + Extraction
- [ ] Implement Step B: Entity Resolution (if needed)
- [ ] Implement Step C: Database Query
- [ ] Implement Step D: Narrative Generation
- [ ] Add session state management
- [ ] Update API to use SSE streaming

### Testing

- [ ] Test multi-turn conversations (context preservation)
- [ ] Test each intent type (search, detail, action, chitchat)
- [ ] Test edge cases (no results, errors, ambiguous queries)
- [ ] Verify streaming works in frontend

---

## Part 5: File Structure Template

```
your_project/
├── app/
│   ├── main.py              # FastAPI + /chat endpoint
│   ├── pipeline.py          # Pipeline orchestrator
│   ├── schemas.py           # Pydantic models (filters, results)
│   ├── state.py             # Session state management
│   ├── llm.py               # LLM configuration
│   │
│   ├── agents/
│   │   ├── intent_extractor.py   # Step A
│   │   └── narrator.py           # Step D
│   │
│   └── database/
│       ├── pool.py          # Connection pool
│       ├── queries.py       # SQL queries (Step C)
│       └── transformers.py  # Row → dict conversion
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────┐
│                AGENTIC RAG PIPELINE                 │
├─────────────────────────────────────────────────────┤
│  User Query                                         │
│       │                                             │
│       ▼                                             │
│  [Step A] Intent + Extraction (1 LLM call)          │
│       │                                             │
│       ├── chitchat → [Step D] Response              │
│       ├── detail   → Lookup → [Step D] Response     │
│       │                                             │
│       ▼                                             │
│  [Step B] Entity Resolution (optional)              │
│       │                                             │
│       ▼                                             │
│  [Step C] Database Query (no LLM)                   │
│       │                                             │
│       ▼                                             │
│  [Step D] Narrative Generation (streaming LLM)      │
│       │                                             │
│       ▼                                             │
│  SSE Stream → Frontend                              │
└─────────────────────────────────────────────────────┘

Key Principles:
• Minimize LLM calls (2 max: extract + narrate)
• One extraction call does intent + filters
• Database queries use CODE, not LLM-generated SQL
• Session state enables multi-turn conversations
• SSE streaming provides real-time UX
```
