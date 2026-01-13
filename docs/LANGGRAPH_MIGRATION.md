# LangGraph Migration Walkthrough

> **Date**: January 13, 2026  
> **Summary**: Migrated the Doctor's Assistant chat system to an Agentic RAG Pipeline using LangGraph for conversation state management and multi-step query processing.

---

## Architecture Overview

```mermaid
graph TD
    subgraph "Client"
        A[User Query]
    end

    subgraph "API Layer"
        B["/api/v1/chat/"]
        C["/api/v1/chat/stream"]
    end

    subgraph "LangGraph Pipeline"
        D["extract_intent"]
        E["resolve_entities"]
        F["query_database"]
        G["generate_response"]
    end

    subgraph "Data Layer"
        H[(PostgreSQL)]
        I[Checkpoint Tables]
    end

    subgraph "AI Providers"
        J["Qwen (Local)"]
        K["Gemini"]
        L["OpenAI"]
        M["Anthropic"]
    end

    A --> B
    A --> C
    B --> D
    C --> D
    D -->|"search/detail/summarize"| E
    D -->|"analytics"| F
    D -->|"chitchat/error"| G
    E --> F
    F --> G
    G --> A

    D --> J
    G --> J
    J -.->|fallback| K
    K -.->|fallback| L
    L -.->|fallback| M

    E --> H
    F --> H
    D --> I
```

---

## Pipeline Flow

```mermaid
flowchart LR
    START([User Query]) --> A[Extract Intent]
    A -->|search/detail/summarize| B[Resolve Entities]
    A -->|analytics| C[Query Database]
    A -->|chitchat/error| D[Generate Response]
    B --> C
    C --> D
    D --> END([Response])

    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#e8f5e9
    style D fill:#fce4ec
```

---

## What Changed

### New Files Created

| File                           | Purpose                                                                               |
| ------------------------------ | ------------------------------------------------------------------------------------- |
| `app/graph/__init__.py`        | Package init                                                                          |
| `app/graph/state.py`           | ConversationState TypedDict, intent constants                                         |
| `app/graph/nodes.py`           | 4 node functions: extract_intent, resolve_entities, query_database, generate_response |
| `app/graph/pipeline.py`        | StateGraph builder, routing logic, PostgreSQL checkpointer                            |
| `app/api/v1/endpoints/chat.py` | New `/chat/` and `/chat/stream` endpoints                                             |

### Modified Files

| File                       | Change                                                  |
| -------------------------- | ------------------------------------------------------- |
| `requirements.txt`         | Added langgraph, langgraph-checkpoint-postgres, psycopg |
| `app/api/v1/api.py`        | Registered chat router                                  |
| `app/config.py`            | Added LangSmith settings, QWEN_BASE_URL                 |
| `app/main.py`              | Added LangSmith initialization                          |
| `app/agents/base_agent.py` | Added local Qwen model support                          |

### Test Files Created

| File                           | Coverage                          |
| ------------------------------ | --------------------------------- |
| `tests/test_graph_state.py`    | State schema, intent constants    |
| `tests/test_graph_pipeline.py` | Routing logic, graph construction |
| `tests/test_graph_nodes.py`    | Individual node functions         |
| `tests/test_chat_api.py`       | API authentication, validation    |

---

## Intent Routing

| Intent      | Route                  | Nodes Executed                                                         |
| ----------- | ---------------------- | ---------------------------------------------------------------------- |
| `chitchat`  | Skip to response       | extract_intent → generate_response                                     |
| `analytics` | Skip entity resolution | extract_intent → query_database → generate_response                    |
| `search`    | Full pipeline          | extract_intent → resolve_entities → query_database → generate_response |
| `detail`    | Full pipeline          | extract_intent → resolve_entities → query_database → generate_response |
| `summarize` | Full pipeline          | extract_intent → resolve_entities → query_database → generate_response |
| `error`     | Graceful degradation   | → generate_response                                                    |

---

## Configuration

Add to `.env`:

```bash
# PostgreSQL (required for app and checkpointer)
DATABASE_URL=postgresql://dev_user:password@localhost:5432/doctors_assistant

# Local Qwen Model (optional)
QWEN_API_KEY=dummy
QWEN_BASE_URL=http://localhost:11434/v1

# LangSmith Observability (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-key
LANGCHAIN_PROJECT=doctors-assistant
```

---

## API Endpoints

### POST `/api/v1/chat/`

Non-streaming chat with full pipeline response.

**Request:**

```json
{ "message": "Show visits for Michael Brown", "session_id": "user-123" }
```

**Response:**

```json
{ "response": "Found 3 visits...", "intent": "search", "results_count": 3 }
```

### POST `/api/v1/chat/stream`

SSE streaming with node-level progress updates.

---

## Running Tests

```bash
# Run all LangGraph tests
pytest tests/test_graph_*.py tests/test_chat_api.py -v

# Run with coverage
pytest tests/test_graph_*.py tests/test_chat_api.py --cov=app.graph
```

---

## Key Design Decisions

1. **TypedDict over Pydantic** - LangGraph requires TypedDict for state serialization
2. **DB via config, not state** - Database sessions passed via `config["configurable"]["db"]` to avoid serialization issues
3. **String intents over Enums** - Prevents JSON serialization errors
4. **Autocommit for setup** - Required for `CREATE INDEX CONCURRENTLY` in PostgreSQL
5. **Fallback agent priority** - qwen → gemini → xai → openai → anthropic
