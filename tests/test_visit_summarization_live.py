"""
Integration tests for visit summarization API with real grok-3 fallback.
Run these tests against a running server to test the actual AI integration.
"""

import requests
import json
import pytest
from datetime import date

# Test configuration
BASE_URL = "http://localhost:8001"  # Adjust port if needed
API_BASE = f"{BASE_URL}/api/v1"


class TestLiveVisitSummarization:
    """Live integration tests for visit summarization with grok-3."""

    @classmethod
    def setup_class(cls):
        """Setup test data by creating a patient and visit."""
        cls.patient_id = None
        cls.visit_id = None

        # Check if server is running
        try:
            response = requests.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            print("✅ Server is running")
        except requests.exceptions.ConnectionError:
            pytest.skip(
                "Server not running. Start with: uvicorn app.main_dev:app --host 127.0.0.1 --port 8001")

    def test_00_server_status(self):
        """Test server is running and AI agents are configured."""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200

        data = response.json()
        print(f"Server status: {data}")

        # Check AI status
        if "ai_enabled" in data:
            print(f"AI enabled: {data['ai_enabled']}")

    def test_01_ai_agent_status(self):
        """Test AI agent availability by checking endpoints."""
        # Check if AI endpoints exist by testing summarize endpoint with invalid data
        response = requests.post(f"{API_BASE}/agents/summarize",
                                 json={"visit_id": "test_invalid"})

        if response.status_code == 404:
            pytest.skip(
                "AI endpoints not available - check API key configuration")

        print(f"AI Endpoint Test Response: {response.status_code}")

        # Should get 422 (validation error) or 500 (server error) if endpoint exists, not 404
        if response.status_code in [422, 500]:
            print("✅ AI endpoints are available")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")

        # List available AI endpoints from OpenAPI spec
        response = requests.get(f"{BASE_URL}/api/v1/openapi.json")
        if response.status_code == 200:
            openapi_data = response.json()
            ai_endpoints = [path for path in openapi_data.get("paths", {}).keys()
                            if "agents" in path]
            print(f"Available AI endpoints: {ai_endpoints}")

    def test_02_create_test_patient(self):
        """Create a test patient for visit summarization."""
        patient_data = {
            "patient_id": "TEST-SUM-001",
            "first_name": "Integration",
            "last_name": "TestPatient",
            "date_of_birth": "1985-06-15",
            "gender": "female",
            "email": "integration.test@example.com",
            "phone": "555-0199",
            "address": "123 Test Street, Test City, TC 12345",
            "emergency_contact": "Test Emergency Contact: 555-0911",
            "medical_history": "Hypertension managed with lisinopril. History of seasonal allergies."
        }

        response = requests.post(f"{API_BASE}/patients/", json=patient_data)
        assert response.status_code == 201

        patient = response.json()
        TestLiveVisitSummarization.patient_id = patient["id"]
        print(f"✅ Created test patient with ID: {patient['id']}")

        return patient

    def test_03_create_test_visit(self):
        """Create a test visit for summarization."""
        if not TestLiveVisitSummarization.patient_id:
            pytest.skip("No patient created")

        visit_data = {
            "patient_id": TestLiveVisitSummarization.patient_id,
            "visit_date": "2024-12-15",
            "visit_type": "routine_checkup",
            "chief_complaint": "Annual physical examination and blood pressure check",
            "diagnosis": "Essential hypertension - well controlled. Overall health excellent.",
            "treatment_plan": "Continue current lisinopril 10mg daily. Increase physical activity to 150 minutes per week. Follow Mediterranean diet principles.",
            "notes": "Patient reports feeling well with no new symptoms. Blood pressure today 128/82, improved from last visit. Weight stable at 145 lbs. Laboratory results pending - CBC, CMP, lipid panel, A1C ordered. Patient educated on DASH diet and stress management techniques. Next appointment in 6 months or sooner if concerns arise.",
            "follow_up_date": "2025-06-15"
        }

        response = requests.post(f"{API_BASE}/visits/", json=visit_data)
        assert response.status_code == 201

        visit = response.json()
        TestLiveVisitSummarization.visit_id = visit["id"]
        print(f"✅ Created test visit with ID: {visit['id']}")

        return visit

    def test_04_test_ai_providers(self):
        """Test the AI provider fallback system by making a simple ask request."""
        test_request = {
            "question": "Hello, can you confirm you are working?",
            "context": "This is a test to verify AI functionality"
        }

        response = requests.post(
            f"{API_BASE}/agents/ask", json=test_request, timeout=10)

        if response.status_code == 404:
            pytest.skip("AI ask endpoint not available")

        if response.status_code != 200:
            print(f"AI test failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            pytest.fail(f"AI test failed with status {response.status_code}")

        data = response.json()

        print(f"AI Provider Test Results:")
        print(f"Test Question: {test_request['question']}")
        print(f"Test Answer: {data.get('answer', 'N/A')[:100]}...")

        if 'provider' in data:
            print(f"Active Provider: {data['provider']}")

        # Should have some kind of response
        assert "answer" in data
        assert len(data["answer"]) > 0

    def test_05_summarize_visit_basic(self):
        """Test basic visit summarization."""
        if not TestLiveVisitSummarization.visit_id:
            pytest.skip("No visit created")

        request_data = {
            "visit_id": str(TestLiveVisitSummarization.visit_id),
            "include_patient_history": True,
            "summary_type": "comprehensive"
        }

        response = requests.post(
            f"{API_BASE}/agents/summarize", json=request_data, timeout=10)

        if response.status_code == 404:
            pytest.skip("AI summarization endpoint not available")

        print(f"Summarization response status: {response.status_code}")

        if response.status_code != 200:
            print(f"Error response: {response.text}")
            pytest.fail(
                f"Summarization failed with status {response.status_code}")

        data = response.json()
        print(f"✅ Visit Summarization Success!")
        print(f"Summary (first 200 chars): {data['summary'][:200]}...")
        print(f"Available Providers: {data.get('available_providers', [])}")

        # Verify response structure
        assert "summary" in data
        assert "visit_id" in data
        assert "patient_id" in data
        assert data["visit_id"] == TestLiveVisitSummarization.visit_id

        # Summary should contain relevant medical information
        summary = data["summary"].lower()
        assert any(term in summary for term in ["hypertension", "blood pressure", "physical", "patient"]), \
            f"Summary doesn't contain expected medical terms: {data['summary'][:100]}"

    def test_06_summarize_patient_history(self):
        """Test patient history summarization."""
        if not TestLiveVisitSummarization.patient_id:
            pytest.skip("No patient created")

        request_data = {
            "question": f"Please provide a comprehensive medical history summary for patient {TestLiveVisitSummarization.patient_id}",
            "context": f"patient_id: {TestLiveVisitSummarization.patient_id}"
        }

        response = requests.post(
            f"{API_BASE}/agents/ask", json=request_data, timeout=10)

        if response.status_code == 404:
            pytest.skip("AI patient history endpoint not available")

        print(f"Patient history response status: {response.status_code}")

        if response.status_code != 200:
            print(f"Error response: {response.text}")
            pytest.fail(
                f"Patient history summarization failed with status {response.status_code}")

        data = response.json()
        print(f"✅ Patient History Summarization Success!")
        print(f"History Summary (first 200 chars): {data['answer'][:200]}...")

        # Verify response structure
        assert "answer" in data
        assert "question" in data

    def test_07_create_discharge_summary(self):
        """Test discharge summary creation."""
        if not TestLiveVisitSummarization.visit_id:
            pytest.skip("No visit created")

        request_data = {
            "visit_id": str(TestLiveVisitSummarization.visit_id),
            "include_patient_history": True,
            "summary_type": "comprehensive"
        }

        response = requests.post(
            f"{API_BASE}/agents/discharge-summary", json=request_data, timeout=10)

        if response.status_code == 404:
            pytest.skip("AI discharge summary endpoint not available")

        print(f"Discharge summary response status: {response.status_code}")

        if response.status_code != 200:
            print(f"Error response: {response.text}")
            pytest.fail(
                f"Discharge summary creation failed with status {response.status_code}")

        data = response.json()
        print(f"✅ Discharge Summary Creation Success!")
        print(
            f"Discharge Summary (first 200 chars): {data['discharge_summary'][:200]}...")

        # Verify response structure
        assert "discharge_summary" in data
        assert "visit_id" in data
        assert "patient_id" in data

    def test_08_test_fallback_scenarios(self):
        """Test different medical scenarios to verify grok-3 handles various cases."""
        if not TestLiveVisitSummarization.patient_id:
            pytest.skip("No patient created")

        # Create an emergency visit scenario
        emergency_visit_data = {
            "patient_id": TestLiveVisitSummarization.patient_id,
            "visit_date": "2024-12-16",
            "visit_type": "emergency",
            "chief_complaint": "Chest pain with shortness of breath",
            "diagnosis": "Non-cardiac chest pain, anxiety-related. EKG normal, troponins negative.",
            "treatment_plan": "Discharge home with anxiolytic as needed. Follow up with PCP in 1 week.",
            "notes": "35-year-old presents with acute onset chest pain. No radiation. Associated with work stress. Vital signs stable. Physical exam unremarkable. EKG shows normal sinus rhythm. Chest X-ray clear."
        }

        # Create emergency visit
        response = requests.post(
            f"{API_BASE}/visits/", json=emergency_visit_data, timeout=10)
        if response.status_code == 201:
            emergency_visit = response.json()

            # Test summarization of emergency visit
            request_data = {
                "visit_id": str(emergency_visit["id"]),
                "include_patient_history": True,
                "summary_type": "comprehensive"
            }

            response = requests.post(
                f"{API_BASE}/agents/summarize", json=request_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Emergency Visit Summarization Success!")
                print(f"Emergency Summary: {data['summary'][:200]}...")

                # Should mention emergency-related terms
                summary = data["summary"].lower()
                assert any(term in summary for term in ["chest pain", "emergency", "ekg", "cardiac"]), \
                    f"Emergency summary missing key terms: {data['summary'][:100]}"
            else:
                print(
                    f"⚠️ Emergency visit summarization failed: {response.status_code}")
        else:
            print(
                f"⚠️ Could not create emergency visit: {response.status_code}")

    @classmethod
    def teardown_class(cls):
        """Clean up test data."""
        # Note: In a real test environment, you might want to clean up
        # test data. For now, we'll leave it for manual inspection.
        if cls.patient_id:
            print(f"Test completed. Test patient ID: {cls.patient_id}")
        if cls.visit_id:
            print(f"Test visit ID: {cls.visit_id}")


# def test_quick_ai_status():
#     """Quick test to check if AI is working - can be run standalone."""
#     try:
#         # Test if AI endpoints are available by making a simple ask request
#         test_request = {
#             "question": "What is the weather like?",
#             "context": "This is a test to check if AI is working"
#         }

#         response = requests.post(f"{BASE_URL}/api/v1/agents/ask",
#                                  json=test_request, timeout=10)

#         if response.status_code == 200:
#             data = response.json()
#             print("🤖 AI Status:")
#             print("  ✅ AI agents are responding!")
#             print(
#                 f"  Test response: {data.get('answer', 'No answer')[:100]}...")

#             # Check for provider information in response
#             if 'provider' in data:
#                 print(f"  Active provider: {data['provider']}")
#                 if 'xai' in data['provider'].lower() or 'grok' in data['provider'].lower():
#                     print("  ✅ X.AI (grok-3) is active!")
#                 elif 'openai' in data['provider'].lower():
#                     print("  ✅ OpenAI is active!")
#                 elif 'anthropic' in data['provider'].lower():
#                     print("  ✅ Anthropic is active!")

#             return True
#         else:
#             print(f"❌ AI test failed: {response.status_code}")
#             if response.text:
#                 print(f"  Error: {response.text[:200]}")
#             return False
#     except requests.exceptions.ConnectionError:
#         print("❌ Cannot connect to server. Is it running?")
#         return False
#     except requests.exceptions.RequestException as e:
#         print(f"❌ Error testing AI: {e}")
#         return False


if __name__ == "__main__":
    # Quick test when run directly
    print("🏥 Medical Assistant AI - Quick Status Check")
    print("=" * 50)

    # success = test_quick_ai_status()

    # if success:
    #     print("\n🎉 Ready to run full integration tests!")
    #     print("Run with: python -m pytest tests/test_visit_summarization_live.py -v -s")
    # else:
    #     print("\n💡 To enable AI features:")
    #     print("1. Add your API keys to .env file")
    #     print("2. Start server: uvicorn app.main_dev:app --host 127.0.0.1 --port 8001")
    #     print("3. Run tests again")
