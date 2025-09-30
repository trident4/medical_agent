"""
Test cases for AI agent endpoints - Visit Summarization API.
Tests the fallback system with OpenAI -> X.AI (grok-3) -> Anthropic.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main_dev import app
from app.agents.base_agent import FallbackAgent
from app.agents.summarizer_fallback import visit_summarizer
from app.models.patient import PatientResponse
from app.models.visit import VisitResponse
from datetime import date, datetime

# Test client
client = TestClient(app)


class TestVisitSummarizationAPI:
    """Test suite for visit summarization API endpoints."""

    def setup_method(self):
        """Setup test data before each test."""
        # Mock patient data
        self.mock_patient = PatientResponse(
            id=1,
            patient_id="PAT001",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            gender="male",
            email="john.doe@email.com",
            phone="555-0123",
            medical_history="Hypertension, Type 2 Diabetes"
        )

        # Mock visit data
        self.mock_visit = VisitResponse(
            id=1,
            patient_id=1,
            visit_date=date(2024, 12, 15),
            visit_type="routine_checkup",
            chief_complaint="Annual physical examination",
            diagnosis="Hypertension - controlled, Diabetes Type 2 - well managed",
            treatment_plan="Continue current medications, lifestyle modifications",
            notes="Patient reports feeling well. Blood pressure 130/80. A1C 6.8%.",
            follow_up_date=date(2025, 6, 15)
        )

    def test_agent_status_endpoint(self):
        """Test the AI agent status endpoint."""
        response = client.get("/api/v1/ai/status")
        assert response.status_code == 200

        data = response.json()
        assert "qa_agent" in data
        assert "summarizer_agent" in data
        assert "fallback_enabled" in data
        assert data["fallback_enabled"] is True

    @patch('app.api.v1.endpoints.agents_fallback.get_visit')
    @patch('app.api.v1.endpoints.agents_fallback.get_patient')
    @patch('app.agents.summarizer_fallback.visit_summarizer.summarize_visit')
    def test_summarize_visit_success(self, mock_summarize, mock_get_patient, mock_get_visit):
        """Test successful visit summarization."""
        # Setup mocks
        mock_get_visit.return_value = self.mock_visit
        mock_get_patient.return_value = self.mock_patient
        mock_summarize.return_value = "Test summary of the visit"

        # Test data
        request_data = {
            "visit_id": 1,
            "include_patient_context": True
        }

        # Make request
        response = client.post("/api/v1/ai/summarize", json=request_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "visit_id" in data
        assert "patient_id" in data
        assert data["visit_id"] == 1
        assert data["patient_id"] == 1

    @patch('app.api.v1.endpoints.agents_fallback.get_visit')
    def test_summarize_visit_not_found(self, mock_get_visit):
        """Test visit summarization with non-existent visit."""
        # Setup mock to raise exception
        mock_get_visit.side_effect = Exception("Visit not found")

        request_data = {
            "visit_id": 999,
            "include_patient_context": True
        }

        response = client.post("/api/v1/ai/summarize", json=request_data)
        assert response.status_code == 500

    @patch('app.api.v1.endpoints.agents_fallback.get_patient')
    @patch('app.api.v1.endpoints.agents_fallback.VisitService')
    @patch('app.agents.summarizer_fallback.visit_summarizer.summarize_patient_history')
    def test_patient_history_summary_success(self, mock_summarize_history, mock_visit_service, mock_get_patient):
        """Test successful patient history summarization."""
        # Setup mocks
        mock_get_patient.return_value = self.mock_patient

        mock_visit_service_instance = Mock()
        mock_visit_service.return_value = mock_visit_service_instance
        mock_visit_service_instance.get_patient_visits_by_db_id.return_value = [
            self.mock_visit]

        mock_summarize_history.return_value = "Patient history summary"

        request_data = {
            "patient_id": 1,
            "max_visits": 5
        }

        response = client.post("/api/v1/ai/patient-history", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "patient_id" in data
        assert data["patient_id"] == 1

    @patch('app.api.v1.endpoints.agents_fallback.get_visit')
    @patch('app.api.v1.endpoints.agents_fallback.get_patient')
    @patch('app.agents.summarizer_fallback.visit_summarizer.create_discharge_summary')
    def test_discharge_summary_success(self, mock_discharge, mock_get_patient, mock_get_visit):
        """Test successful discharge summary creation."""
        # Setup mocks
        mock_get_visit.return_value = self.mock_visit
        mock_get_patient.return_value = self.mock_patient
        mock_discharge.return_value = "Discharge summary content"

        request_data = {
            "visit_id": 1,
            "include_patient_context": True
        }

        response = client.post(
            "/api/v1/ai/discharge-summary", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "discharge_summary" in data
        assert "visit_id" in data
        assert "patient_id" in data


class TestFallbackSystem:
    """Test the AI provider fallback system specifically."""

    @pytest.mark.asyncio
    async def test_fallback_agent_initialization(self):
        """Test that FallbackAgent initializes correctly."""
        agent = FallbackAgent("Test system prompt")

        # Check that agent status is available
        status = agent.get_status()
        assert isinstance(status, dict)
        assert "openai" in status
        assert "xai" in status
        assert "anthropic" in status

    @pytest.mark.asyncio
    async def test_fallback_order(self):
        """Test that fallback happens in correct order: OpenAI -> X.AI -> Anthropic."""
        agent = FallbackAgent("Test prompt")

        # Mock all providers to fail except XAI
        with patch.object(agent, '_query_xai_direct', return_value="XAI response") as mock_xai:
            # Mock OpenAI agent to fail
            mock_openai_agent = Mock()
            mock_openai_agent.run = AsyncMock(
                side_effect=Exception("OpenAI failed"))
            agent.agents['openai'] = mock_openai_agent

            # Mock Anthropic agent (shouldn't be called)
            mock_anthropic_agent = Mock()
            mock_anthropic_agent.run = AsyncMock(
                return_value=Mock(data="Anthropic response"))
            agent.agents['anthropic'] = mock_anthropic_agent

            # Set XAI as custom
            agent.agents['xai'] = "xai_custom"

            result = await agent.run_async("Test input")

            # Verify XAI was called and returned result
            assert result == "XAI response"
            mock_xai.assert_called_once_with("Test input")
            # Anthropic should not be called since XAI succeeded
            mock_anthropic_agent.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """Test behavior when all AI providers fail."""
        agent = FallbackAgent("Test prompt")

        # Mock all providers to fail
        mock_openai_agent = Mock()
        mock_openai_agent.run = AsyncMock(
            side_effect=Exception("OpenAI failed"))
        agent.agents['openai'] = mock_openai_agent

        # Mock XAI to fail
        with patch.object(agent, '_query_xai_direct', side_effect=Exception("XAI failed")):
            agent.agents['xai'] = "xai_custom"

            # Mock Anthropic to fail
            mock_anthropic_agent = Mock()
            mock_anthropic_agent.run = AsyncMock(
                side_effect=Exception("Anthropic failed"))
            agent.agents['anthropic'] = mock_anthropic_agent

            # Should raise exception when all fail
            with pytest.raises(Exception) as exc_info:
                await agent.run_async("Test input")

            assert "All AI providers failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_xai_grok3_direct_call(self):
        """Test direct X.AI API call with grok-3 model."""
        agent = FallbackAgent("Medical assistant prompt")

        # Mock the HTTP client response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Grok-3 medical summary response"
                    }
                }
            ]
        }

        # Mock httpx.AsyncClient
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            result = await agent._query_xai_direct("Summarize this medical visit")

            # Verify the API was called correctly
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args

            # Check URL
            assert call_args[0][0] == "https://api.xai.com/v1/chat/completions"

            # Check payload contains grok-3 model
            payload = call_args[1]['json']
            assert payload['model'] == "grok-3"
            assert "Summarize this medical visit" in payload['messages'][1]['content']

            # Check result
            assert result == "Grok-3 medical summary response"


class TestMedicalSummarizationScenarios:
    """Test various medical scenarios for visit summarization."""

    @pytest.mark.asyncio
    async def test_routine_checkup_summary(self):
        """Test summarization of a routine checkup visit."""
        patient = PatientResponse(
            id=1, patient_id="PAT001", first_name="Alice", last_name="Smith",
            date_of_birth=date(1985, 3, 10), gender="female",
            email="alice@email.com", phone="555-0123",
            medical_history="No significant medical history"
        )

        visit = VisitResponse(
            id=1, patient_id=1, visit_date=date(2024, 12, 15),
            visit_type="routine_checkup",
            chief_complaint="Annual physical examination",
            diagnosis="Healthy adult - no acute concerns",
            treatment_plan="Continue current health maintenance",
            notes="Vital signs normal. No complaints. Encourage continued exercise."
        )

        # Mock the actual AI call to return a realistic summary
        with patch.object(visit_summarizer, 'summarize_visit', return_value="VISIT SUMMARY: Routine annual physical for healthy 39-year-old female. No acute concerns identified."):
            result = await visit_summarizer.summarize_visit(visit, patient)
            assert "Routine annual physical" in result
            assert "healthy" in result.lower()

    @pytest.mark.asyncio
    async def test_emergency_visit_summary(self):
        """Test summarization of an emergency visit."""
        patient = PatientResponse(
            id=2, patient_id="PAT002", first_name="Robert", last_name="Johnson",
            date_of_birth=date(1970, 7, 20), gender="male",
            email="robert@email.com", phone="555-0456",
            medical_history="Hypertension, CAD s/p MI 2019"
        )

        visit = VisitResponse(
            id=2, patient_id=2, visit_date=date(2024, 12, 15),
            visit_type="emergency",
            chief_complaint="Chest pain",
            diagnosis="Non-cardiac chest pain, musculoskeletal etiology",
            treatment_plan="NSAIDs, rest, follow-up with PCP",
            notes="EKG normal, troponins negative. Pain reproducible with palpation."
        )

        with patch.object(visit_summarizer, 'summarize_visit', return_value="EMERGENCY VISIT: 54-year-old male with chest pain. Ruled out cardiac etiology. Musculoskeletal cause identified."):
            result = await visit_summarizer.summarize_visit(visit, patient)
            assert "chest pain" in result.lower()
            assert "emergency" in result.lower()

    @pytest.mark.asyncio
    async def test_chronic_disease_management_summary(self):
        """Test summarization of chronic disease management visit."""
        patient = PatientResponse(
            id=3, patient_id="PAT003", first_name="Maria", last_name="Garcia",
            date_of_birth=date(1965, 11, 5), gender="female",
            email="maria@email.com", phone="555-0789",
            medical_history="Type 2 DM, HTN, Hyperlipidemia, Obesity"
        )

        visit = VisitResponse(
            id=3, patient_id=3, visit_date=date(2024, 12, 15),
            visit_type="follow_up",
            chief_complaint="Diabetes follow-up",
            diagnosis="Type 2 DM - well controlled, HTN - controlled",
            treatment_plan="Continue metformin, increase lisinopril dose",
            notes="A1C 6.5%, BP 145/90. Patient adherent to medications. Weight stable."
        )

        with patch.object(visit_summarizer, 'summarize_visit', return_value="CHRONIC CARE: Diabetes follow-up for 59-year-old female. Good glycemic control (A1C 6.5%). BP slightly elevated, medication adjustment made."):
            result = await visit_summarizer.summarize_visit(visit, patient)
            assert "diabetes" in result.lower()
            assert "a1c" in result.lower()


# Test data fixtures
@pytest.fixture
def sample_patient():
    """Fixture providing sample patient data."""
    return PatientResponse(
        id=1,
        patient_id="TEST001",
        first_name="Test",
        last_name="Patient",
        date_of_birth=date(1990, 1, 1),
        gender="other",
        email="test@example.com",
        phone="555-TEST",
        medical_history="Test medical history"
    )


@pytest.fixture
def sample_visit():
    """Fixture providing sample visit data."""
    return VisitResponse(
        id=1,
        patient_id=1,
        visit_date=date(2024, 12, 15),
        visit_type="test_visit",
        chief_complaint="Test complaint",
        diagnosis="Test diagnosis",
        treatment_plan="Test treatment",
        notes="Test notes"
    )


class TestAPIValidation:
    """Test API request validation and error handling."""

    def test_summarize_invalid_visit_id(self):
        """Test summarization with invalid visit ID format."""
        request_data = {
            "visit_id": "invalid",
            "include_patient_context": True
        }

        response = client.post("/api/v1/ai/summarize", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_summarize_missing_visit_id(self):
        """Test summarization without required visit_id."""
        request_data = {
            "include_patient_context": True
        }

        response = client.post("/api/v1/ai/summarize", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_patient_history_invalid_patient_id(self):
        """Test patient history with invalid patient ID."""
        request_data = {
            "patient_id": -1,
            "max_visits": 5
        }

        response = client.post("/api/v1/ai/patient-history", json=request_data)
        assert response.status_code == 500  # Should fail to find patient


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_visit_summarization.py -v
    pytest.main([__file__, "-v"])
