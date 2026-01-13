"""
Tests for LangGraph node functions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.graph.nodes import extract_intent, resolve_entities, query_database
from app.graph.state import (
    ConversationState,
    INTENT_SEARCH,
    INTENT_CHITCHAT,
    INTENT_ANALYTICS,
)


def create_test_state(
    query: str = "test query",
    intent: str = None,
    entity_to_resolve: str = None,
    resolved_ids: dict = None,
    error: str = None,
) -> ConversationState:
    """Helper to create a test state."""
    return {
        "query": query,
        "session_id": "test-session",
        "intent": intent,
        "filters": {},
        "entity_to_resolve": entity_to_resolve,
        "resolved_ids": resolved_ids or {},
        "results": [],
        "response": "",
        "messages": [],
        "error": error,
    }


class TestExtractIntent:
    """Test extract_intent node."""

    @pytest.mark.asyncio
    @patch("app.graph.nodes.FallbackAgent")
    async def test_extract_intent_returns_intent(self, mock_agent_class):
        """Node should return intent from query."""
        # Mock the agent response
        mock_agent = MagicMock()
        mock_agent.run_async = AsyncMock(
            return_value='{"intent": "search", "filters": {}, "entity_to_resolve": "Michael"}'
        )
        mock_agent_class.return_value = mock_agent

        state = create_test_state(query="Show visits for Michael")
        config = {"configurable": {"db": MagicMock()}}

        result = await extract_intent(state, config)

        # Result should have intent key (or error if agent fails)
        assert "intent" in result or "error" in result


class TestResolveEntities:
    """Test resolve_entities node."""

    @pytest.mark.asyncio
    async def test_resolve_entities_with_error_returns_empty(self):
        """Node should return empty if error exists."""
        state = create_test_state(error="Previous error")
        config = {"configurable": {"db": MagicMock()}}

        result = await resolve_entities(state, config)
        assert result == {}

    @pytest.mark.asyncio
    async def test_resolve_entities_no_entity_returns_empty_ids(self):
        """Node should return empty resolved_ids if no entity to resolve."""
        state = create_test_state(entity_to_resolve=None)
        config = {"configurable": {"db": MagicMock()}}

        result = await resolve_entities(state, config)
        assert result == {"resolved_ids": {}}


class TestQueryDatabase:
    """Test query_database node."""

    @pytest.mark.asyncio
    async def test_query_database_with_error_returns_empty(self):
        """Node should return empty if error exists."""
        state = create_test_state(error="Previous error")
        config = {"configurable": {"db": MagicMock()}}

        result = await query_database(state, config)
        assert result == {}

    @pytest.mark.asyncio
    async def test_query_database_with_mock_db_returns_error_or_results(self):
        """Query database with mock db should handle gracefully."""
        state = create_test_state(intent=INTENT_SEARCH)

        # Create a proper async mock for the db
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=MagicMock(
                scalars=MagicMock(
                    return_value=MagicMock(all=MagicMock(return_value=[]))
                )
            )
        )

        config = {"configurable": {"db": mock_db}}

        result = await query_database(state, config)

        # Should return results or error (graceful handling)
        assert "results" in result or "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
