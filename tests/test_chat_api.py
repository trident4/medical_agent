"""
Tests for LangGraph chat API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestChatEndpointAuth:
    """Test authentication for chat endpoints."""

    def test_chat_requires_auth(self):
        """Test that /chat/ endpoint requires authentication."""
        response = client.post(
            "/api/v1/chat/",
            json={"message": "Hello", "session_id": "test-123"},
        )
        assert response.status_code == 401

    def test_chat_stream_requires_auth(self):
        """Test that /chat/stream endpoint requires authentication."""
        response = client.post(
            "/api/v1/chat/stream",
            json={"message": "Hello", "session_id": "test-123"},
        )
        assert response.status_code == 401

    def test_chat_invalid_token(self):
        """Test that invalid token is rejected."""
        response = client.post(
            "/api/v1/chat/",
            headers={"Authorization": "Bearer invalid-token"},
            json={"message": "Hello", "session_id": "test-123"},
        )
        assert response.status_code == 401


class TestChatEndpointValidation:
    """Test request validation for chat endpoints."""

    def test_chat_requires_message(self):
        """Test that message field is required."""
        response = client.post(
            "/api/v1/chat/",
            json={"session_id": "test-123"},
        )
        # Should fail validation or auth (auth checked first)
        assert response.status_code in [401, 422]

    def test_chat_requires_session_id(self):
        """Test that session_id field is required."""
        response = client.post(
            "/api/v1/chat/",
            json={"message": "Hello"},
        )
        # Should fail validation or auth
        assert response.status_code in [401, 422]


class TestChatRouteExists:
    """Test that chat routes are properly registered."""

    def test_chat_route_in_openapi(self):
        """Test that chat routes appear in OpenAPI schema."""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200

        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Check that chat paths exist
        assert "/api/v1/chat/" in paths
        assert "/api/v1/chat/stream" in paths

    def test_chat_route_has_post_method(self):
        """Test that chat routes have POST method."""
        response = client.get("/api/v1/openapi.json")
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        assert "post" in paths.get("/api/v1/chat/", {})
        assert "post" in paths.get("/api/v1/chat/stream", {})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
