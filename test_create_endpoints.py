#!/usr/bin/env python3
"""
Test script for creating new patients and visits via the API.
"""

import requests
import json
from datetime import datetime, date

BASE_URL = "http://localhost:8000/api/v1"


def test_create_patient():
    """Test creating a new patient."""
    print("🏥 Testing Patient Creation")
    print("=" * 50)

    # New patient data
    new_patient = {
        "patient_id": "PAT006",
        "first_name": "Maria",
        "last_name": "Rodriguez",
        "date_of_birth": "1990-08-14",
        "gender": "Female",
        "phone": "(555) 678-9012",
        "email": "maria.rodriguez@email.com",
        "address": "987 Sunset Blvd, San Francisco, CA 94122",
        "emergency_contact": "Carlos Rodriguez (Husband) - (555) 678-9013",
        "medical_history": "Gestational diabetes 2018, Otherwise healthy",
        "allergies": "No known allergies",
        "current_medications": "Prenatal vitamins daily"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/patients",
            json=new_patient,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 201:
            print("✅ Patient created successfully!")
            patient_data = response.json()
            print(f"📋 Patient ID: {patient_data['patient_id']}")
            print(
                f"👤 Name: {patient_data['first_name']} {patient_data['last_name']}")
            print(f"📧 Email: {patient_data['email']}")
            return patient_data['patient_id']
        elif response.status_code == 400:
            print(
                "⚠️  Patient already exists (this is expected if running multiple times)")
            return "PAT006"
        else:
            print(f"❌ Failed to create patient: {response.status_code}")
            print(f"Error: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None


def test_create_visit(patient_id):
    """Test creating a new visit for a patient."""
    print(f"\n📋 Testing Visit Creation for {patient_id}")
    print("=" * 50)

    # New visit data
    new_visit = {
        "visit_id": "VIS006",
        "patient_id": patient_id,
        "visit_date": datetime.now().isoformat(),
        "visit_type": "routine",
        "chief_complaint": "Routine prenatal check-up - 28 weeks",
        "symptoms": "Mild back pain, occasional heartburn, fetal movement active",
        "diagnosis": "Normal pregnancy at 28 weeks gestation",
        "treatment_plan": "Continue prenatal vitamins, glucose tolerance test ordered",
        "medications_prescribed": "Continue current prenatal vitamins",
        "follow_up_instructions": "Return in 2 weeks, glucose screening results review",
        "doctor_notes": "Fundal height appropriate for gestational age. Fetal heart rate 145 bpm. Patient reports good fetal movement. Discussed nutrition and exercise.",
        "vital_signs": json.dumps({
            "blood_pressure_systolic": 118,
            "blood_pressure_diastolic": 75,
            "heart_rate": 88,
            "temperature": 98.4,
            "weight": 145,
            "height": 64,
            "fundal_height": 28
        }),
        "lab_results": json.dumps([
            {"test_name": "Glucose tolerance test",
                "value": "Pending", "status": "pending"},
            {"test_name": "Hemoglobin", "value": "11.8",
                "unit": "g/dL", "status": "normal"},
            {"test_name": "Urine protein", "value": "Negative", "status": "normal"}
        ]),
        "duration_minutes": 30
    }

    try:
        response = requests.post(
            f"{BASE_URL}/visits",
            json=new_visit,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 201:
            print("✅ Visit created successfully!")
            visit_data = response.json()
            print(f"📋 Visit ID: {visit_data['visit_id']}")
            print(f"🏥 Type: {visit_data['visit_type']}")
            print(f"💬 Chief Complaint: {visit_data['chief_complaint']}")
            return visit_data['visit_id']
        elif response.status_code == 400:
            print("⚠️  Visit already exists (this is expected if running multiple times)")
            return "VIS006"
        else:
            print(f"❌ Failed to create visit: {response.status_code}")
            print(f"Error: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None


def verify_creation():
    """Verify the created patient and visit can be retrieved."""
    print(f"\n🔍 Verifying Created Data")
    print("=" * 50)

    try:
        # Get the new patient
        patient_response = requests.get(
            f"{BASE_URL}/patients/PAT006", timeout=10)
        if patient_response.status_code == 200:
            patient = patient_response.json()
            print(
                f"✅ Patient Retrieved: {patient['first_name']} {patient['last_name']}")

        # Get the new visit
        visit_response = requests.get(f"{BASE_URL}/visits/VIS006", timeout=10)
        if visit_response.status_code == 200:
            visit = visit_response.json()
            print(f"✅ Visit Retrieved: {visit['chief_complaint']}")

        # Get patient's visits
        visits_response = requests.get(
            f"{BASE_URL}/patients/PAT006/visits", timeout=10)
        if visits_response.status_code == 200:
            visits = visits_response.json()
            print(f"✅ Patient has {len(visits)} visit(s)")

    except requests.exceptions.RequestException as e:
        print(f"❌ Verification error: {e}")


def test_bulk_creation():
    """Test creating multiple patients and visits."""
    print(f"\n👥 Testing Bulk Creation")
    print("=" * 50)

    # Additional patients
    patients = [
        {
            "patient_id": "PAT007",
            "first_name": "James",
            "last_name": "Wilson",
            "date_of_birth": "1972-11-03",
            "gender": "Male",
            "phone": "(555) 789-0123",
            "email": "james.wilson@email.com",
            "address": "456 Market St, San Francisco, CA 94102",
            "emergency_contact": "Susan Wilson (Wife) - (555) 789-0124",
            "medical_history": "High blood pressure, arthritis",
            "allergies": "Ibuprofen (stomach irritation)",
            "current_medications": "Lisinopril 5mg daily, Acetaminophen as needed"
        },
        {
            "patient_id": "PAT008",
            "first_name": "Lisa",
            "last_name": "Kim",
            "date_of_birth": "1988-02-28",
            "gender": "Female",
            "phone": "(555) 890-1234",
            "email": "lisa.kim@email.com",
            "address": "789 California St, San Francisco, CA 94108",
            "emergency_contact": "David Kim (Brother) - (555) 890-1235",
            "medical_history": "Seasonal allergies, previous appendectomy 2010",
            "allergies": "Tree pollen, ragweed",
            "current_medications": "Zyrtec 10mg daily during allergy season"
        }
    ]

    created_patients = []

    for patient_data in patients:
        try:
            response = requests.post(
                f"{BASE_URL}/patients",
                json=patient_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 201:
                patient = response.json()
                created_patients.append(patient['patient_id'])
                print(
                    f"✅ Created: {patient['first_name']} {patient['last_name']} ({patient['patient_id']})")
            elif response.status_code == 400:
                created_patients.append(patient_data['patient_id'])
                print(f"⚠️  {patient_data['patient_id']} already exists")

        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating {patient_data['patient_id']}: {e}")

    return created_patients


def main():
    """Main test function."""
    print("🏥 Medical Assistant API - Create Endpoints Test")
    print("=" * 60)
    print(f"🌐 Server: {BASE_URL}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test individual patient creation
    patient_id = test_create_patient()

    if patient_id:
        # Test visit creation for the new patient
        visit_id = test_create_visit(patient_id)

        if visit_id:
            # Verify the created data
            verify_creation()

    # Test bulk creation
    bulk_patients = test_bulk_creation()

    print(f"\n🎉 Creation Tests Complete!")
    print("=" * 60)
    print(f"✅ Total patients in system: Check via GET /api/v1/patients")
    print(f"✅ Total visits in system: Check via GET /api/v1/visits")
    print(f"🌐 View in browser: http://localhost:8001/docs")

    print(f"\n📊 Quick verification commands:")
    print(f"curl {BASE_URL}/patients/PAT006")
    print(f"curl {BASE_URL}/visits/VIS006")
    print(f"curl {BASE_URL}/patients/PAT006/visits")


if __name__ == "__main__":
    main()
