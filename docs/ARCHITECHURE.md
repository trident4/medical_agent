# Medical Assistant Project - Architecture & Implementation Guide

A comprehensive guide to understanding how this AI-powered medical assistant is built.

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Technology Stack](#technology-stack)
3. [Core Concepts](#core-concepts)
4. [Request Flow](#request-flow)
5. [Key Design Decisions](#key-design-decisions)
6. [Testing Strategy](#testing-strategy)
7. [HIPAA Compliance](#hipaa-compliance)
8. [Deep Dives](#deep-dives)

---

## High-Level Architecture

This project follows a **layered architecture** pattern for maintainability and scalability:

```
┌─────────────────────────────────────────┐
│         Frontend (React)                │
│    (ReactMarkdown with GFM)             │
└──────────────┬──────────────────────────┘
               │ HTTP/REST API
┌──────────────▼──────────────────────────┐
│         FastAPI Layer                   │
│    (app/api/v1/endpoints/)              │
│  - Routes/Controllers                   │
│  - Request/Response handling            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│       Service Layer                     │
│    (app/services/)                      │
│  - Business logic                       │
│  - Data transformation                  │
│  - Orchestration                        │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
┌──────▼─────┐  ┌─────▼────────┐
│  AI Agents │  │   Database   │
│ (PydanticAI)│  │ (PostgreSQL) │
│            │  │   SQLAlchemy │
└────────────┘  └──────────────┘
```

### Why This Architecture?

- **Separation of Concerns**: Each layer has a single responsibility
- **Testability**: Can test each layer independently
- **Scalability**: Easy to add new features without touching existing code
- **Maintainability**: Clear structure makes code easy to find and modify

---

## Technology Stack

### Backend

| Technology     | Purpose         | Why We Use It                           |
| -------------- | --------------- | --------------------------------------- |
| **FastAPI**    | Web framework   | Modern, fast, automatic API docs        |
| **Pydantic**   | Data validation | Type safety, automatic validation       |
| **SQLAlchemy** | ORM             | Python ↔ SQL translation, async support |
| **PydanticAI** | AI agents       | Structured AI outputs, multi-provider   |
| **PostgreSQL** | Database        | Reliable, HIPAA-compliant, JSON support |
| **Alembic**    | Migrations      | Database version control                |

### AI Providers (with Fallback)

1. **X.AI (Grok-3)** - Primary (fast, cost-effective)
2. **OpenAI (GPT-4)** - Fallback (reliable, high quality)
3. **Anthropic (Claude)** - Final fallback (excellent reasoning)

### Frontend

| Technology        | Purpose                           |
| ----------------- | --------------------------------- |
| **React**         | UI framework                      |
| **ReactMarkdown** | Render AI responses               |
| **remarkGfm**     | GitHub Flavored Markdown (tables) |

---

## Core Concepts

### 1. FastAPI Application Structure

**What is FastAPI?**

- Modern Python web framework built on Starlette (ASGI)
- Automatic OpenAPI documentation
- Type hints for validation
- Async/await support

**Main Application** (`app/main.py`):

```python
from fastapi import FastAPI
from app.api.v1.endpoints import agents, patients, visits

# Create FastAPI app
app = FastAPI(
    title="Medical Assistant API",
    description="AI-powered medical assistant for doctors",
    version="1.0.0"
)

# Include routers (modular organization)
app.include_router(
    agents.router,
    prefix="/api/v1/agents",
    tags=["AI Agents"]
)

app.include_router(
    patients.router,
    prefix="/api/v1/patients",
    tags=["Patients"]
)

app.include_router(
    visits.router,
    prefix="/api/v1/visits",
    tags=["Visits"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Benefits:**

- **Modularity**: Each router handles specific endpoints
- **Versioning**: `/api/v1/` allows future versions without breaking clients
- **Auto-docs**: Visit `/docs` for interactive API documentation
- **Type safety**: Catches errors at development time

---

### 2. Pydantic Models - Data Validation

**What are Pydantic models?**

- Python classes that define data structure
- Automatic validation on instantiation
- Type safety throughout the application
- JSON serialization/deserialization

**Example** (`app/models/visit.py`):

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class VisitCreate(BaseModel):
    """Model for creating a new visit."""
    visit_id: str = Field(..., description="Unique visit identifier")
    patient_id: str = Field(..., description="Patient identifier")
    visit_date: datetime = Field(..., description="Date and time of visit")
    visit_type: str = Field(..., description="Type of visit (routine, emergency, etc.)")
    chief_complaint: Optional[str] = None
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    medications_prescribed: Optional[str] = None
    follow_up_instructions: Optional[str] = None
    doctor_notes: Optional[str] = None
    vital_signs: Optional[str] = None  # JSON string
    lab_results: Optional[str] = None  # JSON string
    duration_minutes: Optional[int] = None

class VisitResponse(BaseModel):
    """Response model for visit data."""
    id: Optional[int] = None
    visit_id: str
    patient_id: str
    visit_date: datetime
    visit_type: str
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    vital_signs: Optional[dict] = None  # Parsed JSON
    lab_results: Optional[list] = None  # Parsed JSON

    class Config:
        from_attributes = True  # Allow ORM mode
```

**What happens when a request comes in:**

```python
# FastAPI automatically validates
@router.post("/visits/", response_model=VisitResponse)
async def create_visit(request: VisitCreate, db: AsyncSession = Depends(get_db)):
    # If request doesn't match VisitCreate schema,
    # FastAPI returns 422 Unprocessable Entity automatically
    # If valid, you get a fully typed, validated object

    visit_service = VisitService(db)
    return await visit_service.create_visit(request)
```

**Benefits:**

- No manual validation code needed
- Type safety catches bugs at development time
- Self-documenting API (OpenAPI schema generation)
- IDE autocomplete and type checking

---

### 3. Service Layer Pattern

**Why have a service layer?**

- **Separation of business logic from HTTP handling**
- **Reusability**: Same service used by multiple endpoints
- **Testability**: Can test business logic without HTTP
- **Single Responsibility**: Each layer does one thing well

**Example** (`app/services/visit_service.py`):

```python
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.visit import Visit, VisitCreate, VisitResponse

class VisitService:
    """Service class for visit-related operations."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def get_visits(
        self,
        skip: int = 0,
        limit: int = 100,
        patient_id: Optional[str] = None,
        visit_type: Optional[str] = None
    ) -> List[VisitResponse]:
        """
        Get visits with optional filtering.

        Business logic:
        1. Build query with filters
        2. Apply pagination
        3. Execute query
        4. Transform to response models
        """
        query = select(Visit)

        # Apply filters (business logic)
        conditions = []
        if patient_id:
            conditions.append(Visit.patient_id == patient_id)
        if visit_type:
            conditions.append(Visit.visit_type == visit_type)

        if conditions:
            query = query.where(and_(*conditions))

        # Pagination
        query = query.order_by(Visit.visit_date.desc()).offset(skip).limit(limit)

        # Execute
        result = await self.db.execute(query)
        visits = result.scalars().all()

        # Transform to response models
        return [self._convert_to_response(visit) for visit in visits]

    def _convert_to_response(self, visit: Visit) -> VisitResponse:
        """Convert database model to response model."""
        visit_dict = visit.__dict__.copy()

        # Parse JSON fields
        if visit.vital_signs:
            visit_dict["vital_signs"] = json.loads(visit.vital_signs)
        if visit.lab_results:
            visit_dict["lab_results"] = json.loads(visit.lab_results)

        return VisitResponse(**visit_dict)
```

**Flow:**

```
API Endpoint → Service → Database
     ↓              ↓         ↓
Validates       Business   Queries
request         logic      database
     ↓              ↓         ↓
Calls          Transforms  Returns
service        data        raw data
     ↓              ↓
Returns       Returns
response      formatted
              data
```

**Benefits:**

- API layer stays thin (just routing and validation)
- Business logic is testable without HTTP
- Same service can be reused by multiple endpoints
- Easy to add caching, logging, or other cross-cutting concerns

---

### 4. PydanticAI Agents - The AI Brain

**What is PydanticAI?**

- Framework for building AI agents with structured outputs
- Built-in retry logic and error handling
- Model-agnostic (works with multiple AI providers)
- Type-safe responses using Pydantic models

**Your Fallback System** (`app/agents/base_agent.py`):

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class FallbackAgent:
    """Base agent with multi-provider fallback support."""

    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.agents = self._setup_agents()

    def _setup_agents(self) -> dict:
        """Setup AI agents in priority order."""
        agents = {}

        # Priority 1: X.AI (Grok-3) - Fast and cost-effective
        if settings.XAI_API_KEY:
            try:
                agents['xai'] = Agent(
                    OpenAIChatModel(
                        'grok-beta',
                        base_url='https://api.x.ai/v1',
                        api_key=settings.XAI_API_KEY
                    ),
                    system_prompt=self.system_prompt
                )
                logger.info("✅ X.AI (Grok-3) agent initialized")
            except Exception as e:
                logger.warning(f"❌ X.AI agent failed to initialize: {e}")

        # Priority 2: OpenAI (GPT-4) - Reliable fallback
        if settings.OPENAI_API_KEY:
            try:
                agents['openai'] = Agent(
                    'openai:gpt-4o',
                    system_prompt=self.system_prompt
                )
                logger.info("✅ OpenAI agent initialized")
            except Exception as e:
                logger.warning(f"❌ OpenAI agent failed to initialize: {e}")

        # Priority 3: Anthropic (Claude) - Final fallback
        if settings.ANTHROPIC_API_KEY:
            try:
                agents['anthropic'] = Agent(
                    'anthropic:claude-3-5-sonnet-20241022',
                    system_prompt=self.system_prompt
                )
                logger.info("✅ Anthropic agent initialized")
            except Exception as e:
                logger.warning(f"❌ Anthropic agent failed to initialize: {e}")

        return agents

    async def run_async(self, user_input: str, message_history: Optional[list] = None) -> str:
        """
        Run agent with automatic fallback.

        Tries each provider in order until one succeeds.
        """
        # Try each provider in priority order
        for provider_name in ['xai', 'openai', 'anthropic']:
            agent = self.agents.get(provider_name)

            if not agent:
                logger.debug(f"⏭️  Skipping {provider_name} (not configured)")
                continue

            try:
                logger.info(f"🤖 Attempting {provider_name}...")

                # Run the agent
                result = await agent.run(user_input, message_history=message_history)

                # Extract the result
                response = self._extract_result(result)

                logger.info(f"✅ {provider_name} succeeded ({len(response)} chars)")
                return response

            except Exception as e:
                logger.warning(f"❌ {provider_name} failed: {str(e)}")
                # Continue to next provider
                continue

        # All providers failed
        raise Exception("All AI providers failed. Please try again later.")

    def _extract_result(self, result) -> str:
        """Extract text from agent result."""
        # Handle different result formats
        if hasattr(result, 'data'):
            return str(result.data)
        elif hasattr(result, 'output'):
            return str(result.output)
        elif hasattr(result, 'content'):
            return str(result.content)
        else:
            return str(result)
```

**How the Fallback Works:**

```python
# Example usage
agent = FallbackAgent(system_prompt="You are a medical assistant...")

# User asks a question
response = await agent.run_async("What is the patient's blood pressure?")

# Internally:
# 1. Try X.AI (Grok-3) first
#    ✅ Success → Return immediately
#    ❌ Failure → Continue to next
#
# 2. Try OpenAI (GPT-4)
#    ✅ Success → Return
#    ❌ Failure → Continue to next
#
# 3. Try Anthropic (Claude)
#    ✅ Success → Return
#    ❌ Failure → Raise exception

# Result: Most reliable response possible
```

**Benefits:**

- **Resilience**: If one provider is down, automatically try the next
- **Cost Optimization**: Use cheaper models first
- **Quality Control**: Can prioritize different models for different tasks
- **No Single Point of Failure**: Multiple AI providers = higher uptime

---

### 5. Database with SQLAlchemy

**What is SQLAlchemy?**

- ORM (Object-Relational Mapping)
- Write Python code instead of SQL
- Async support for better performance
- Type-safe queries

**Database Models** (`app/models/visit.py`):

```python
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base
from datetime import datetime

class Visit(Base):
    """Database model for medical visits."""
    __tablename__ = "visits"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Identifiers
    visit_id = Column(String, unique=True, index=True, nullable=False)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)

    # Visit information
    visit_date = Column(DateTime, nullable=False)
    visit_type = Column(String, nullable=False)
    chief_complaint = Column(Text)
    symptoms = Column(Text)
    diagnosis = Column(Text)
    treatment_plan = Column(Text)
    medications_prescribed = Column(Text)
    follow_up_instructions = Column(Text)
    doctor_notes = Column(Text)

    # JSON stored as text (flexible schema)
    vital_signs = Column(Text)  # JSON string
    lab_results = Column(Text)  # JSON string

    # Metadata
    duration_minutes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="visits")
```

**Why Store JSON as Text?**

```python
# Flexibility for different visit types
vital_signs_general = {
    "blood_pressure_systolic": 120,
    "blood_pressure_diastolic": 80,
    "heart_rate": 75,
    "temperature": 98.6
}

vital_signs_prenatal = {
    "blood_pressure_systolic": 118,
    "blood_pressure_diastolic": 75,
    "heart_rate": 88,
    "temperature": 98.4,
    "fundal_height": 28,  # Prenatal-specific
    "fetal_heart_rate": 145  # Prenatal-specific
}

# Both can be stored in the same column!
visit.vital_signs = json.dumps(vital_signs_general)
# or
visit.vital_signs = json.dumps(vital_signs_prenatal)

# Retrieve and parse
vital_signs_dict = json.loads(visit.vital_signs)
```

**Benefits:**

- Different medical specialties have different measurements
- No need to modify database schema for new fields
- Easy to query and display in tables
- PostgreSQL can still index and query JSON data

**Async Database Operations:**

```python
# Traditional (blocking) approach
def get_visit(visit_id: str):
    visit = db.query(Visit).filter(Visit.visit_id == visit_id).first()
    return visit

# Async (non-blocking) approach
async def get_visit(visit_id: str):
    query = select(Visit).where(Visit.visit_id == visit_id)
    result = await db.execute(query)
    visit = result.scalar_one_or_none()
    return visit
```

**Why Async?**

- While waiting for database, can handle other requests
- Better performance for I/O-bound operations
- Required for PydanticAI agents (they use async)

---

### 6. The Formatting Service - Data Presentation

**Why Format Data on the Backend?**

- **HIPAA Compliance**: Processing happens server-side with proper security
- **Consistency**: Same formatting across all clients
- **Frontend Simplicity**: Just render Markdown, no complex logic
- **Code Reusability**: Same formatting for API responses and AI context

**Your Formatting Service** (`app/services/formatting_service.py`):

```python
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)

class MedicalDataFormatter:
    """Format medical data for display in responses."""

    @staticmethod
    def format_vital_signs_markdown(vital_signs_json: Optional[str]) -> str:
        """
        Convert vital signs JSON to Markdown table.

        Input: '{"blood_pressure_systolic": 120, "heart_rate": 75, ...}'
        Output: Markdown table with status indicators
        """
        if not vital_signs_json:
            return "No vital signs data available."

        try:
            # Parse JSON (handles both string and dict)
            vital_signs = json.loads(vital_signs_json) if isinstance(
                vital_signs_json, str) else vital_signs_json

            # Helper functions for status determination
            def get_bp_status(systolic: int, diastolic: int) -> str:
                """Determine blood pressure status."""
                if systolic < 120 and diastolic < 80:
                    return "✅ Normal"
                elif systolic < 130 and diastolic < 80:
                    return "⚠️ Elevated"
                elif systolic < 140 or diastolic < 90:
                    return "🔶 High Stage 1"
                else:
                    return "🔴 High Stage 2"

            def get_heart_rate_status(hr: int) -> str:
                """Determine heart rate status."""
                if 60 <= hr <= 100:
                    return "✅ Normal"
                elif hr < 60:
                    return "🔵 Low (Bradycardia)"
                else:
                    return "🔴 High (Tachycardia)"

            # Build Markdown table
            table = "\n**Vital Signs:**\n\n"
            table += "| Measurement | Value | Unit | Status |\n"
            table += "|-------------|-------|------|--------|\n"

            # Add blood pressure
            if vital_signs.get('blood_pressure_systolic') and vital_signs.get('blood_pressure_diastolic'):
                systolic = vital_signs['blood_pressure_systolic']
                diastolic = vital_signs['blood_pressure_diastolic']
                status = get_bp_status(systolic, diastolic)
                table += f"| Blood Pressure | {systolic}/{diastolic} | mmHg | {status} |\n"

            # Add heart rate
            if vital_signs.get('heart_rate'):
                hr = vital_signs['heart_rate']
                status = get_heart_rate_status(hr)
                table += f"| Heart Rate | {hr} | bpm | {status} |\n"

            # Add temperature
            if vital_signs.get('temperature'):
                temp = vital_signs['temperature']
                status = "✅ Normal" if 97.0 <= temp <= 99.0 else "🔴 Abnormal"
                table += f"| Temperature | {temp} | °F | {status} |\n"

            return table

        except Exception as e:
            logger.error(f"Error formatting vital signs: {e}")
            return "Error formatting vital signs data."

    @staticmethod
    def format_lab_results_markdown(lab_results_json: Optional[str]) -> str:
        """
        Format lab results JSON to Markdown table.

        Input: '[{"test_name": "HbA1c", "value": "7.8", "status": "high"}, ...]'
        Output: Markdown table with status indicators
        """
        if not lab_results_json:
            return "No lab results available."

        try:
            # Parse JSON
            lab_results = json.loads(lab_results_json) if isinstance(
                lab_results_json, str) else lab_results_json

            # Build Markdown table
            table = "\n**Lab Results:**\n\n"
            table += "| Test Name | Value | Unit | Reference Range | Status |\n"
            table += "|-----------|-------|------|-----------------|--------|\n"

            for lab in lab_results:
                test_name = lab.get("test_name", "Unknown")
                value = lab.get("value", "N/A")
                unit = lab.get("unit", "")
                ref_range = lab.get("reference_range", "N/A")
                status = lab.get("status", "Unknown").lower()

                # Add status emoji
                if status == "normal":
                    status_display = "✅ Normal"
                elif status == "high":
                    status_display = "🔴 High"
                elif status == "low":
                    status_display = "🔵 Low"
                elif status == "pending":
                    status_display = "⏳ Pending"
                else:
                    status_display = status.capitalize()

                table += f"| {test_name} | {value} | {unit} | {ref_range} | {status_display} |\n"

            return table

        except Exception as e:
            logger.error(f"Error formatting lab results: {e}")
            return "Error formatting lab results data."


# Global instance for easy import
medical_formatter = MedicalDataFormatter()
```

**Usage in QA Agent:**

```python
from app.services.formatting_service import medical_formatter

class MedicalQAAgent:
    async def answer_question(self, question: str, visits: List[VisitResponse]) -> str:
        # Build context with formatted tables
        context = "Patient Information:\n\n"

        for visit in visits:
            # Add formatted vital signs
            if visit.vital_signs:
                context += medical_formatter.format_vital_signs_markdown(
                    json.dumps(visit.vital_signs)
                )

            # Add formatted lab results
            if visit.lab_results:
                context += medical_formatter.format_lab_results_markdown(
                    json.dumps(visit.lab_results)
                )

        # AI sees the formatted tables in context
        # AI includes tables in response
        response = await self.agent.run_async(f"Context:\n{context}\n\nQuestion: {question}")

        return response
```

**Frontend Rendering:**

```jsx
// Frontend (React)
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function ChatMessage({ message }) {
  return (
    <div className="message">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {message.answer}
      </ReactMarkdown>
    </div>
  );
}
```

**What the User Sees:**

```markdown
Based on the visit from 2025-10-27, here are the vital signs:

**Vital Signs:**

| Measurement    | Value  | Unit | Status    |
| -------------- | ------ | ---- | --------- |
| Blood Pressure | 118/75 | mmHg | ✅ Normal |
| Heart Rate     | 88     | bpm  | ✅ Normal |
| Temperature    | 98.4   | °F   | ✅ Normal |

All vital signs are within normal ranges.
```

**Rendered as:**

<table>
<thead>
<tr>
<th>Measurement</th>
<th>Value</th>
<th>Unit</th>
<th>Status</th>
</tr>
</thead>
<tbody>
<tr>
<td>Blood Pressure</td>
<td>118/75</td>
<td>mmHg</td>
<td>✅ Normal</td>
</tr>
<tr>
<td>Heart Rate</td>
<td>88</td>
<td>bpm</td>
<td>✅ Normal</td>
</tr>
<tr>
<td>Temperature</td>
<td>98.4</td>
<td>°F</td>
<td>✅ Normal</td>
</tr>
</tbody>
</table>

**Benefits:**

- **HIPAA Compliant**: All processing server-side
- **Clean & Professional**: Proper table formatting
- **Visual Indicators**: Emojis provide quick status assessment
- **No Frontend Changes**: Works with existing ReactMarkdown
- **Copy/Paste Ready**: Doctors can copy tables to other documents

---

## Request Flow

Let's trace a complete request from start to finish:

**User Question**: "What were the patient's vital signs from the last visit?"

```
1. User Types Question in Frontend
   ↓
   Frontend React Component

2. Frontend Sends HTTP POST Request
   ↓
   POST /api/v1/agents/ask
   Body: {
     "question": "What were the patient's vital signs?",
     "patient_id": "PAT001",
     "context_type": "recent"
   }

3. FastAPI Receives Request
   ↓
   @router.post("/ask", response_model=QuestionAnswerResponse)
   async def ask_question_endpoint(request: QuestionAnswerRequest, ...):

4. Pydantic Validates Request
   ↓
   QuestionAnswerRequest.model_validate(request_body)
   - Ensures all required fields present
   - Type checks all fields
   - Returns 422 if invalid

5. Endpoint Calls PatientService
   ↓
   patient_service = PatientService(db)
   patient = await patient_service.get_patient_by_id(request.patient_id)

6. Service Queries Database
   ↓
   query = select(Patient).where(Patient.patient_id == patient_id)
   result = await db.execute(query)
   patient = result.scalar_one_or_none()

7. Service Gets Recent Visits
   ↓
   visit_service = VisitService(db)
   visits = await visit_service.get_patient_visits(patient.id, limit=5)

8. Format Medical Data
   ↓
   for visit in visits:
       if visit.vital_signs:
           formatted_vitals = medical_formatter.format_vital_signs_markdown(
               json.dumps(visit.vital_signs)
           )

9. Build AI Context
   ↓
   context = f"""
   Patient: {patient.name}

   Recent Visit Information:
   {formatted_vitals}
   """

10. Call Medical QA Agent
    ↓
    medical_qa_agent = MedicalQAAgent()
    answer = await medical_qa_agent.answer_question(
        question=request.question,
        patients=[patient],
        visits=visits
    )

11. Agent Tries X.AI (Grok-3) First
    ↓
    try:
        result = await xai_agent.run(user_input, message_history=[])
        return result
    except Exception:
        # Fallback to OpenAI

12. X.AI Processes Request
    ↓
    - Receives context with formatted Markdown tables
    - Generates response including the tables
    - Returns structured output

13. Agent Returns Response
    ↓
    response = """
    Based on the visit from 2025-10-27:

    **Vital Signs:**
    | Measurement | Value | Unit | Status |
    |-------------|-------|------|--------|
    | Blood Pressure | 118/75 | mmHg | ✅ Normal |
    ...
    """

14. Endpoint Builds Response
    ↓
    return QuestionAnswerResponse(
        answer=answer,
        sources=[{"type": "visit", "id": visit.visit_id}],
        confidence=0.95
    )

15. FastAPI Serializes Response
    ↓
    JSON Response:
    {
      "answer": "Based on the visit...\n\n**Vital Signs:**...",
      "sources": [...],
      "confidence": 0.95
    }

16. Frontend Receives Response
    ↓
    const response = await fetch('/api/v1/agents/ask', {...});
    const data = await response.json();

17. React Renders Markdown
    ↓
    <ReactMarkdown remarkPlugins={[remarkGfm]}>
      {data.answer}
    </ReactMarkdown>

18. User Sees Formatted Table
    ↓
    Beautiful HTML table with vital signs and status indicators
```

**Total Time**: ~2-5 seconds

- Database query: ~50ms
- AI processing: ~2-4 seconds
- Data formatting: ~10ms
- HTTP overhead: ~50ms

---

## Key Design Decisions

### 1. Why Async/Await?

**Without Async (Blocking):**

```python
def get_visits(patient_id: str):
    # Server blocks here waiting for database
    visits = db.query(Visit).filter(Visit.patient_id == patient_id).all()
    return visits

# Problem: While waiting for DB, can't handle other requests
# If DB takes 100ms, server can handle at most 10 requests/second
```

**With Async (Non-blocking):**

```python
async def get_visits(patient_id: str):
    # Server yields control while waiting for database
    query = select(Visit).where(Visit.patient_id == patient_id)
    result = await db.execute(query)
    visits = result.scalars().all()
    return visits

# Benefit: While waiting for DB, can handle other requests
# Can handle 100+ concurrent requests
```

**Real-World Impact:**

```python
# Multiple concurrent requests
async def handle_requests():
    # All three happen concurrently
    patient = await get_patient("PAT001")  # 50ms
    visits = await get_visits("PAT001")     # 50ms
    ai_response = await agent.run("...")    # 2000ms

    # Total time: ~2000ms (not 2100ms)
    # Without async: ~2100ms (sequential)
```

**When to Use Async:**

- ✅ Database queries
- ✅ API calls (OpenAI, X.AI)
- ✅ File I/O
- ✅ Network requests
- ❌ CPU-bound tasks (use multiprocessing instead)

---

### 2. Why Dependency Injection?

**Without Dependency Injection:**

```python
# Global database connection (bad)
db = create_engine("postgresql://...")

@router.post("/visits/")
async def create_visit(request: VisitCreate):
    # Uses global db (hard to test, not isolated)
    db.add(Visit(**request.dict()))
    db.commit()
```

**Problems:**

- Hard to test (can't mock database)
- No connection pooling
- Not thread-safe
- Can't have multiple databases

**With Dependency Injection:**

```python
# Dependency function
async def get_db():
    """Get database session."""
    async with AsyncSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# Endpoint uses dependency
@router.post("/visits/")
async def create_visit(
    request: VisitCreate,
    db: AsyncSession = Depends(get_db)  # ← Injected!
):
    # Uses injected db (testable, isolated)
    service = VisitService(db)
    return await service.create_visit(request)
```

**Benefits:**

- ✅ Easy to test (inject mock database)
- ✅ Automatic connection management
- ✅ Connection pooling handled by framework
- ✅ Each request gets isolated session

**Testing Example:**

```python
# Test with mock database
async def test_create_visit():
    # Create test database session
    async with AsyncSession(test_engine) as db:
        # Inject test database
        service = VisitService(db)

        # Test without touching production database
        visit = await service.create_visit(test_visit_data)
        assert visit.visit_id == "VIS001"
```

---

### 3. Why JSON in Database?

**Traditional Approach (Rigid Schema):**

```sql
CREATE TABLE visits (
    id SERIAL PRIMARY KEY,
    blood_pressure_systolic INT,
    blood_pressure_diastolic INT,
    heart_rate INT,
    temperature FLOAT,
    ...
);

-- Problem: What about prenatal visits?
-- Need fundal_height, fetal_heart_rate
-- Would need to add columns or create separate table
```

**JSON Approach (Flexible Schema):**

```sql
CREATE TABLE visits (
    id SERIAL PRIMARY KEY,
    vital_signs TEXT  -- JSON stored as text
);

-- Insert general visit
INSERT INTO visits (vital_signs) VALUES (
    '{"blood_pressure_systolic": 120, "heart_rate": 75}'
);

-- Insert prenatal visit with custom fields
INSERT INTO visits (vital_signs) VALUES (
    '{"blood_pressure_systolic": 118, "fundal_height": 28, "fetal_heart_rate": 145}'
);
```

**Benefits:**

- ✅ Different specialties can add custom fields
- ✅ No schema migrations needed for new measurements
- ✅ Still queryable (PostgreSQL JSON functions)
- ✅ Easy to validate with Pydantic on read/write

**Trade-offs:**

- ❌ Slightly slower than native columns
- ❌ Can't enforce schema at database level
- ✅ But Pydantic validates on application level

**When to Use JSON:**

- ✅ Flexible, varying structure (vital signs, lab results)
- ✅ Nested data
- ✅ Schema evolution expected
- ❌ Need complex database queries on nested fields
- ❌ Need database-level constraints

---

### 4. Why Markdown for Formatting?

**Alternative 1: Send HTML**

```python
# Backend sends HTML
return "<table><tr><td>Blood Pressure</td><td>120/80</td></tr></table>"

# Problems:
# - Security risk (XSS attacks)
# - Not readable in raw form
# - Hard to sanitize
# - Frontend loses control over styling
```

**Alternative 2: Send Structured Data**

```python
# Backend sends structured data
return {
    "vital_signs": [
        {"measurement": "BP", "value": "120/80", "status": "normal"}
    ]
}

# Problems:
# - Frontend needs complex table rendering logic
# - Duplication if multiple clients (web, mobile)
# - Each client implements formatting differently
```

**Markdown Approach (Best of Both Worlds):**

```python
# Backend sends Markdown
return """
| Measurement | Value | Status |
|-------------|-------|--------|
| Blood Pressure | 120/80 | ✅ Normal |
"""

# Benefits:
# ✅ Human-readable in raw form
# ✅ No XSS risk (ReactMarkdown sanitizes)
# ✅ Frontend just renders (remarkGfm handles tables)
# ✅ Works across all clients
# ✅ Copy-paste friendly for doctors
# ✅ GitHub Flavored Markdown = universal standard
```

**Example Output:**

```markdown
**Vital Signs:**

| Measurement    | Value  | Unit | Status    |
| -------------- | ------ | ---- | --------- |
| Blood Pressure | 118/75 | mmHg | ✅ Normal |
| Heart Rate     | 88     | bpm  | ✅ Normal |
```

Renders as beautiful HTML table with:

- Proper borders
- Aligned columns
- Responsive design
- Styled with CSS

---

## Testing Strategy

Your project uses a comprehensive testing pyramid:

```
           /\
          /  \
         /    \  End-to-End Tests
        /______\  (Full user flows)
       /        \
      /          \ Integration Tests
     /            \  (API tests with real DB)
    /______________\
   /                \ Unit Tests
  /                  \  (Individual functions)
 /____________________\
```

### Unit Tests

**Test individual functions in isolation:**

```python
# tests/unit/test_formatting_service.py
import pytest
from app.services.formatting_service import medical_formatter

def test_format_vital_signs_normal():
    """Test vital signs formatting with normal values."""
    vital_signs = '{"blood_pressure_systolic": 120, "blood_pressure_diastolic": 80, "heart_rate": 75}'

    result = medical_formatter.format_vital_signs_markdown(vital_signs)

    assert "Blood Pressure" in result
    assert "120/80" in result
    assert "✅ Normal" in result

def test_format_vital_signs_high_bp():
    """Test vital signs formatting with high blood pressure."""
    vital_signs = '{"blood_pressure_systolic": 150, "blood_pressure_diastolic": 95}'

    result = medical_formatter.format_vital_signs_markdown(vital_signs)

    assert "🔴 High" in result or "🔶 High" in result

def test_format_vital_signs_empty():
    """Test handling of empty vital signs."""
    result = medical_formatter.format_vital_signs_markdown(None)

    assert "No vital signs" in result
```

### Integration Tests

**Test API endpoints with real database:**

```python
# tests/test_agents_api_fallback.py
import requests

BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

class TestAgentsAPIWithFallback:
    """Integration tests for agents API."""

    def test_01_create_test_patient(self):
        """Test patient creation."""
        patient_data = {
            "patient_id": "PAT001",
            "name": "John Doe",
            "date_of_birth": "1985-03-15",
            "gender": "male"
        }

        response = requests.post(f"{API_BASE}/patients/", json=patient_data)

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["patient_id"] == "PAT001"

    def test_03_ask_endpoint_basic_question(self):
        """Test medical Q&A with patient context."""
        request_data = {
            "question": "What was this patient's last diagnosis?",
            "patient_id": "PAT001",
            "context_type": "recent"
        }

        response = requests.post(f"{API_BASE}/agents/ask", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert len(data["answer"]) > 0
        print(f"\nAI Answer: {data['answer'][:200]}...")

    def test_08_fallback_system_verification(self):
        """Test that fallback system works."""
        # Test general medical question (no patient context)
        request_data = {
            "question": "What are the key differences between Type 1 and Type 2 diabetes?",
            "context_type": "none"
        }

        response = requests.post(f"{API_BASE}/agents/ask", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify AI response quality
        answer = data["answer"].lower()
        assert "type 1" in answer or "type 2" in answer
        assert "diabetes" in answer
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_agents_api_fallback.py -v

# Run specific test class
pytest tests/test_agents_api_fallback.py::TestAgentsAPIWithFallback -v

# Run specific test method
pytest tests/test_agents_api_fallback.py::TestAgentsAPIWithFallback::test_03_ask_endpoint_basic_question -v

# Run with output (see print statements)
pytest tests/ -v -s

# Run with coverage report
pytest tests/ --cov=app --cov-report=html
```

---

## HIPAA Compliance

Your project follows medical data best practices for HIPAA compliance:

### 1. No Sensitive Data in Logs

```python
# ❌ BAD - Never log API keys or patient data
logger.info(f"Using API key: {settings.OPENAI_API_KEY}")
logger.info(f"Patient data: {patient.dict()}")

# ✅ GOOD - Log without sensitive info
logger.info("OpenAI API initialized successfully")
logger.info(f"Processing request for patient ID: {patient.patient_id}")
```

### 2. Secure Data Handling

```python
# All medical data processing happens server-side
formatted_data = medical_formatter.format_vital_signs(visit.vital_signs)

# Frontend only receives:
# - Formatted, sanitized output
# - No raw medical data
# - No internal database IDs
```

### 3. Type Safety Prevents Data Leaks

```python
class PatientResponse(BaseModel):
    """Public API response - only safe fields."""
    patient_id: str  # External ID (not internal DB ID)
    name: str
    date_of_birth: date

    # Never expose:
    # - Internal database IDs
    # - Raw medical records
    # - Audit trails
    # - System metadata

class Patient(Base):
    """Database model - includes sensitive fields."""
    id: int  # Internal ID (never exposed)
    patient_id: str  # External ID (safe to expose)
    name: str
    ssn: str  # NEVER exposed in API

    # Clear separation between DB and API models
```

### 4. Audit Trails

```python
class Visit(Base):
    """All database models include audit fields."""
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)  # User who created

    # Track all data access
```

### 5. Secure API Keys

```python
# .env file (never committed to git)
OPENAI_API_KEY=sk-...
XAI_API_KEY=xai-...
DATABASE_URL=postgresql://...

# .gitignore includes
.env
.env.*
*.key
```

### 6. Data Validation

```python
# Pydantic validates all inputs
class VisitCreate(BaseModel):
    visit_id: str = Field(..., regex=r'^VIS\d{6}$')  # Enforce format
    patient_id: str = Field(..., regex=r'^PAT\d{6}$')
    visit_date: datetime = Field(...)

    @validator('visit_date')
    def validate_visit_date(cls, v):
        """Ensure visit date is not in the future."""
        if v > datetime.now():
            raise ValueError("Visit date cannot be in the future")
        return v
```

---

## Deep Dives

### How AI Prompt Engineering Works

**System Prompt (Sets AI Behavior):**

```python
system_prompt = """
You are a medical assistant AI specializing in summarizing patient visit data for healthcare professionals.

Your role is to:
1. Create concise, accurate summaries of patient visits
2. Highlight key medical findings and diagnoses
3. Identify important follow-up actions
4. Provide actionable recommendations
5. Maintain HIPAA compliance and medical confidentiality

Guidelines:
- Use clear, professional medical terminology
- Focus on clinically relevant information
- Highlight any concerning symptoms or findings
- Suggest appropriate follow-up care when needed
- Be objective and evidence-based
- Include confidence assessment for your analysis

Always structure your response with:
- A comprehensive summary paragraph
- Key clinical points (3-5 bullet points)
- Specific recommendations for care
- Assessment of follow-up necessity
- Confidence score (0.0-1.0)

When presenting vital signs or lab results, include them in Markdown tables for clarity.
"""
```

**Context Building:**

```python
async def answer_question(
    self,
    question: str,
    patients: List[PatientResponse],
    visits: List[VisitResponse]
) -> str:
    """Build rich context for AI."""

    # Start with patient information
    context_parts = []

    if patients:
        context_parts.append("Patient Information:")
        for patient in patients:
            context_parts.append(f"- Name: {patient.name}")
            context_parts.append(f"- Age: {calculate_age(patient.date_of_birth)}")
            context_parts.append(f"- Gender: {patient.gender}")

    # Add visit information with formatted tables
    if visits:
        context_parts.append("\nRecent Visit Information:")
        for visit in visits[:5]:  # Last 5 visits
            context_parts.append(f"\n**Visit {visit.visit_id} ({visit.visit_date}):**")
            context_parts.append(f"- Chief Complaint: {visit.chief_complaint}")
            context_parts.append(f"- Diagnosis: {visit.diagnosis}")

            # Add formatted vital signs table
            if visit.vital_signs:
                vital_signs_table = medical_formatter.format_vital_signs_markdown(
                    json.dumps(visit.vital_signs)
                )
                context_parts.append(vital_signs_table)

            # Add formatted lab results table
            if visit.lab_results:
                lab_results_table = medical_formatter.format_lab_results_markdown(
                    json.dumps(visit.lab_results)
                )
                context_parts.append(lab_results_table)

    # Combine into full context
    context = "\n".join(context_parts)

    # Send to AI with question
    user_prompt = f"""
Context:
{context}

Question: {question}

Please provide a detailed answer based on the patient's medical history above.
Include relevant data from the vital signs and lab results tables in your response.
"""

    # AI sees the full context with formatted tables
    response = await self.agent.run_async(user_prompt)

    return response
```

**Why This Works:**

- ✅ AI sees structured data (tables are clear)
- ✅ AI can reference specific values
- ✅ AI includes tables in response (already formatted)
- ✅ Context is comprehensive but concise

---

### How Database Migrations Work (Alembic)

**Initial Setup:**

```bash
# Initialize Alembic
alembic init alembic

# Configure alembic.ini
sqlalchemy.url = postgresql://user:pass@localhost/dbname
```

**Create Migration:**

```bash
# Auto-generate migration from models
alembic revision --autogenerate -m "Add visits table"

# Creates file: alembic/versions/001_add_visits_table.py
```

**Migration File:**

```python
# alembic/versions/001_add_visits_table.py
def upgrade():
    """Upgrade database schema."""
    op.create_table(
        'visits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('visit_id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('visit_date', sa.DateTime(), nullable=False),
        sa.Column('vital_signs', sa.Text(), nullable=True),
        sa.Column('lab_results', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_visits_visit_id', 'visits', ['visit_id'], unique=True)

def downgrade():
    """Rollback database schema."""
    op.drop_index('ix_visits_visit_id', table_name='visits')
    op.drop_table('visits')
```

**Apply Migration:**

```bash
# Upgrade to latest version
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Check current version
alembic current

# View history
alembic history
```

---

### How to Add a New Endpoint

**Step-by-Step Guide:**

**1. Define Pydantic Models:**

```python
# app/models/prescription.py
from pydantic import BaseModel
from datetime import datetime

class PrescriptionCreate(BaseModel):
    """Model for creating a prescription."""
    medication_name: str
    dosage: str
    frequency: str
    duration_days: int
    patient_id: str

class PrescriptionResponse(BaseModel):
    """Response model for prescription."""
    id: int
    prescription_id: str
    medication_name: str
    dosage: str
    frequency: str
    patient_id: str
    created_at: datetime
```

**2. Create Database Model:**

```python
# app/models/prescription.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database.base import Base

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(String, unique=True, index=True)
    medication_name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    duration_days = Column(Integer)
    patient_id = Column(String, ForeignKey("patients.patient_id"))
    created_at = Column(DateTime, default=datetime.utcnow)
```

**3. Create Service:**

```python
# app/services/prescription_service.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.prescription import Prescription, PrescriptionCreate, PrescriptionResponse

class PrescriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_prescription(self, prescription: PrescriptionCreate) -> PrescriptionResponse:
        """Create a new prescription."""
        db_prescription = Prescription(**prescription.model_dump())
        self.db.add(db_prescription)
        await self.db.commit()
        await self.db.refresh(db_prescription)
        return PrescriptionResponse.model_validate(db_prescription)

    async def get_prescriptions(self, patient_id: str) -> List[PrescriptionResponse]:
        """Get all prescriptions for a patient."""
        query = select(Prescription).where(Prescription.patient_id == patient_id)
        result = await self.db.execute(query)
        prescriptions = result.scalars().all()
        return [PrescriptionResponse.model_validate(p) for p in prescriptions]
```

**4. Create API Endpoint:**

```python
# app/api/v1/endpoints/prescriptions.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.prescription_service import PrescriptionService
from app.models.prescription import PrescriptionCreate, PrescriptionResponse

router = APIRouter()

@router.post("/", response_model=PrescriptionResponse)
async def create_prescription(
    request: PrescriptionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new prescription."""
    service = PrescriptionService(db)
    return await service.create_prescription(request)

@router.get("/{patient_id}", response_model=List[PrescriptionResponse])
async def get_prescriptions(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all prescriptions for a patient."""
    service = PrescriptionService(db)
    return await service.get_prescriptions(patient_id)
```

**5. Register Router:**

```python
# app/main.py
from app.api.v1.endpoints import prescriptions

app.include_router(
    prescriptions.router,
    prefix="/api/v1/prescriptions",
    tags=["Prescriptions"]
)
```

**6. Create Migration:**

```bash
alembic revision --autogenerate -m "Add prescriptions table"
alembic upgrade head
```

**7. Test:**

```bash
# Start server
uvicorn app.main:app --reload

# Visit http://localhost:8000/docs
# Test the new /api/v1/prescriptions/ endpoints
```

---

### How to Deploy to Production

**1. Environment Setup:**

```bash
# production.env
DATABASE_URL=postgresql://prod_user:prod_pass@prod_db:5432/medical_assistant
OPENAI_API_KEY=sk-prod-...
XAI_API_KEY=xai-prod-...
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**2. Docker Setup:**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Run migrations and start server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**3. Docker Compose:**

```yaml
# docker-compose.yml
version: "3.8"

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: medical_assistant
      POSTGRES_USER: prod_user
      POSTGRES_PASSWORD: prod_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://prod_user:prod_pass@db:5432/medical_assistant
    depends_on:
      - db
    env_file:
      - production.env

volumes:
  postgres_data:
```

**4. Deploy:**

```bash
# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f app

# Run migrations
docker-compose exec app alembic upgrade head
```

**5. Monitoring:**

```python
# Add health check endpoint
@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check with database connectivity test."""
    try:
        # Test database connection
        await db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database unavailable")
```

---

## Summary

### Key Takeaways

1. **FastAPI** = Web server that handles HTTP requests
2. **Pydantic** = Data validation that ensures data correctness
3. **SQLAlchemy** = Database ORM that translates Python ↔ SQL
4. **PydanticAI** = AI agent framework with multi-provider fallback
5. **Service Layer** = Business logic that keeps code organized
6. **Markdown Formatting** = Display layer for beautiful tables

### The Magic Formula

```
HTTP Request → Validate → Service Logic → AI/Database → Format → Response
```

### Architecture Benefits

- ✅ **Modular**: Easy to modify individual components
- ✅ **Testable**: Each layer can be tested independently
- ✅ **Scalable**: Can handle growth without major rewrites
- ✅ **Maintainable**: Clear structure makes code easy to find
- ✅ **Type-Safe**: Catches errors at development time
- ✅ **Resilient**: Fallback system handles failures gracefully
- ✅ **Secure**: HIPAA-compliant data handling throughout

### Next Steps

To deepen your understanding:

1. **Read the code**: Start with `app/main.py` and follow the flow
2. **Run the tests**: See how each component is tested
3. **Make small changes**: Add a new field or endpoint
4. **Read the logs**: Understand what happens during requests
5. **Experiment**: Break things and see what happens (in development!)

Remember: This architecture may seem complex at first, but each layer serves a specific purpose. Once you understand the flow, you'll see how elegant and maintainable it is.

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PydanticAI Documentation](https://ai.pydantic.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Python Async/Await](https://docs.python.org/3/library/asyncio.html)

---

_This guide was created to help you understand the architecture and implementation of the Medical Assistant project. Keep it handy for reference as you continue developing!_
