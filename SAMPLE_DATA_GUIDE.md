# 🏥 Medical Assistant API - Sample Data Guide

Your Medical Assistant API now has **realistic sample data** ready for testing! Here's everything you need to know about the sample data and how to use it.

## 📊 Sample Data Overview

### 👥 Patients (5 patients)

- **PAT001** - John Smith (Hypertension, Diabetes risk)
- **PAT002** - Sarah Johnson (Asthma, Allergies)
- **PAT003** - Robert Davis (Type 2 Diabetes, High cholesterol)
- **PAT004** - Emily Chen (Healthy young adult)
- **PAT005** - Michael Brown (Coronary artery disease, Post-MI)

### 📋 Visits (5 recent visits)

- **VIS001** - John Smith: Hypertension follow-up
- **VIS002** - Sarah Johnson: Asthma exacerbation (urgent)
- **VIS003** - Robert Davis: Diabetes management
- **VIS004** - Emily Chen: Annual physical
- **VIS005** - Michael Brown: Cardiology follow-up

## 🚀 Testing the API

### 1. Start the Development Server

```bash
cd /Users/chetan/Personal/HobbyProjects/doctors-assistant
source .venv/bin/activate
uvicorn app.main_dev:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Access API Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/api/v1/openapi.json

## 🧪 API Testing Examples

### Patient Endpoints

```bash
# Get all patients
curl http://localhost:8000/api/v1/patients

# Get specific patient
curl http://localhost:8000/api/v1/patients/PAT001

# Get patient's medical history
curl http://localhost:8000/api/v1/patients/PAT003  # Diabetes patient

# Get patient's visits
curl http://localhost:8000/api/v1/patients/PAT002/visits  # Asthma patient visits
```

### Visit Endpoints

```bash
# Get all visits
curl http://localhost:8000/api/v1/visits

# Get specific visit
curl http://localhost:8000/api/v1/visits/VIS002  # Urgent asthma visit

# Filter by visit type
curl 'http://localhost:8000/api/v1/visits?visit_type=urgent'
curl 'http://localhost:8000/api/v1/visits?visit_type=routine'
curl 'http://localhost:8000/api/v1/visits?visit_type=follow-up'
```

### System Status

```bash
# Check system health
curl http://localhost:8000/api/v1/setup-status
```

## 📋 Sample Data Details

### 🩺 Medical Scenarios Included

1. **Chronic Disease Management** (John Smith - PAT001)

   - Primary: Hypertension
   - Risk factors: Family history of diabetes
   - Medications: Lisinopril, Metformin
   - Recent visit: Blood pressure control assessment

2. **Acute Care** (Sarah Johnson - PAT002)

   - Primary: Asthma exacerbation
   - Triggers: Seasonal allergens
   - Treatment: Nebulizer, Prednisone course
   - Emergency care scenario

3. **Diabetes Care** (Robert Davis - PAT003)

   - Primary: Type 2 Diabetes (suboptimal control)
   - Secondary: High cholesterol
   - HbA1c: 8.2% (elevated)
   - Medication adjustment needed

4. **Preventive Care** (Emily Chen - PAT004)

   - Healthy young adult
   - Annual physical examination
   - Normal lab results
   - Contraception counseling

5. **Cardiology Follow-up** (Michael Brown - PAT005)
   - Post-myocardial infarction
   - Coronary artery disease
   - Cardiac rehabilitation
   - Complex medication regimen

### 📊 Data Fields Included

**Patient Records:**

- Demographics (name, DOB, gender, contact info)
- Medical history and allergies
- Current medications
- Emergency contacts
- Insurance information

**Visit Records:**

- Chief complaints and symptoms
- Vital signs (BP, HR, temperature, weight)
- Laboratory results (formatted as JSON)
- Diagnosis and treatment plans
- Medications prescribed
- Follow-up instructions
- Doctor's notes
- Visit duration

## 🤖 AI Features (Optional)

To enable AI-powered features, add your OpenAI API key:

```bash
# Add to .env file
echo "OPENAI_API_KEY=your-api-key-here" >> .env
```

Then test AI endpoints:

```bash
# Summarize a visit
curl -X POST http://localhost:8000/api/v1/ai/summarize-visit \
  -H "Content-Type: application/json" \
  -d '{"visit_id": "VIS002"}'

# Ask questions about a patient
curl -X POST http://localhost:8000/api/v1/ai/ask-about-patient \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "PAT003", "question": "What is this patient'\''s diabetes control status?"}'
```

## 🔍 Database Access

You can also query the database directly:

```bash
# Connect to PostgreSQL
psql doctors_assistant

# View patients
SELECT patient_id, first_name, last_name, medical_history FROM patients;

# View visits with patient names
SELECT v.visit_id, p.first_name, p.last_name, v.visit_type, v.chief_complaint
FROM visits v
JOIN patients p ON v.patient_id = p.id;

# Get visit details
SELECT * FROM visits WHERE visit_id = 'VIS002';
```

## 📈 Next Steps

1. **Test the API** using the interactive docs at http://localhost:8000/docs
2. **Add your OpenAI API key** to enable AI features
3. **Create additional test data** by modifying the sample data script
4. **Build your frontend** using these API endpoints
5. **Add authentication** for production use

## 🛠️ Troubleshooting

### Common Issues:

1. **Server won't start**: Make sure virtual environment is activated
2. **Database connection errors**: Verify PostgreSQL is running
3. **API key warnings**: Add OPENAI_API_KEY to .env (optional for basic features)
4. **Port conflicts**: Change port using `--port 8001`

### Useful Commands:

```bash
# Check if server is running
curl http://localhost:8000/api/v1/setup-status

# View server logs
tail -f app.log

# Restart PostgreSQL (if needed)
brew services restart postgresql

# Check database connection
psql doctors_assistant -c "SELECT COUNT(*) FROM patients;"
```

## 🎉 Success!

Your Medical Assistant API is now ready with comprehensive sample data! You can:

- ✅ Browse realistic patient records
- ✅ View detailed medical visits
- ✅ Test all CRUD operations
- ✅ Explore the interactive API documentation
- ✅ Query the database directly
- ✅ Add AI features with an API key

Happy coding! 🚀
