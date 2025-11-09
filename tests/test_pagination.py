"""
Tests for pagination functionality using API endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_01_pagination_page_based():
    """Test page-based pagination through API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test first page
        response = await client.get("/api/v1/patients/?page=1&page_size=5")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data, "Should have items field"
        assert "total" in data, "Should have total field"
        assert "page" in data, "Should have page field"
        assert "page_size" in data, "Should have page_size field"
        assert "total_pages" in data, "Should have total_pages field"
        assert "has_next" in data, "Should have has_next field"
        assert "has_previous" in data, "Should have has_previous field"

        assert data["page"] == 1, "Page should be 1"
        assert data["page_size"] == 5, "Page size should be 5"
        assert data["has_previous"] is False, "First page should not have previous"

        # Store total for later tests
        total_patients = data["total"]

        # If we have enough patients, test middle and last pages
        if total_patients >= 15:
            # Test middle page
            response = await client.get("/api/v1/patients/?page=2&page_size=5")
            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 2, "Page should be 2"
            assert data["has_previous"] is True, "Second page should have previous"

            # Test last page
            last_page = data["total_pages"]
            response = await client.get(f"/api/v1/patients/?page={last_page}&page_size=5")
            assert response.status_code == 200
            data = response.json()
            assert data["page"] == last_page, f"Page should be {last_page}"
            assert data["has_next"] is False, "Last page should not have next"


@pytest.mark.asyncio
async def test_02_pagination_offset_based():
    """Test offset-based pagination (backward compatibility)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/patients/?skip=0&limit=10")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(
            data, list), "Should return list for offset-based pagination"
        # Should return up to 10 items (or fewer if less exist)
        assert len(data) <= 10, "Should return at most 10 items"


@pytest.mark.asyncio
async def test_03_pagination_with_search():
    """Test pagination works with search."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First get some patient data to search for
        response = await client.get("/api/v1/patients/?page=1&page_size=1")
        assert response.status_code == 200
        data = response.json()

        if data["total"] > 0 and len(data["items"]) > 0:
            # Get the first name of the first patient
            first_patient_name = data["items"][0]["full_name"].split()[0]

            # Search with pagination
            response = await client.get(
                f"/api/v1/patients/?search={first_patient_name}&page=1&page_size=5"
            )
            assert response.status_code == 200
            data = response.json()

            assert "items" in data, "Should have items field"
            assert "total" in data, "Should have total field"
            # Verify search worked - results should contain the search term
            if len(data["items"]) > 0:
                assert first_patient_name in data["items"][0]["full_name"]


@pytest.mark.asyncio
async def test_04_pagination_empty_page():
    """Test requesting a page beyond available data."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/patients/?page=9999&page_size=5")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 0, "Should return empty list"
        assert data["page"] == 9999, "Page should be 9999"
        assert data["has_next"] is False, "Should not have next page"


@pytest.mark.asyncio
async def test_05_pagination_metadata_accuracy():
    """Test that pagination metadata is accurate."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        page_size = 3
        response = await client.get(f"/api/v1/patients/?page=1&page_size={page_size}")
        assert response.status_code == 200

        data = response.json()

        # Verify metadata calculations
        total = data["total"]
        expected_total_pages = (
            total + page_size - 1) // page_size  # Ceiling division

        assert data["total_pages"] == expected_total_pages, "Total pages calculation incorrect"
        assert data["has_next"] == (
            data["page"] < data["total_pages"]), "has_next calculation incorrect"
        assert data["has_previous"] == (
            data["page"] > 1), "has_previous calculation incorrect"
