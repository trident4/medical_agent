"""
LangGraph pipeline nodes for the Medical Assistant.

Each node is an async function that:
1. Takes state and config as parameters
2. Returns a dict with state updates
3. Gets database session from config["configurable"]["db"], NOT from state
"""

from typing import Any
from langgraph.types import RunnableConfig
from app.graph.state import (
    ConversationState,
    INTENT_SEARCH,
    INTENT_DETAIL,
    INTENT_SUMMARIZE,
    INTENT_ANALYTICS,
    INTENT_CHITCHAT,
    VALID_INTENTS,
)
from app.agents.base_agent import FallbackAgent
from app.agents.analytics_agent import analytics_agent
import json
import logging

logger = logging.getLogger(__name__)

# Agents initialized once (singleton pattern)
intent_agent = FallbackAgent(
    system_prompt="""
You are an intent classifier for a medical assistant.
Given a user query, extract:
1. intent: One of "search", "detail", "summarize", "analytics", "chitchat"
2. filters: Relevant filters like patient_name, date_start, date_end, diagnosis
3. entity_to_resolve: Any name that needs to be looked up (e.g., "John Smith")

Return ONLY valid JSON:
{"intent": "search", "filters": {"patient_name": "..."}, "entity_to_resolve": null}

Examples:
- "Show me patients with diabetes" -> {"intent": "search", "filters": {"diagnosis": "diabetes"}, "entity_to_resolve": null}
- "What visits did John Smith have?" -> {"intent": "search", "filters": {}, "entity_to_resolve": "John Smith"}
- "How many patients visited last month?" -> {"intent": "analytics", "filters": {}, "entity_to_resolve": null}
- "Hello" -> {"intent": "chitchat", "filters": {}, "entity_to_resolve": null}
"""
)

narrator_agent = FallbackAgent(
    system_prompt="""
You are a helpful medical assistant for doctors.
Generate professional, concise responses based on query results.
Always cite specific data from results when available.
Be clear and actionable in your responses.
"""
)


async def extract_intent(state: ConversationState, config: RunnableConfig) -> dict:
    """
    Step A: Intent + Filter extraction.

    Extracts the user's intent and any filters from their query.
    Returns structured data for routing and downstream processing.
    """
    try:
        recent_messages = state.get("messages", [])[-5:]
        context = f"Query: {state['query']}\nRecent conversation: {recent_messages}"

        result = await intent_agent.run_async(context)

        # Parse JSON response
        parsed = json.loads(result)
        intent = parsed.get("intent", INTENT_CHITCHAT)

        # Validate intent
        if intent not in VALID_INTENTS:
            logger.warning(
                f"Invalid intent '{intent}' returned, defaulting to chitchat"
            )
            intent = INTENT_CHITCHAT

        logger.info(f"Extracted intent: {intent}, filters: {parsed.get('filters', {})}")

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
    """
    Step B: Resolve names to database IDs.

    Performs fuzzy matching on patient names to get their database IDs.
    """
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
            select(Patient)
            .where(
                or_(
                    Patient.first_name.ilike(f"%{entity}%"),
                    Patient.last_name.ilike(f"%{entity}%"),
                )
            )
            .limit(1)
        )
        patient = result.scalar_one_or_none()

        if patient:
            logger.info(f"Resolved '{entity}' to patient_id: {patient.id}")
            return {"resolved_ids": {"patient_id": patient.id}}

        logger.warning(f"Could not resolve entity: {entity}")
        return {"resolved_ids": {}}

    except Exception as e:
        logger.error(f"Entity resolution failed: {e}")
        return {"error": f"Entity resolution failed: {str(e)}"}


async def query_database(state: ConversationState, config: RunnableConfig) -> dict:
    """
    Step C: Execute database query with caching.

    Uses AnalyticsAgent for analytics queries (has cache + templates).
    Uses direct queries for search/detail intents.
    """
    if state.get("error"):
        return {}

    try:
        # Get db from config
        db = config["configurable"]["db"]
        intent = state.get("intent")

        # Use AnalyticsAgent for analytics queries (has cache + templates)
        if intent == INTENT_ANALYTICS:
            result = await analytics_agent.answer_analytics_question(
                question=state["query"], db=db, explain=False  # We'll explain in Step D
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

        logger.info(f"Query returned {len(visits)} results")

        return {
            "results": [
                {
                    "id": v.id,
                    "date": str(v.visit_date),
                    "chief_complaint": v.chief_complaint,
                    "diagnosis": v.diagnosis,
                    "visit_type": v.visit_type,
                }
                for v in visits
            ]
        }

    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return {"error": f"Database query failed: {str(e)}"}


async def generate_response(state: ConversationState, config: RunnableConfig) -> dict:
    """
    Step D: Generate natural language response.

    Uses FallbackAgent to generate a professional response based on results.
    Handles errors gracefully with user-friendly messages.
    """
    # Handle errors gracefully
    if state.get("error"):
        error_msg = f"I encountered an issue: {state['error']}. Please try rephrasing your question."
        return {
            "response": error_msg,
            "messages": [
                {"role": "user", "content": state["query"]},
                {"role": "assistant", "content": error_msg},
            ],
        }

    try:
        results = state.get("results", [])
        results_summary = (
            f"{len(results)} results found" if results else "No results found"
        )

        prompt = f"""
User Query: {state['query']}
Intent: {state.get('intent')}
Results: {results[:10]}
Summary: {results_summary}

Generate a helpful, professional response for a medical professional.
If there are results, summarize them clearly. If no results, suggest alternatives.
"""
        response = await narrator_agent.run_async(prompt)

        logger.info(f"Generated response for intent: {state.get('intent')}")

        return {
            "response": response,
            "messages": [
                {"role": "user", "content": state["query"]},
                {"role": "assistant", "content": response},
            ],
        }
    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        fallback = "I apologize, but I couldn't generate a response. Please try again."
        return {
            "response": fallback,
            "messages": [
                {"role": "user", "content": state["query"]},
                {"role": "assistant", "content": fallback},
            ],
            "error": str(e),
        }
