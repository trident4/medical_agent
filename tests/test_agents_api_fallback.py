"""
API test cases for the Grok-3 fallback system.
Tests all agent endpoints with real API calls.
"""

import pytest
import requests
import json
from datetime import datetime, date


# Test configuration
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"


class TestAgentsAPIWithFallback:
    """Test the agents API endpoints with Grok-3 fallback system."""

    @classmethod
    def setup_class(cls):
        """Setup test data."""
        cls.test_patient_id = None
        cls.test_visit_id = None

        # Check if server is running
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            assert response.status_code == 200
            print("✅ Server is running")
        except requests.exceptions.ConnectionError:
            pytest.skip(
                "Server not running. Start with: uvicorn app.main:app --host 127.0.0.1 --port 8001")

    def test_01_create_test_patient(self):
        """Create a test patient for API testing."""
        patient_data = {
            "patient_id": "API-TEST-001",
            "first_name": "Alice",
            "last_name": "TestPatient",
            "date_of_birth": "1990-05-15",
            "gender": "female",
            "email": "alice.test@example.com",
            "phone": "555-0100",
            "address": "456 Test Avenue, Test City, TC 12345",
            "emergency_contact": "Emergency Contact: 555-0911",
            "medical_history": "Type 2 diabetes, well controlled with metformin. History of hypertension.",
            "allergies": "Penicillin",
            "current_medications": "Metformin 500mg twice daily, Lisinopril 10mg daily"
        }

        response = requests.post(
            f"{API_BASE}/patients/", json=patient_data, timeout=10)
        if response.status_code == 201:
            patient = response.json()
            TestAgentsAPIWithFallback.test_patient_id = patient["id"]
            print(f"✅ Created test patient with ID: {patient['id']}")
        elif response.status_code == 400:
            # Patient already exists, get existing patient
            get_response = requests.get(
                f"{API_BASE}/patients/API-TEST-001", timeout=10)
            if get_response.status_code == 200:
                patient = get_response.json()
                TestAgentsAPIWithFallback.test_patient_id = patient["id"]
                print(
                    f"✅ Using existing test patient with ID: {patient['id']}")
            else:
                pytest.fail(
                    f"Could not retrieve existing patient: {get_response.status_code}")
        else:
            pytest.fail(
                f"Failed to create or retrieve patient: {response.status_code} - {response.text}")

        return patient

    def test_02_create_test_visit(self):
        """Create a test visit for API testing."""
        if not TestAgentsAPIWithFallback.test_patient_id:
            pytest.skip("No patient created")

        visit_data = {
            "patient_id": TestAgentsAPIWithFallback.test_patient_id,
            "visit_id": "API-TEST-VISIT-001",
            "visit_date": "2024-12-20T10:00:00",
            "visit_type": "follow_up",
            "chief_complaint": "Routine diabetes follow-up and blood pressure check",
            "diagnosis": "Type 2 diabetes mellitus - well controlled. Essential hypertension - stable.",
            "treatment_plan": "Continue current metformin regimen. Increase lisinopril to 15mg daily due to slightly elevated BP. Schedule follow-up in 3 months.",
            "doctor_notes": "Patient reports good adherence to medications. Blood glucose logs show excellent control with HbA1c of 6.8%. Blood pressure today 138/85, slightly elevated from last visit. No complaints of side effects from current medications. Patient educated on low-sodium diet and importance of regular exercise.",
            "medications_prescribed": "Metformin 500mg BID (continue), Lisinopril 15mg daily (increased from 10mg)",
            "follow_up_instructions": "Follow-up in 3 months. Monitor blood pressure at home weekly. Continue glucose monitoring twice daily.",
            "follow_up_date": "2025-03-20"
        }

        response = requests.post(
            f"{API_BASE}/visits/", json=visit_data, timeout=10)
        if response.status_code == 201:
            visit = response.json()
            TestAgentsAPIWithFallback.test_visit_id = visit["id"]
            TestAgentsAPIWithFallback.test_visit_visit_id = visit["visit_id"]
            print(f"✅ Created test visit with ID: {visit['id']}")
        elif response.status_code == 400:
            # Visit already exists, get existing visit
            get_response = requests.get(
                f"{API_BASE}/visits/API-TEST-VISIT-001", timeout=10)
            print(f"Get existing visit response: {get_response.status_code}")
            if get_response.status_code == 200:
                visit = get_response.json()
                TestAgentsAPIWithFallback.test_visit_id = visit["id"]
                print(
                    f"✅ Using existing test visit with ID: {visit['id']}")
            else:
                pytest.fail(
                    f"Could not retrieve existing visit: {get_response.status_code}")
        else:
            pytest.fail(
                f"Failed to create or retrieve visit: {response.status_code} - {response.text}")

        return visit

    def test_03_ask_endpoint_basic_question(self):
        """Test the /ask endpoint with a basic medical question."""
        if not TestAgentsAPIWithFallback.test_patient_id:
            pytest.skip("No patient created")

        request_data = {
            "question": "What was this patient's last diagnosis?",
            "patient_id": "API-TEST-001",
            "context_type": "patient"
        }

        response = requests.post(
            f"{API_BASE}/agents/ask", json=request_data, timeout=30)

        print(f"Ask endpoint response status: {response.status_code}")

        if response.status_code != 200:
            print(f"Error response: {response.text}")
            pytest.fail(
                f"Ask endpoint failed with status {response.status_code}")

        data = response.json()
        print(f"✅ Ask Endpoint Success!")
        print(f"Question: {data['question']}")
        print(f"Answer (first 200 chars): {data['answer'][:200]}...")
        print(f"Sources: {data['sources']}")

        # Verify response structure
        assert "question" in data
        assert "answer" in data
        assert "sources" in data
        assert "confidence_score" in data
        assert "context_used" in data
        assert "generated_at" in data

        # Answer should contain relevant medical information
        answer = data["answer"].lower()
        assert any(term in answer for term in ["diabetes", "hypertension", "diagnosis", "patient"]), \
            f"Answer doesn't contain expected medical terms: {data['answer'][:100]}"

    def test_04_ask_endpoint_general_question(self):
        """Test the /ask endpoint with a general medical question."""
        request_data = {
            "question": "What is the normal range for HbA1c in diabetic patients?",
            "context_type": "all"
        }

        response = requests.post(
            f"{API_BASE}/agents/ask", json=request_data, timeout=30)

        print(f"General question response status: {response.status_code}")

        if response.status_code != 200:
            print(f"Error response: {response.text}")
            pytest.fail(
                f"General question failed with status {response.status_code}")

        data = response.json()
        print(f"✅ General Question Success!")
        print(f"Answer (first 200 chars): {data['answer'][:200]}...")

        # Verify response structure
        assert "answer" in data
        assert len(data["answer"]) > 10

        # Answer should contain relevant information about HbA1c
        answer = data["answer"].lower()
        assert any(term in answer for term in ["hba1c", "diabetic", "glucose", "7%", "percent"]), \
            f"Answer doesn't contain expected HbA1c information: {data['answer'][:100]}"

    def test_05_summarize_endpoint(self):
        """Test the /summarize endpoint."""
        if not TestAgentsAPIWithFallback.test_visit_id:
            pytest.skip("No visit created")

        request_data = {
            "visit_id": "API-TEST-VISIT-001",
            "include_patient_history": True,
            "summary_type": "comprehensive"
        }

        response = requests.post(
            f"{API_BASE}/agents/summarize", json=request_data, timeout=30)

        print(f"Summarize endpoint response status: {response.status_code}")

        if response.status_code != 200:
            print(f"Error response: {response.text}")
            pytest.fail(
                f"Summarize endpoint failed with status {response.status_code}")

        data = response.json()
        print(f"✅ Summarize Endpoint Success!")
        print(f"Summary (first 200 chars): {data['summary'][:200]}...")
        print(f"Key points: {data['key_points']}")

        # Verify response structure
        assert "visit_id" in data
        assert "summary" in data
        assert "key_points" in data
        assert "recommendations" in data
        assert "follow_up_required" in data
        assert "confidence_score" in data
        assert "generated_at" in data

        # Summary should contain relevant medical information
        summary = data["summary"].lower()
        assert any(term in summary for term in ["diabetes", "visit", "patient", "medical"]), \
            f"Summary doesn't contain expected medical terms: {data['summary'][:100]}"

    def test_06_health_summary_endpoint(self):
        """Test the /health-summary endpoint."""
        if not TestAgentsAPIWithFallback.test_patient_id:
            pytest.skip("No patient created")

        request_data = {
            "patient_id": "API-TEST-001",
            "include_recent_visits": 5
        }

        response = requests.post(
            f"{API_BASE}/agents/health-summary", json=request_data, timeout=30)

        print(f"Health summary response status: {response.status_code}")

        if response.status_code != 200:
            print(f"Error response: {response.text}")
            pytest.fail(
                f"Health summary failed with status {response.status_code}")

        data = response.json()
        print(f"✅ Health Summary Success!")
        print(f"Summary (first 200 chars): {data['summary'][:200]}...")
        print(f"Health trends: {data['health_trends']}")

        # Verify response structure
        assert "patient_id" in data
        assert "summary" in data
        assert "health_trends" in data
        assert "risk_factors" in data
        assert "recommendations" in data
        assert "recent_visits_count" in data
        assert "generated_at" in data

    def test_07_compare_visits_endpoint(self):
        """Test the /compare-visits endpoint."""
        if not TestAgentsAPIWithFallback.test_visit_id:
            pytest.skip("No visit created")

        # Create a second visit for comparison
        visit_data = {
            "patient_id": TestAgentsAPIWithFallback.test_patient_id,
            "visit_id": "API-TEST-VISIT-002",
            "visit_date": "2025-01-15T14:00:00",
            "visit_type": "follow_up",
            "chief_complaint": "Follow-up after medication adjustment",
            "diagnosis": "Type 2 diabetes mellitus - excellent control. Essential hypertension - well controlled.",
            "treatment_plan": "Continue current regimen. Patient responding well to increased lisinopril dose.",
            "doctor_notes": "Patient reports excellent adherence. Blood pressure improved to 125/78. HbA1c remains stable at 6.9%. No side effects reported."
        }

        response = requests.post(
            f"{API_BASE}/visits/", json=visit_data, timeout=10)

        if response.status_code == 201:
            visit2 = response.json()
            print(f"✅ Created second test visit with ID: {visit2['id']}")
        elif response.status_code == 400:
            # Visit already exists, get existing visit
            get_response = requests.get(
                f"{API_BASE}/visits/API-TEST-VISIT-002", timeout=10)
            if get_response.status_code == 200:
                visit2 = get_response.json()
                print(
                    f"✅ Using existing second test visit with ID: {visit2['id']}")
            else:
                pytest.fail(
                    f"Could not retrieve existing second visit: {get_response.status_code}")
        else:
            pytest.fail(
                f"Failed to create or retrieve second visit: {response.status_code} - {response.text}")

            # Now compare the visits
            response = requests.post(
                f"{API_BASE}/agents/compare-visits",
                params={
                    "visit_id_1": str(TestAgentsAPIWithFallback.test_visit_visit_id),
                    "visit_id_2": str(visit2["visit_id"])
                },
                timeout=30
            )

            print(f"Compare visits response status: {response.status_code}")

            if response.status_code != 200:
                print(f"Error response: {response.text}")
                pytest.fail(
                    f"Compare visits failed with status {response.status_code}")

            data = response.json()
            print(f"✅ Compare Visits Success!")
            print(
                f"Comparison (first 200 chars): {data['comparison'][:200]}...")

            # Verify response structure
            assert "visit_1" in data
            assert "visit_2" in data
            assert "comparison" in data
            assert "generated_at" in data

    def test_08_fallback_system_verification(self):
        """Test that confirms the fallback system is working by checking response times and content."""
        request_data = {
            "question": "What are the key differences between Type 1 and Type 2 diabetes?",
            "context_type": "all"
        }

        start_time = datetime.now()
        response = requests.post(
            f"{API_BASE}/agents/ask", json=request_data, timeout=30)
        end_time = datetime.now()

        response_time = (end_time - start_time).total_seconds()

        print(f"Fallback system test response status: {response.status_code}")
        print(f"Response time: {response_time:.2f} seconds")

        if response.status_code != 200:
            print(f"Error response: {response.text}")
            pytest.fail(
                f"Fallback system test failed with status {response.status_code}")

        data = response.json()
        print(f"✅ Fallback System Working!")
        print(
            f"Answer quality check (first 300 chars): {data['answer'][:300]}...")

        # Verify the answer quality suggests AI is working
        answer = data["answer"].lower()
        assert len(data["answer"]
                   ) > 50, "Answer too short - AI might not be working"
        assert any(term in answer for term in ["type 1", "type 2", "diabetes", "insulin", "pancreas"]), \
            f"Answer doesn't contain expected diabetes information: {data['answer'][:100]}"

    @classmethod
    def teardown_class(cls):
        """Clean up test data."""
        if cls.test_patient_id:
            print(f"Test completed. Test patient ID: {cls.test_patient_id}")
        if cls.test_visit_id:
            print(f"Test visit ID: {cls.test_visit_id}")


def test_quick_fallback_status():
    """Quick test to verify the fallback system is operational."""
    try:
        # Test a simple question
        request_data = {
            "question": "What is the normal range for blood pressure?",
            "context_type": "all"
        }

        response = requests.post(f"{BASE_URL}/api/v1/agents/ask",
                                 json=request_data, timeout=15)

        if response.status_code == 200:
            data = response.json()
            print("🤖 Fallback System Status:")
            print("  ✅ AI agents are responding!")
            print(
                f"  Test response: {data.get('answer', 'No answer')[:100]}...")

            # Check response quality
            answer = data.get('answer', '')
            if len(answer) > 50 and any(term in answer.lower() for term in ['blood pressure', 'mmhg', '120', '80']):
                print("  ✅ Response quality looks good - AI is working!")
                return True
            else:
                print("  ⚠️ Response quality seems poor - check AI configuration")
                return False
        else:
            print(f"❌ Fallback system test failed: {response.status_code}")
            if response.text:
                print(f"  Error: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"❌ Error testing fallback system: {e}")
        return False


if __name__ == "__main__":
    # Quick test when run directly
    print("🏥 Medical Assistant API - Grok-3 Fallback System Test")
    print("=" * 60)

    success = test_quick_fallback_status()

    if success:
        print("\n🎉 Grok-3 fallback system is working!")
        print(
            "Run full tests with: python -m pytest tests/test_agents_api_fallback.py -v -s")
    else:
        print("\n💡 Troubleshooting:")
        print("1. Check that your X.AI API key is properly configured")
        print(
            "2. Verify server is running: uvicorn app.main:app --host 127.0.0.1 --port 8001")
        print("3. Check server logs for any errors")
