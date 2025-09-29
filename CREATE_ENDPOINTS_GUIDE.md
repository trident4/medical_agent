# 🏥 Medical Assistant API - CREATE Endpoints Guide

Your Medical Assistant API includes comprehensive **CREATE endpoints** for adding new patients and visits. Here's everything you need to know about creating data via the API.

## 📋 Available CREATE Endpoints

### 1. 👥 Create Patient

**Endpoint**: `POST /api/v1/patients`  
**Purpose**: Add a new patient to the system  
**Status Code**: `201 Created` on success

### 2. 📋 Create Visit

**Endpoint**: `POST /api/v1/visits`  
**Purpose**: Add a new visit for an existing patient  
**Status Code**: `201 Created` on success

## 🔧 How to Use the CREATE Endpoints

### Interactive Documentation

**Best way to test**: Visit http://localhost:8001/docs

- Click on the **POST** endpoints
- Click "Try it out"
- Fill in the JSON data
- Execute the request

### 👥 Creating a New Patient

#### Required Fields:

- `patient_id` (string) - Unique patient identifier
- `first_name` (string) - Patient's first name
- `last_name` (string) - Patient's last name
- `date_of_birth` (date) - Format: "YYYY-MM-DD"
- `gender` (string) - Patient's gender
- `phone` (string) - Contact phone number
- `email` (string) - Email address

#### Optional Fields:

- `address` (string) - Physical address
- `emergency_contact` (string) - Emergency contact info
- `medical_history` (string) - Past medical history
- `allergies` (string) - Known allergies
- `current_medications` (string) - Current medications
- `insurance_provider` (string) - Insurance information
- `insurance_policy_number` (string) - Policy number

#### Example JSON for Patient Creation:

```json
{
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
```

#### cURL Example:

```bash
curl -X POST http://localhost:8001/api/v1/patients \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### 📋 Creating a New Visit

#### Required Fields:

- `visit_id` (string) - Unique visit identifier
- `patient_id` (string) - Must match an existing patient's patient_id
- `visit_date` (datetime) - Format: "YYYY-MM-DDTHH:MM:SS"
- `visit_type` (string) - Type of visit (routine, urgent, follow-up, etc.)
- `chief_complaint` (string) - Main reason for visit

#### Optional Fields:

- `symptoms` (string) - Patient's symptoms
- `diagnosis` (string) - Medical diagnosis
- `treatment_plan` (string) - Treatment recommendations
- `medications_prescribed` (string) - Prescribed medications
- `follow_up_instructions` (string) - Follow-up care instructions
- `doctor_notes` (string) - Doctor's notes
- `vital_signs` (JSON string) - Vital signs data
- `lab_results` (JSON string) - Laboratory test results
- `duration_minutes` (integer) - Visit duration

#### Example JSON for Visit Creation:

```json
{
  "visit_id": "VIS006",
  "patient_id": "PAT006",
  "visit_date": "2025-09-29T15:30:00",
  "visit_type": "routine",
  "chief_complaint": "Routine prenatal check-up - 28 weeks",
  "symptoms": "Mild back pain, occasional heartburn, fetal movement active",
  "diagnosis": "Normal pregnancy at 28 weeks gestation",
  "treatment_plan": "Continue prenatal vitamins, glucose tolerance test ordered",
  "medications_prescribed": "Continue current prenatal vitamins",
  "follow_up_instructions": "Return in 2 weeks, glucose screening results review",
  "doctor_notes": "Fundal height appropriate for gestational age. Fetal heart rate 145 bpm.",
  "vital_signs": "{\"blood_pressure_systolic\": 118, \"blood_pressure_diastolic\": 75, \"heart_rate\": 88, \"temperature\": 98.4, \"weight\": 145, \"fundal_height\": 28}",
  "lab_results": "[{\"test_name\": \"Glucose tolerance test\", \"value\": \"Pending\", \"status\": \"pending\"}, {\"test_name\": \"Hemoglobin\", \"value\": \"11.8\", \"unit\": \"g/dL\", \"status\": \"normal\"}]",
  "duration_minutes": 30
}
```

#### cURL Example:

```bash
curl -X POST http://localhost:8001/api/v1/visits \
  -H "Content-Type: application/json" \
  -d '{
    "visit_id": "VIS006",
    "patient_id": "PAT006",
    "visit_date": "2025-09-29T15:30:00",
    "visit_type": "routine",
    "chief_complaint": "Routine prenatal check-up - 28 weeks",
    "symptoms": "Mild back pain, occasional heartburn",
    "diagnosis": "Normal pregnancy at 28 weeks gestation",
    "treatment_plan": "Continue prenatal vitamins, glucose tolerance test ordered",
    "duration_minutes": 30
  }'
```

## ✅ Validation & Error Handling

### Patient Creation Errors:

- **400 Bad Request**: Patient ID already exists
- **422 Validation Error**: Missing required fields or invalid data format
- **500 Internal Server Error**: Database connection issues

### Visit Creation Errors:

- **400 Bad Request**: Visit ID already exists OR patient_id not found
- **422 Validation Error**: Missing required fields or invalid data format
- **500 Internal Server Error**: Database connection issues

### Example Error Response:

```json
{
  "detail": "Patient with ID PAT006 already exists"
}
```

## 🧪 Testing Workflow

### 1. Test with Interactive Docs (Recommended)

1. Open http://localhost:8001/docs
2. Find the **POST /api/v1/patients** endpoint
3. Click "Try it out"
4. Paste the JSON example
5. Click "Execute"
6. Check the response

### 2. Test with cURL

```bash
# Create a patient
curl -X POST http://localhost:8001/api/v1/patients \
  -H "Content-Type: application/json" \
  -d @test_patient.json

# Create a visit for that patient
curl -X POST http://localhost:8001/api/v1/visits \
  -H "Content-Type: application/json" \
  -d @test_visit.json

# Verify creation
curl http://localhost:8001/api/v1/patients/PAT006
curl http://localhost:8001/api/v1/visits/VIS006
```

### 3. Test with Python Script

```python
import requests
import json

# Create patient
patient_data = {
    "patient_id": "PAT999",
    "first_name": "Test",
    "last_name": "Patient",
    "date_of_birth": "1985-05-15",
    "gender": "Other",
    "phone": "(555) 999-0000",
    "email": "test@example.com"
}

response = requests.post(
    "http://localhost:8001/api/v1/patients",
    json=patient_data
)

if response.status_code == 201:
    print("Patient created successfully!")
    print(response.json())
```

## 📊 Advanced Features

### 1. Bulk Creation

You can create multiple patients/visits by calling the endpoints multiple times:

```python
patients = [patient1_data, patient2_data, patient3_data]
for patient in patients:
    response = requests.post(url, json=patient)
    if response.status_code == 201:
        print(f"Created: {patient['patient_id']}")
```

### 2. Data Validation

- **Date formats**: Use ISO format (YYYY-MM-DD for dates, YYYY-MM-DDTHH:MM:SS for datetime)
- **JSON fields**: vital_signs and lab_results should be JSON strings
- **Patient IDs**: Must be unique across the system
- **Visit IDs**: Must be unique across the system

### 3. Relationship Validation

- **Visits require existing patients**: The patient_id in a visit must reference an existing patient
- **Foreign key constraints**: Database enforces referential integrity

## 🎯 Best Practices

### 1. ID Generation

- Use consistent ID patterns (PAT001, PAT002, VIS001, VIS002)
- Consider UUIDs for production systems
- Check for existence before creating

### 2. Data Quality

- Validate dates before sending
- Sanitize input data
- Use consistent formats for phone numbers, addresses

### 3. Error Handling

- Always check response status codes
- Handle validation errors gracefully
- Implement retry logic for network issues

### 4. Testing

- Test with both valid and invalid data
- Verify created records with GET endpoints
- Test edge cases (missing fields, duplicate IDs)

## 🚀 Ready to Create!

Your Medical Assistant API now supports full CRUD operations:

- ✅ **CREATE**: Add new patients and visits
- ✅ **READ**: Retrieve patient and visit data
- ✅ **UPDATE**: Modify existing records (PUT endpoints)
- ✅ **DELETE**: Remove records (DELETE endpoints)

Start creating your medical data using the interactive documentation at:
**http://localhost:8001/docs**

---

_Last updated: 2025-09-29_  
_Server: http://localhost:8001_  
_Documentation: /docs_
