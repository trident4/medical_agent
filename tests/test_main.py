"""
Basic tests for the medical assistant API.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_main():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Medical Assistant API"


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_openapi_docs():
    """Test that OpenAPI docs are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_api_routes_exist():
    """Test that API routes are properly mounted."""
    # Test that the OpenAPI schema includes our API routes
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200

    openapi_schema = response.json()
    paths = openapi_schema.get("paths", {})

    # Check that our main API paths exist
    assert any("/api/v1/patients" in path for path in paths.keys())
    assert any("/api/v1/visits" in path for path in paths.keys())
    assert any("/api/v1/agents" in path for path in paths.keys())


@pytest.mark.asyncio
async def test_patient_endpoints_structure():
    """Test that patient endpoints have correct structure."""
    # This is a structural test - we're not testing database operations
    # since we don't have a test database set up yet

    # Test that the endpoints exist and return appropriate error messages
    # when no database is connected
    response = client.get("/api/v1/patients/")
    # This might fail with a database error, which is expected
    # The important thing is that the route exists
    assert response.status_code in [200, 500]  # 500 if no DB connection


if __name__ == "__main__":
    pytest.main([__file__])
