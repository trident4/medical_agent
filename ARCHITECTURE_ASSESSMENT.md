# Architecture Assessment: Agentic RAG Pipeline

> **Project**: Doctor's Assistant  
> **Assessment Date**: 2026-01-12  
> **Assessed Against**: Agentic RAG Pipeline Pattern (skill.md)

---

## 1. Current Architecture Summary

The Doctor's Assistant is an **AI-powered medical assistant API** built with FastAPI. It provides:

- **Visit Summarization**: AI-generated summaries of patient visits
- **Medical Q&A**: Answer questions about patient data
- **Analytics Queries**: Natural language to SQL for analytics questions
- **Multi-provider AI Fallback**: Supports Gemini, Grok, OpenAI, and Anthropic with automatic failover

### Key Components

| Component         | Implementation                                                                              |
| ----------------- | ------------------------------------------------------------------------------------------- |
| **Entry Point**   | `app/main.py` - FastAPI application                                                         |
| **API Endpoints** | `/api/v1/agents/*` and `/api/v1/analytics/*`                                                |
| **LLM Agents**    | `app/agents/` - `FallbackAgent`, `AnalyticsAgent`, `MedicalQAAgent`, `VisitSummarizerAgent` |
| **Database**      | SQLAlchemy async with PostgreSQL/SQLite support                                             |
| **Streaming**     | SSE via `StreamingResponse`                                                                 |

### Data Flow

```
User Query → FastAPI Endpoint → Specialized Agent → FallbackAgent (LLM) → Response
                                      ↓
                              Database (SQLAlchemy)
```

---

## 2. Assessment Checklist

### Core Pattern Components

| #   | Component                 | Question                                                               | Status     |
| --- | ------------------------- | ---------------------------------------------------------------------- | ---------- |
| 1   | **Intent Classification** | Does the system classify user queries into distinct intents?           | ⚠️ Partial |
| 2   | **Structured Extraction** | Does an LLM extract structured data from natural language?             | ⚠️ Partial |
| 3   | **Step-Based Pipeline**   | Are processing steps separated (extract → resolve → query → generate)? | ❌ No      |
| 4   | **Session State**         | Does the system maintain conversation context across turns?            | ❌ No      |
| 5   | **SSE Streaming**         | Does the UI receive real-time updates during processing?               | ✅ Yes     |

### Step-by-Step Breakdown

| Step                            | What It Should Do                                                  | Status                   |
| ------------------------------- | ------------------------------------------------------------------ | ------------------------ |
| **Step A: Intent + Extraction** | LLM classifies intent AND extracts structured entities in ONE call | ❌ Not implemented       |
| **Step B: Entity Resolution**   | Converts names/locations to IDs, validates entities                | ⚠️ Partial (in QA agent) |
| **Step C: Database Query**      | Executes parameterized SQL/API calls with extracted filters        | ✅ Yes (AnalyticsAgent)  |
| **Step D: Response Generation** | LLM generates natural language from query results                  | ✅ Yes                   |

### Red Flags (Anti-Patterns) Detected

| Anti-Pattern                                                     | Status     | Notes                                                               |
| ---------------------------------------------------------------- | ---------- | ------------------------------------------------------------------- |
| ❌ LLM called for every database query                           | ⚠️         | AnalyticsAgent uses cache → templates → AI hybrid (good!)           |
| ❌ Intent detection and filter extraction are separate LLM calls | ✅ Good    | Not applicable - no intent extraction                               |
| ❌ No session state                                              | ❌ Present | Each query is independent, no conversation context                  |
| ❌ Full response before sending (no streaming)                   | ✅ Good    | SSE streaming implemented                                           |
| ❌ LLM generates SQL directly                                    | ⚠️ Partial | AnalyticsAgent generates SQL, but validates with `_is_safe_query()` |
| ❌ Hardcoded if/else for intent detection                        | ⚠️ Partial | Uses `QueryTemplates` pattern matching, not LLM                     |

---

## 3. Gap Analysis

### What's Working Well ✅

1. **Multi-provider Fallback System**: Excellent `FallbackAgent` implementation with Gemini → Grok → OpenAI → Anthropic chain
2. **SSE Streaming**: Real-time response streaming via `StreamingResponse`
3. **Hybrid Query Approach**: `AnalyticsAgent` uses cache → templates → AI for cost optimization
4. **SQL Safety Validation**: `_is_safe_query()` prevents dangerous SQL execution
5. **Modular Agent Architecture**: Separate agents for different concerns

### What's Missing ❌

1. **Unified Pipeline Orchestrator**

   - No central `Pipeline.run_stream()` that coordinates Steps A→B→C→D
   - Each agent operates independently without a shared flow

2. **Intent Classification**

   - No structured intent detection (search, detail, action, chitchat)
   - Requests go directly to specific endpoints instead of being routed by intent

3. **Structured Filter Extraction**

   - No `ExtractionResult` or `Filters` Pydantic models for entity extraction
   - Natural language → SQL happens in one step without intermediate structured data

4. **Session State Management**

   - No `SessionState` class tracking filters, last results, or conversation history
   - Cannot handle multi-turn conversations like "under $500k" after "farms in Iowa"

5. **Entity Resolution**
   - No lookup from names to database IDs
   - Patient/doctor names are passed directly without resolution

---

## 4. Migration Recommendations

### Priority 1: Add Session State (High Impact, Medium Effort)

```python
# app/state.py
@dataclass
class SessionState:
    filters: Dict[str, Any] = field(default_factory=dict)
    last_results: list = field(default_factory=list)
    history: list = field(default_factory=list)
```

- Enables multi-turn conversations
- Preserves context across queries

### Priority 2: Create Extraction Schema (High Impact, Medium Effort)

```python
# app/schemas/extraction.py
class IntentType(str, Enum):
    SEARCH = "search"           # Find appointments/patients/records
    DETAIL = "detail"           # More info about specific item
    ACTION = "action"           # Schedule, cancel, reschedule
    CHITCHAT = "chitchat"       # Greetings, help, off-topic

class MedicalFilters(BaseModel):
    patient_name: Optional[str] = None
    patient_id: Optional[int] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    doctor_name: Optional[str] = None
    appointment_type: Optional[str] = None
```

### Priority 3: Create Pipeline Orchestrator (High Impact, High Effort)

```python
# app/pipeline.py
class MedicalPipeline:
    async def run_stream(self, query: str, session_id: str):
        # Step A: Extract intent + filters
        # Step B: Resolve entities
        # Step C: Query database
        # Step D: Generate narrative
```

### Priority 4: Entity Resolution Service (Medium Impact, Medium Effort)

```python
# app/services/resolver.py
async def resolve_patient(name: str, db: AsyncSession) -> Optional[int]:
    # Fuzzy match patient name to patient_id
```

---

## 5. Estimated Effort

| Change                                    | Effort   | Impact | Priority |
| ----------------------------------------- | -------- | ------ | -------- |
| Session State Management                  | 2-3 days | High   | 1        |
| Extraction Schema + Intent Classification | 3-4 days | High   | 2        |
| Pipeline Orchestrator                     | 5-7 days | High   | 3        |
| Entity Resolution Service                 | 2-3 days | Medium | 4        |
| Unify Chat Endpoint                       | 1-2 days | Medium | 5        |

**Total Estimated Effort**: 13-19 days

---

## 6. Quick Wins (Can Implement Now)

1. **Add `session_id` to API endpoints** - No breaking changes, prepares for stateful sessions
2. **Create `SessionState` dataclass** - Foundation for multi-turn
3. **Extend `AnalyticsQuery` with intent field** - Backward compatible

---

## 7. Current File Structure vs. Ideal

### Current Structure

```
app/
├── agents/
│   ├── base_agent.py         # FallbackAgent with multi-provider
│   ├── analytics_agent.py    # SQL generation + execution
│   ├── qa_agent.py           # Q&A with context
│   └── summarizer_fallback.py # Visit summarization
├── api/v1/endpoints/
│   ├── agents.py             # Summarize, Q&A endpoints
│   └── analytics.py          # Analytics query endpoints
└── database/
    └── session.py            # SQLAlchemy async session
```

### Recommended Additions

```
app/
├── pipeline.py               # [NEW] Central orchestrator
├── state.py                  # [NEW] Session state management
├── schemas/
│   └── extraction.py         # [NEW] Intent + Filters models
└── services/
    └── resolver.py           # [NEW] Entity resolution
```

---

## Summary

The Doctor's Assistant project has a **solid foundation** with excellent multi-provider fallback, SSE streaming, and a hybrid query optimization strategy. However, it lacks the **central pipeline orchestrator** and **session state management** that define the Agentic RAG Pipeline pattern.

**Recommendation**: Implement session state first (Priority 1) to enable multi-turn conversations, then progressively add intent extraction and the unified pipeline orchestrator.
