"""
LangGraph state schema for the Medical Assistant pipeline.

IMPORTANT:
- LangGraph requires TypedDict, not Pydantic BaseModel for state.
- DO NOT put database session in state - it cannot be serialized.
- Use str for intent, not Enum (serialization issues).
"""

from typing import Optional, List, Dict, Any, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


# Intent as string constants (avoids Enum serialization issues)
INTENT_SEARCH = "search"
INTENT_DETAIL = "detail"
INTENT_SUMMARIZE = "summarize"
INTENT_ANALYTICS = "analytics"
INTENT_CHITCHAT = "chitchat"

VALID_INTENTS = {
    INTENT_SEARCH,
    INTENT_DETAIL,
    INTENT_SUMMARIZE,
    INTENT_ANALYTICS,
    INTENT_CHITCHAT,
}


class ConversationState(TypedDict):
    """
    LangGraph state that flows between pipeline nodes.

    IMPORTANT: Do NOT include database session here.
    Pass db via config["configurable"]["db"] instead.
    """

    # Input
    query: str
    session_id: str

    # Step A output (Intent Extraction)
    intent: Optional[str]  # Use str, not Enum (serialization safe)
    filters: Dict[str, Any]
    entity_to_resolve: Optional[str]

    # Step B output (Entity Resolution)
    resolved_ids: Dict[str, int]

    # Step C output (Database Query)
    results: List[Dict[str, Any]]

    # Step D output (Response Generation)
    response: str

    # Conversation history (auto-accumulated by LangGraph)
    messages: Annotated[list, add_messages]

    # Error tracking for graceful degradation
    error: Optional[str]
