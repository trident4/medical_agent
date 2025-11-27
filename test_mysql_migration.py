"""
Test MySQL migration - verify database connectivity and JSON column functionality
"""
import asyncio
import sys
from datetime import datetime, date
from sqlalchemy import select
from app.database.session import AsyncSessionLocal, engine
from app.models.patient import Patient
from app.models.visit import Visit


async def test_mysql_connection():
    """Test MySQL database connection and JSON column functionality."""
    
    print("🔍 Testing MySQL Migration...")
    print(f"📊 Database URL: {engine.url}")
    print(f"📦 Dialect: {engine.dialect.name}")
    
    async with AsyncSessionLocal() as session:
        try:
            # Test 1: Create a test patient
            print("\n✅ Test 1: Creating test patient...")
            test_patient = Patient(
                patient_id="TEST001",
                first_name="MySQL",
                last_name="Test",
                date_of_birth=date(1990, 1, 1),
                gender="Other",
                email="mysql.test@example.com"
            )
            session.add(test_patient)
            await session.commit()
            await session.refresh(test_patient)
            print(f"   Created patient ID: {test_patient.id}")
            
            # Test 2: Create a visit with JSON data
            print("\n✅ Test 2: Creating visit with JSON data...")
            test_visit = Visit(
                visit_id="VISIT001",
                patient_id=test_patient.id,
                visit_date=datetime.now(),
                visit_type="routine",
                chief_complaint="Testing JSON columns",
                vital_signs={
                    "blood_pressure_systolic": 120,
                    "blood_pressure_diastolic": 80,
                    "heart_rate": 72,
                    "temperature": 98.6
                },
                lab_results=[
                    {
                        "test_name": "Blood Glucose",
                        "value": "95",
                        "unit": "mg/dL",
                        "status": "normal"
                    }
                ]
            )
            session.add(test_visit)
            await session.commit()
            await session.refresh(test_visit)
            print(f"   Created visit ID: {test_visit.id}")
            print(f"   Vital signs: {test_visit.vital_signs}")
            print(f"   Lab results: {test_visit.lab_results}")
            
            # Test 3: Query and verify JSON data
            print("\n✅ Test 3: Querying and verifying JSON data...")
            result = await session.execute(
                select(Visit).where(Visit.id == test_visit.id)
            )
            retrieved_visit = result.scalar_one()
            
            assert retrieved_visit.vital_signs["heart_rate"] == 72
            assert retrieved_visit.lab_results[0]["test_name"] == "Blood Glucose"
            print("   JSON data retrieved and verified successfully!")
            
            # Cleanup
            print("\n🧹 Cleaning up test data...")
            await session.delete(test_visit)
            await session.delete(test_patient)
            await session.commit()
            
            print("\n🎉 All tests passed! MySQL migration successful!")
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            await session.rollback()
            return False


if __name__ == "__main__":
    success = asyncio.run(test_mysql_connection())
    sys.exit(0 if success else 1)
