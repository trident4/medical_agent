#!/usr/bin/env python3
"""
Script to test the Medical Assistant API with sample data.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"


def test_endpoint(endpoint, description):
    """Test an API endpoint and display the results."""
    print(f"\n📋 {description}")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")

            if isinstance(data, list):
                print(f"📊 Found {len(data)} records")
                if data:
                    print(f"🔍 Sample record:")
                    print(json.dumps(data[0], indent=2, default=str))
            else:
                print("📄 Response:")
                print(json.dumps(data, indent=2, default=str))
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Error: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")

    print("-" * 60)


def main():
    """Test all API endpoints with sample data."""
    print("🏥 Medical Assistant API - Testing with Sample Data")
    print("=" * 70)
    print(f"🌐 Server: {BASE_URL}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test basic endpoints
    test_endpoint("/patients", "Get All Patients")
    test_endpoint("/patients/PAT001", "Get Specific Patient (John Smith)")
    test_endpoint("/patients/PAT001/visits", "Get Patient's Visits")
    test_endpoint("/visits", "Get All Visits")
    test_endpoint("/visits/VIS001", "Get Specific Visit")
    test_endpoint("/setup-status", "System Status")

    print("\n🎯 Quick Test Summary:")
    print("="*70)
    print("✅ If all tests passed, your Medical Assistant API is working!")
    print("🌐 Access the interactive docs at: http://localhost:8000/docs")
    print("📊 View the API schema at: http://localhost:8000/api/v1/openapi.json")

    print("\n🧪 Sample API Calls to Try:")
    print("="*70)
    print("1. List all patients:")
    print("   curl http://localhost:8000/api/v1/patients")
    print("\n2. Get patient details:")
    print("   curl http://localhost:8000/api/v1/patients/PAT002")
    print("\n3. Search visits by type:")
    print("   curl 'http://localhost:8000/api/v1/visits?visit_type=urgent'")
    print("\n4. Get visit with full details:")
    print("   curl http://localhost:8000/api/v1/visits/VIS002")

    print("\n🤖 AI Features (requires OpenAI API key):")
    print("="*70)
    print("• Visit Summarization: POST /api/v1/ai/summarize-visit")
    print("• Patient Q&A: POST /api/v1/ai/ask-about-patient")
    print("• Add your OpenAI API key to .env to enable AI features")


if __name__ == "__main__":
    main()
