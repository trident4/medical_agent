"""
Tests for LangGraph pipeline routing logic.
"""

import pytest
from app.graph.pipeline import route_by_intent, build_graph
from app.graph.state import (
    ConversationState,
    INTENT_SEARCH,
    INTENT_DETAIL,
    INTENT_SUMMARIZE,
    INTENT_ANALYTICS,
    INTENT_CHITCHAT,
)


class TestRouteByIntent:
    """Test conditional routing based on intent."""

    def _create_state(self, intent: str = None, error: str = None) -> ConversationState:
        """Helper to create a test state."""
        return {
            "query": "test query",
            "session_id": "test-session",
            "intent": intent,
            "filters": {},
            "entity_to_resolve": None,
            "resolved_ids": {},
            "results": [],
            "response": "",
            "messages": [],
            "error": error,
        }

    def test_route_error_to_generate_response(self):
        """Error state should route to generate_response."""
        state = self._create_state(error="Something failed")
        result = route_by_intent(state)
        assert result == "generate_response"

    def test_route_chitchat_to_generate_response(self):
        """Chitchat intent should skip to generate_response."""
        state = self._create_state(intent=INTENT_CHITCHAT)
        result = route_by_intent(state)
        assert result == "generate_response"

    def test_route_analytics_to_query_database(self):
        """Analytics intent should skip entity resolution."""
        state = self._create_state(intent=INTENT_ANALYTICS)
        result = route_by_intent(state)
        assert result == "query_database"

    def test_route_search_to_resolve_entities(self):
        """Search intent should go through full pipeline."""
        state = self._create_state(intent=INTENT_SEARCH)
        result = route_by_intent(state)
        assert result == "resolve_entities"

    def test_route_detail_to_resolve_entities(self):
        """Detail intent should go through full pipeline."""
        state = self._create_state(intent=INTENT_DETAIL)
        result = route_by_intent(state)
        assert result == "resolve_entities"

    def test_route_summarize_to_resolve_entities(self):
        """Summarize intent should go through full pipeline."""
        state = self._create_state(intent=INTENT_SUMMARIZE)
        result = route_by_intent(state)
        assert result == "resolve_entities"


class TestBuildGraph:
    """Test graph construction."""

    def test_build_graph_returns_state_graph(self):
        """build_graph should return a StateGraph object."""
        from langgraph.graph import StateGraph

        graph = build_graph()
        assert isinstance(graph, StateGraph)

    def test_graph_has_all_nodes(self):
        """Graph should have all required nodes."""
        graph = build_graph()

        # Check nodes are registered
        node_names = list(graph.nodes.keys())
        assert "extract_intent" in node_names
        assert "resolve_entities" in node_names
        assert "query_database" in node_names
        assert "generate_response" in node_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
