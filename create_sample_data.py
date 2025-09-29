#!/usr/bin/env python3
"""
Script to create sample patient and visit data for testing the Medical Assistant API.
"""

import asyncio
import json
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.patient import Patient
from app.models.visit import Visit


# Sample patient data
SAMPLE_PATIENTS = [
    {
        "patient_id": "PAT001",
        "first_name": "John",
        "last_name": "Smith",
        "date_of_birth": date(1985, 3, 15),
        "gender": "Male",
        "phone": "(555) 123-4567",
        "email": "john.smith@email.com",
        "address": "123 Main St, San Francisco, CA 94105",
        "emergency_contact": "Jane Smith (Wife) - (555) 123-4568",
        "medical_history": "Hypertension diagnosed 2018, Family history of diabetes",
        "allergies": "Penicillin (severe reaction), Shellfish (mild)",
        "current_medications": "Lisinopril 10mg daily, Metformin 500mg twice daily"
    },
    {
        "patient_id": "PAT002",
        "first_name": "Sarah",
        "last_name": "Johnson",
        "date_of_birth": date(1992, 7, 22),
        "gender": "Female",
        "phone": "(555) 234-5678",
        "email": "sarah.johnson@email.com",
        "address": "456 Oak Ave, San Francisco, CA 94102",
        "emergency_contact": "Michael Johnson (Brother) - (555) 234-5679",
        "medical_history": "Asthma since childhood, Seasonal allergies",
        "allergies": "Pollen, Dust mites",
        "current_medications": "Albuterol inhaler as needed, Claritin 10mg daily"
    },
    {
        "patient_id": "PAT003",
        "first_name": "Robert",
        "last_name": "Davis",
        "date_of_birth": date(1978, 12, 5),
        "gender": "Male",
        "phone": "(555) 345-6789",
        "email": "robert.davis@email.com",
        "address": "789 Pine St, San Francisco, CA 94108",
        "emergency_contact": "Linda Davis (Wife) - (555) 345-6790",
        "medical_history": "Type 2 Diabetes diagnosed 2020, High cholesterol",
        "allergies": "No known allergies",
        "current_medications": "Metformin 1000mg twice daily, Atorvastatin 20mg daily"
    },
    {
        "patient_id": "PAT004",
        "first_name": "Emily",
        "last_name": "Chen",
        "date_of_birth": date(1995, 9, 18),
        "gender": "Female",
        "phone": "(555) 456-7890",
        "email": "emily.chen@email.com",
        "address": "321 Elm St, San Francisco, CA 94110",
        "emergency_contact": "David Chen (Father) - (555) 456-7891",
        "medical_history": "Generally healthy, Previous ankle fracture 2019",
        "allergies": "Latex (contact dermatitis)",
        "current_medications": "Multivitamin daily, Birth control pill"
    },
    {
        "patient_id": "PAT005",
        "first_name": "Michael",
        "last_name": "Brown",
        "date_of_birth": date(1965, 4, 30),
        "gender": "Male",
        "phone": "(555) 567-8901",
        "email": "michael.brown@email.com",
        "address": "654 Cedar Rd, San Francisco, CA 94115",
        "emergency_contact": "Patricia Brown (Wife) - (555) 567-8902",
        "medical_history": "Coronary artery disease, Previous MI 2019, Hypertension",
        "allergies": "Aspirin (gastric irritation)",
        "current_medications": "Clopidogrel 75mg daily, Metoprolol 50mg twice daily, Rosuvastatin 40mg daily"
    }
]


def create_sample_visits(patient_ids):
    """Create sample visit data for the patients."""
    visits = []

    # John Smith (PAT001) - Hypertension follow-up
    visits.append({
        "visit_id": "VIS001",
        "patient_id": patient_ids["PAT001"],
        "visit_date": datetime.now() - timedelta(days=30),
        "visit_type": "follow-up",
        "chief_complaint": "Routine hypertension follow-up",
        "symptoms": "No acute symptoms, occasional mild headaches",
        "diagnosis": "Essential hypertension, well controlled",
        "treatment_plan": "Continue current medications, lifestyle modifications",
        "medications_prescribed": "Lisinopril 10mg daily (continued)",
        "follow_up_instructions": "Return in 3 months, monitor BP at home",
        "doctor_notes": "BP well controlled on current regimen. Patient compliant with medications. Discussed diet and exercise.",
        "vital_signs": json.dumps({
            "blood_pressure_systolic": 128,
            "blood_pressure_diastolic": 82,
            "heart_rate": 72,
            "temperature": 98.6,
            "weight": 180,
            "height": 70
        }),
        "lab_results": json.dumps([
            {"test_name": "Basic Metabolic Panel",
                "value": "Normal", "status": "normal"},
            {"test_name": "HbA1c", "value": "6.8%",
                "unit": "%", "status": "elevated"}
        ]),
        "duration_minutes": 20
    })

    # Sarah Johnson (PAT002) - Asthma exacerbation
    visits.append({
        "visit_id": "VIS002",
        "patient_id": patient_ids["PAT002"],
        "visit_date": datetime.now() - timedelta(days=15),
        "visit_type": "urgent",
        "chief_complaint": "Shortness of breath and wheezing",
        "symptoms": "Increased wheezing, shortness of breath with minimal exertion, cough with clear sputum",
        "diagnosis": "Acute asthma exacerbation, likely triggered by seasonal allergens",
        "treatment_plan": "Nebulizer treatment, prednisone course, increase controller therapy",
        "medications_prescribed": "Prednisone 40mg daily x 5 days, Increase albuterol use",
        "follow_up_instructions": "Return if symptoms worsen, follow up in 1 week",
        "doctor_notes": "Moderate asthma exacerbation. Good response to nebulizer. Peak flow 320 (baseline 380).",
        "vital_signs": json.dumps({
            "blood_pressure_systolic": 110,
            "blood_pressure_diastolic": 70,
            "heart_rate": 88,
            "temperature": 98.4,
            "respiratory_rate": 22,
            "oxygen_saturation": 96,
            "weight": 135,
            "height": 64
        }),
        "duration_minutes": 35
    })

    # Robert Davis (PAT003) - Diabetes management
    visits.append({
        "visit_id": "VIS003",
        "patient_id": patient_ids["PAT003"],
        "visit_date": datetime.now() - timedelta(days=45),
        "visit_type": "routine",
        "chief_complaint": "Diabetes management and routine check-up",
        "symptoms": "Occasional fatigue, increased thirst",
        "diagnosis": "Type 2 Diabetes Mellitus, suboptimal control",
        "treatment_plan": "Increase metformin dose, dietary counseling, exercise program",
        "medications_prescribed": "Metformin increased to 1000mg twice daily",
        "follow_up_instructions": "Return in 6 weeks for glucose check, start glucose monitoring",
        "doctor_notes": "HbA1c elevated at 8.2%. Discussed diet modifications and exercise. Patient motivated to improve control.",
        "vital_signs": json.dumps({
            "blood_pressure_systolic": 135,
            "blood_pressure_diastolic": 85,
            "heart_rate": 76,
            "temperature": 98.7,
            "weight": 210,
            "height": 72
        }),
        "lab_results": json.dumps([
            {"test_name": "HbA1c", "value": "8.2%",
                "unit": "%", "status": "elevated"},
            {"test_name": "Fasting Glucose", "value": "165",
                "unit": "mg/dL", "status": "elevated"},
            {"test_name": "Total Cholesterol", "value": "195",
                "unit": "mg/dL", "status": "normal"}
        ]),
        "duration_minutes": 30
    })

    # Emily Chen (PAT004) - Annual physical
    visits.append({
        "visit_id": "VIS004",
        "patient_id": patient_ids["PAT004"],
        "visit_date": datetime.now() - timedelta(days=10),
        "visit_type": "routine",
        "chief_complaint": "Annual physical examination",
        "symptoms": "No acute complaints, feeling well",
        "diagnosis": "Healthy young adult, up to date with preventive care",
        "treatment_plan": "Continue current health maintenance, update vaccinations",
        "medications_prescribed": "Continue current medications",
        "follow_up_instructions": "Return in 1 year for annual physical",
        "doctor_notes": "Excellent health. Normal physical exam. Discussed contraception options and preventive care.",
        "vital_signs": json.dumps({
            "blood_pressure_systolic": 108,
            "blood_pressure_diastolic": 68,
            "heart_rate": 65,
            "temperature": 98.3,
            "weight": 125,
            "height": 65
        }),
        "lab_results": json.dumps([
            {"test_name": "Complete Blood Count",
                "value": "Normal", "status": "normal"},
            {"test_name": "Lipid Panel", "value": "Normal", "status": "normal"}
        ]),
        "duration_minutes": 25
    })

    # Michael Brown (PAT005) - Cardiology follow-up
    visits.append({
        "visit_id": "VIS005",
        "patient_id": patient_ids["PAT005"],
        "visit_date": datetime.now() - timedelta(days=7),
        "visit_type": "follow-up",
        "chief_complaint": "Cardiology follow-up post-MI",
        "symptoms": "Mild chest discomfort with exertion, improved exercise tolerance",
        "diagnosis": "Coronary artery disease, stable angina, post-MI",
        "treatment_plan": "Continue dual antiplatelet therapy, cardiac rehabilitation",
        "medications_prescribed": "Continue current cardiac medications",
        "follow_up_instructions": "Return in 3 months, continue cardiac rehab, stress test in 6 months",
        "doctor_notes": "Stable CAD. Good progress in cardiac rehab. EKG shows old inferior MI, no acute changes.",
        "vital_signs": json.dumps({
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 75,
            "heart_rate": 62,
            "temperature": 98.5,
            "weight": 195,
            "height": 71
        }),
        "lab_results": json.dumps([
            {"test_name": "Troponin", "value": "<0.01",
                "unit": "ng/mL", "status": "normal"},
            {"test_name": "BNP", "value": "45",
                "unit": "pg/mL", "status": "normal"},
            {"test_name": "Lipid Panel", "value": "LDL 85 mg/dL", "status": "target"}
        ]),
        "duration_minutes": 40
    })

    return visits


async def create_sample_data():
    """Create sample patients and visits in the database."""
    try:
        # Create database engine and session
        db_url = settings.DATABASE_URL.replace(
            "postgresql://", "postgresql+asyncpg://")
        engine = create_async_engine(db_url)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            print("🏥 Creating sample patient data...")

            # Create patients
            patient_ids = {}
            for patient_data in SAMPLE_PATIENTS:
                patient = Patient(**patient_data)
                session.add(patient)
                await session.flush()  # Get the ID without committing
                patient_ids[patient_data["patient_id"]] = patient.id
                print(
                    f"   ✅ Created patient: {patient.first_name} {patient.last_name} (ID: {patient.patient_id})")

            print("\n📋 Creating sample visit data...")

            # Create visits
            visits_data = create_sample_visits(patient_ids)
            for visit_data in visits_data:
                visit = Visit(**visit_data)
                session.add(visit)
                await session.flush()
                patient_name = next(p["first_name"] + " " + p["last_name"]
                                    for p in SAMPLE_PATIENTS if patient_ids[p["patient_id"]] == visit.patient_id)
                print(
                    f"   ✅ Created visit: {visit.visit_id} for {patient_name} ({visit.visit_type})")

            # Commit all changes
            await session.commit()
            print(
                f"\n🎉 Successfully created {len(SAMPLE_PATIENTS)} patients and {len(visits_data)} visits!")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_data():
    """Verify the sample data was created correctly."""
    try:
        db_url = settings.DATABASE_URL.replace(
            "postgresql://", "postgresql+asyncpg://")
        engine = create_async_engine(db_url)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # Count patients
            from sqlalchemy import func, select
            patient_count = await session.execute(select(func.count(Patient.id)))
            patient_total = patient_count.scalar()

            # Count visits
            visit_count = await session.execute(select(func.count(Visit.id)))
            visit_total = visit_count.scalar()

            print(f"\n📊 Database Summary:")
            print(f"   Patients: {patient_total}")
            print(f"   Visits: {visit_total}")

            # Show sample patient
            sample_patient = await session.execute(
                select(Patient).where(Patient.patient_id == "PAT001")
            )
            patient = sample_patient.scalar_one_or_none()

            if patient:
                print(
                    f"\n👤 Sample Patient: {patient.first_name} {patient.last_name}")
                print(f"   Patient ID: {patient.patient_id}")
                print(
                    f"   Age: {(date.today() - patient.date_of_birth).days // 365}")
                print(f"   Medical History: {patient.medical_history}")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"❌ Error verifying data: {e}")
        return False


def print_api_examples():
    """Print examples of how to use the API with the sample data."""
    print("\n" + "="*60)
    print("🚀 API Testing Examples")
    print("="*60)

    print("\n📋 Test the API with curl commands:")
    print("\n1. Get all patients:")
    print("   curl http://localhost:8000/api/v1/patients")

    print("\n2. Get specific patient:")
    print("   curl http://localhost:8000/api/v1/patients/PAT001")

    print("\n3. Get patient's visits:")
    print("   curl http://localhost:8000/api/v1/patients/PAT001/visits")

    print("\n4. Get all visits:")
    print("   curl http://localhost:8000/api/v1/visits")

    print("\n5. Get specific visit:")
    print("   curl http://localhost:8000/api/v1/visits/VIS001")

    print("\n🌐 Or use the interactive API documentation:")
    print("   http://localhost:8000/docs")

    print("\n📊 Database access:")
    print("   psql doctors_assistant")
    print("   SELECT * FROM patients;")
    print("   SELECT * FROM visits;")


async def main():
    """Main function to create and verify sample data."""
    print("🏥 Medical Assistant - Sample Data Creator")
    print("="*50)

    # Create sample data
    success = await create_sample_data()

    if success:
        # Verify data
        await verify_data()

        # Print usage examples
        print_api_examples()

        print(f"\n✨ Sample data creation complete!")
        print("Your medical assistant now has realistic test data to work with.")
    else:
        print("\n❌ Failed to create sample data. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
