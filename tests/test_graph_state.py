"""
Tests for LangGraph state schema and constants.
"""

import pytest
from app.graph.state import (
    ConversationState,
    INTENT_SEARCH,
    INTENT_DETAIL,
    INTENT_SUMMARIZE,
    INTENT_ANALYTICS,
    INTENT_CHITCHAT,
    VALID_INTENTS,
)


class TestIntentConstants:
    """Test intent constant definitions."""

    def test_intent_constants_are_strings(self):
        """Verify all intent constants are strings."""
        assert isinstance(INTENT_SEARCH, str)
        assert isinstance(INTENT_DETAIL, str)
        assert isinstance(INTENT_SUMMARIZE, str)
        assert isinstance(INTENT_ANALYTICS, str)
        assert isinstance(INTENT_CHITCHAT, str)

    def test_valid_intents_contains_all_constants(self):
        """Verify VALID_INTENTS set contains all intent constants."""
        assert INTENT_SEARCH in VALID_INTENTS
        assert INTENT_DETAIL in VALID_INTENTS
        assert INTENT_SUMMARIZE in VALID_INTENTS
        assert INTENT_ANALYTICS in VALID_INTENTS
        assert INTENT_CHITCHAT in VALID_INTENTS

    def test_valid_intents_count(self):
        """Verify VALID_INTENTS has exactly 5 intents."""
        assert len(VALID_INTENTS) == 5


class TestConversationState:
    """Test ConversationState TypedDict structure."""

    def test_create_minimal_state(self):
        """Test creating a minimal valid state."""
        state: ConversationState = {
            "query": "Hello",
            "session_id": "test-123",
            "intent": None,
            "filters": {},
            "entity_to_resolve": None,
            "resolved_ids": {},
            "results": [],
            "response": "",
            "messages": [],
            "error": None,
        }
        assert state["query"] == "Hello"
        assert state["session_id"] == "test-123"

    def test_state_with_intent(self):
        """Test state with intent set."""
        state: ConversationState = {
            "query": "Show patients",
            "session_id": "test-456",
            "intent": INTENT_SEARCH,
            "filters": {"diagnosis": "diabetes"},
            "entity_to_resolve": None,
            "resolved_ids": {},
            "results": [],
            "response": "",
            "messages": [],
            "error": None,
        }
        assert state["intent"] == "search"
        assert state["filters"]["diagnosis"] == "diabetes"

    def test_state_with_results(self):
        """Test state with query results."""
        state: ConversationState = {
            "query": "Show visits",
            "session_id": "test-789",
            "intent": INTENT_SEARCH,
            "filters": {},
            "entity_to_resolve": None,
            "resolved_ids": {"patient_id": 1},
            "results": [{"id": 1, "date": "2024-01-01", "chief_complaint": "Headache"}],
            "response": "Found 1 visit",
            "messages": [],
            "error": None,
        }
        assert len(state["results"]) == 1
        assert state["resolved_ids"]["patient_id"] == 1

    def test_state_with_error(self):
        """Test state with error set."""
        state: ConversationState = {
            "query": "Invalid query",
            "session_id": "test-error",
            "intent": None,
            "filters": {},
            "entity_to_resolve": None,
            "resolved_ids": {},
            "results": [],
            "response": "",
            "messages": [],
            "error": "Something went wrong",
        }
        assert state["error"] == "Something went wrong"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
