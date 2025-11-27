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
    """Create 5 sample visits for each patient (25 total visits)."""
    visits = []
    visit_counter = 1
    
    # PAT001 - John Smith: Hypertension management journey
    patient_id = patient_ids["PAT001"]
    
    # Visit 1: Initial diagnosis (120 days ago)
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=120),
        "visit_type": "routine",
        "chief_complaint": "Routine check-up, occasional headaches",
        "symptoms": "Mild headaches, especially in the morning",
        "diagnosis": "Essential hypertension, newly diagnosed",
        "treatment_plan": "Lifestyle modifications, start antihypertensive medication",
        "medications_prescribed": "Lisinopril 10mg daily",
        "follow_up_instructions": "Return in 1 month to check BP response",
        "doctor_notes": "BP elevated at 148/92. No end-organ damage. Started on ACE inhibitor.",
        "vital_signs": {"blood_pressure_systolic": 148, "blood_pressure_diastolic": 92, "heart_rate": 78, "temperature": 98.6, "weight": 185, "height": 70},
        "lab_results": [{"test_name": "Basic Metabolic Panel", "value": "Normal", "status": "normal"}],
        "duration_minutes": 30
    })
    visit_counter += 1
    
    # Visit 2: Medication adjustment (90 days ago)
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=90),
        "visit_type": "follow-up",
        "chief_complaint": "Blood pressure follow-up",
        "symptoms": "Headaches improved, feeling better",
        "diagnosis": "Essential hypertension, responding to treatment",
        "treatment_plan": "Continue current medication, monitor BP",
        "medications_prescribed": "Lisinopril 10mg daily (continued)",
        "follow_up_instructions": "Return in 6 weeks",
        "doctor_notes": "BP improved to 138/86. Good medication tolerance. Continue current regimen.",
        "vital_signs": {"blood_pressure_systolic": 138, "blood_pressure_diastolic": 86, "heart_rate": 74, "temperature": 98.5, "weight": 183, "height": 70},
        "duration_minutes": 15
    })
    visit_counter += 1
    
    # Visit 3: Progress check (60 days ago)
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=60),
        "visit_type": "follow-up",
        "chief_complaint": "Hypertension follow-up",
        "symptoms": "No complaints, feeling well",
        "diagnosis": "Essential hypertension, well controlled",
        "treatment_plan": "Continue medications, lifestyle modifications",
        "medications_prescribed": "Lisinopril 10mg daily (continued)",
        "follow_up_instructions": "Return in 2 months",
        "doctor_notes": "BP at goal 128/80. Patient compliant. Discussed DASH diet.",
        "vital_signs": {"blood_pressure_systolic": 128, "blood_pressure_diastolic": 80, "heart_rate": 72, "temperature": 98.6, "weight": 181, "height": 70},
        "duration_minutes": 20
    })
    visit_counter += 1
    
    # Visit 4: Routine check (30 days ago)
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=30),
        "visit_type": "routine",
        "chief_complaint": "Routine hypertension follow-up",
        "symptoms": "No acute symptoms",
        "diagnosis": "Essential hypertension, well controlled",
        "treatment_plan": "Continue current medications",
        "medications_prescribed": "Lisinopril 10mg daily (continued)",
        "follow_up_instructions": "Return in 3 months",
        "doctor_notes": "BP stable. Added metformin for prediabetes (HbA1c 6.2%).",
        "vital_signs": {"blood_pressure_systolic": 126, "blood_pressure_diastolic": 78, "heart_rate": 70, "temperature": 98.7, "weight": 180, "height": 70},
        "lab_results": [{"test_name": "HbA1c", "value": "6.2%", "unit": "%", "status": "elevated"}],
        "duration_minutes": 25
    })
    visit_counter += 1
    
    # Visit 5: Recent visit (7 days ago)
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=7),
        "visit_type": "follow-up",
        "chief_complaint": "Metformin follow-up",
        "symptoms": "Mild GI upset initially, now resolved",
        "diagnosis": "Essential hypertension, Prediabetes",
        "treatment_plan": "Continue medications, dietary counseling",
        "medications_prescribed": "Lisinopril 10mg daily, Metformin 500mg twice daily",
        "follow_up_instructions": "Return in 3 months for HbA1c recheck",
        "doctor_notes": "Tolerating metformin well. BP excellent. Weight loss of 5 lbs.",
        "vital_signs": {"blood_pressure_systolic": 124, "blood_pressure_diastolic": 76, "heart_rate": 68, "temperature": 98.6, "weight": 180, "height": 70},
        "duration_minutes": 20
    })
    visit_counter += 1
    
    # PAT002 - Sarah Johnson: Asthma management
    patient_id = patient_ids["PAT002"]
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=120),
        "visit_type": "routine",
        "chief_complaint": "Annual physical examination",
        "symptoms": "Asthma well controlled, no recent exacerbations",
        "diagnosis": "Mild persistent asthma, well controlled",
        "treatment_plan": "Continue current controller therapy",
        "medications_prescribed": "Albuterol inhaler PRN, Claritin 10mg daily",
        "follow_up_instructions": "Return in 1 year or if symptoms worsen",
        "doctor_notes": "Lung exam clear. Peak flow 380 L/min (personal best).",
        "vital_signs": {"blood_pressure_systolic": 108, "blood_pressure_diastolic": 68, "heart_rate": 68, "temperature": 98.4, "weight": 135, "height": 64},
        "duration_minutes": 25
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=90),
        "visit_type": "urgent",
        "chief_complaint": "Increased wheezing and shortness of breath",
        "symptoms": "Wheezing, chest tightness, increased albuterol use",
        "diagnosis": "Asthma exacerbation, seasonal allergies",
        "treatment_plan": "Nebulizer treatment, oral steroids, increase controller",
        "medications_prescribed": "Prednisone 40mg x 5 days, Increase albuterol use",
        "follow_up_instructions": "Return in 3-5 days",
        "doctor_notes": "Moderate exacerbation. Peak flow 280. Good response to nebulizer.",
        "vital_signs": {"blood_pressure_systolic": 112, "blood_pressure_diastolic": 72, "heart_rate": 92, "temperature": 98.3, "respiratory_rate": 24, "oxygen_saturation": 94, "weight": 135, "height": 64},
        "duration_minutes": 40
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=60),
        "visit_type": "follow-up",
        "chief_complaint": "Asthma follow-up after exacerbation",
        "symptoms": "Much improved, minimal wheezing",
        "diagnosis": "Asthma, improved after treatment",
        "treatment_plan": "Start inhaled corticosteroid controller",
        "medications_prescribed": "Fluticasone inhaler 110mcg twice daily, Albuterol PRN",
        "follow_up_instructions": "Return in 1 month",
        "doctor_notes": "Significant improvement. Peak flow back to 360. Started ICS.",
        "vital_signs": {"blood_pressure_systolic": 110, "blood_pressure_diastolic": 70, "heart_rate": 72, "temperature": 98.5, "oxygen_saturation": 98, "weight": 134, "height": 64},
        "duration_minutes": 20
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=30),
        "visit_type": "follow-up",
        "chief_complaint": "Asthma medication review",
        "symptoms": "Doing well on new controller medication",
        "diagnosis": "Mild persistent asthma, well controlled on ICS",
        "treatment_plan": "Continue current regimen",
        "medications_prescribed": "Fluticasone 110mcg BID, Albuterol PRN, Claritin daily",
        "follow_up_instructions": "Return in 3 months",
        "doctor_notes": "Excellent control. Minimal rescue inhaler use. Peak flow 375.",
        "vital_signs": {"blood_pressure_systolic": 108, "blood_pressure_diastolic": 68, "heart_rate": 70, "temperature": 98.4, "weight": 133, "height": 64},
        "duration_minutes": 15
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=7),
        "visit_type": "routine",
        "chief_complaint": "Routine asthma check",
        "symptoms": "No complaints, asthma well controlled",
        "diagnosis": "Mild persistent asthma, well controlled",
        "treatment_plan": "Continue current medications",
        "medications_prescribed": "Continue all current medications",
        "follow_up_instructions": "Return in 6 months",
        "doctor_notes": "Stable asthma. Good technique with inhalers. No exacerbations.",
        "vital_signs": {"blood_pressure_systolic": 106, "blood_pressure_diastolic": 66, "heart_rate": 68, "temperature": 98.3, "weight": 133, "height": 64},
        "duration_minutes": 15
    })
    visit_counter += 1
    
    # PAT003 - Robert Davis: Diabetes journey
    patient_id = patient_ids["PAT003"]
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=120),
        "visit_type": "routine",
        "chief_complaint": "Fatigue, increased thirst and urination",
        "symptoms": "Polyuria, polydipsia, fatigue for 2 months",
        "diagnosis": "Type 2 Diabetes Mellitus, newly diagnosed",
        "treatment_plan": "Start metformin, diabetes education, lifestyle modifications",
        "medications_prescribed": "Metformin 500mg twice daily",
        "follow_up_instructions": "Return in 2 weeks, diabetes education class",
        "doctor_notes": "Fasting glucose 245 mg/dL, HbA1c 9.2%. Started on metformin.",
        "vital_signs": {"blood_pressure_systolic": 142, "blood_pressure_diastolic": 88, "heart_rate": 80, "temperature": 98.7, "weight": 220, "height": 72},
        "lab_results": [
            {"test_name": "Fasting Glucose", "value": "245", "unit": "mg/dL", "status": "elevated"},
            {"test_name": "HbA1c", "value": "9.2%", "unit": "%", "status": "elevated"}
        ],
        "duration_minutes": 45
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=90),
        "visit_type": "follow-up",
        "chief_complaint": "Diabetes follow-up",
        "symptoms": "Tolerating metformin, some GI upset",
        "diagnosis": "Type 2 Diabetes, adjusting to treatment",
        "treatment_plan": "Increase metformin dose, continue lifestyle changes",
        "medications_prescribed": "Metformin 1000mg twice daily",
        "follow_up_instructions": "Return in 6 weeks for glucose check",
        "doctor_notes": "Fasting glucose improved to 180. Increase metformin dose.",
        "vital_signs": {"blood_pressure_systolic": 138, "blood_pressure_diastolic": 86, "heart_rate": 78, "temperature": 98.6, "weight": 215, "height": 72},
        "lab_results": [{"test_name": "Fasting Glucose", "value": "180", "unit": "mg/dL", "status": "elevated"}],
        "duration_minutes": 20
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=60),
        "visit_type": "follow-up",
        "chief_complaint": "Diabetes management, dietary counseling",
        "symptoms": "Feeling better, more energy",
        "diagnosis": "Type 2 Diabetes, improving control",
        "treatment_plan": "Continue medications, nutrition consultation",
        "medications_prescribed": "Metformin 1000mg BID, Atorvastatin 20mg daily",
        "follow_up_instructions": "Return in 6 weeks",
        "doctor_notes": "Weight loss of 5 lbs. Glucose improving. Added statin for cholesterol.",
        "vital_signs": {"blood_pressure_systolic": 135, "blood_pressure_diastolic": 84, "heart_rate": 76, "temperature": 98.7, "weight": 215, "height": 72},
        "duration_minutes": 30
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=30),
        "visit_type": "routine",
        "chief_complaint": "Diabetes check-up",
        "symptoms": "Generally feeling well",
        "diagnosis": "Type 2 Diabetes, moderate control",
        "treatment_plan": "Continue current regimen, increase exercise",
        "medications_prescribed": "Continue all medications",
        "follow_up_instructions": "Return in 3 months for HbA1c",
        "doctor_notes": "HbA1c improved to 7.8%. Continue current plan. Encourage exercise.",
        "vital_signs": {"blood_pressure_systolic": 132, "blood_pressure_diastolic": 82, "heart_rate": 74, "temperature": 98.6, "weight": 212, "height": 72},
        "lab_results": [{"test_name": "HbA1c", "value": "7.8%", "unit": "%", "status": "elevated"}],
        "duration_minutes": 25
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=7),
        "visit_type": "follow-up",
        "chief_complaint": "Diabetes management review",
        "symptoms": "Increased fatigue, occasional thirst",
        "diagnosis": "Type 2 Diabetes, suboptimal control",
        "treatment_plan": "Consider adding second agent, intensify lifestyle",
        "medications_prescribed": "Continue current medications",
        "follow_up_instructions": "Return in 2 weeks to discuss treatment adjustment",
        "doctor_notes": "HbA1c 8.2%, glucose control slipping. Discuss adding GLP-1 agonist.",
        "vital_signs": {"blood_pressure_systolic": 135, "blood_pressure_diastolic": 85, "heart_rate": 76, "temperature": 98.7, "weight": 210, "height": 72},
        "lab_results": [
            {"test_name": "HbA1c", "value": "8.2%", "unit": "%", "status": "elevated"},
            {"test_name": "Fasting Glucose", "value": "165", "unit": "mg/dL", "status": "elevated"}
        ],
        "duration_minutes": 30
    })
    visit_counter += 1
    
    # PAT004 - Emily Chen: Healthy patient
    patient_id = patient_ids["PAT004"]
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=120),
        "visit_type": "routine",
        "chief_complaint": "New patient visit, establishing care",
        "symptoms": "No acute complaints",
        "diagnosis": "Healthy young adult",
        "treatment_plan": "Preventive care, update vaccinations",
        "medications_prescribed": "Continue birth control pill",
        "follow_up_instructions": "Return in 1 year for annual physical",
        "doctor_notes": "Comprehensive exam normal. Updated Tdap. Discussed contraception.",
        "vital_signs": {"blood_pressure_systolic": 110, "blood_pressure_diastolic": 70, "heart_rate": 68, "temperature": 98.3, "weight": 128, "height": 65},
        "lab_results": [{"test_name": "Complete Blood Count", "value": "Normal", "status": "normal"}],
        "duration_minutes": 30
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=90),
        "visit_type": "consultation",
        "chief_complaint": "Contraception consultation",
        "symptoms": "Interested in long-acting contraception",
        "diagnosis": "Contraception counseling",
        "treatment_plan": "Discussed IUD options, patient to consider",
        "medications_prescribed": "Continue current birth control pill",
        "follow_up_instructions": "Call to schedule IUD insertion if desired",
        "doctor_notes": "Discussed Mirena vs Paragard. Patient wants to think about it.",
        "vital_signs": {"blood_pressure_systolic": 108, "blood_pressure_diastolic": 68, "heart_rate": 66, "temperature": 98.4, "weight": 127, "height": 65},
        "duration_minutes": 20
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=60),
        "visit_type": "urgent",
        "chief_complaint": "Sore throat, congestion, cough",
        "symptoms": "Sore throat x 3 days, nasal congestion, dry cough",
        "diagnosis": "Upper respiratory infection, viral",
        "treatment_plan": "Symptomatic treatment, rest, fluids",
        "medications_prescribed": "Acetaminophen PRN, Dextromethorphan for cough",
        "follow_up_instructions": "Return if symptoms worsen or fever develops",
        "doctor_notes": "Viral URI. Throat mildly erythematous. Lungs clear. Rapid strep negative.",
        "vital_signs": {"blood_pressure_systolic": 112, "blood_pressure_diastolic": 72, "heart_rate": 75, "temperature": 99.1, "weight": 126, "height": 65},
        "duration_minutes": 15
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=30),
        "visit_type": "routine",
        "chief_complaint": "Vaccination update",
        "symptoms": "No complaints, here for flu shot",
        "diagnosis": "Healthy, preventive care",
        "treatment_plan": "Administer influenza vaccine",
        "medications_prescribed": "Influenza vaccine administered",
        "follow_up_instructions": "Return in 1 year",
        "doctor_notes": "Flu vaccine given. No adverse reactions. Feeling well.",
        "vital_signs": {"blood_pressure_systolic": 108, "blood_pressure_diastolic": 68, "heart_rate": 67, "temperature": 98.3, "weight": 125, "height": 65},
        "duration_minutes": 10
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=7),
        "visit_type": "routine",
        "chief_complaint": "Annual physical examination",
        "symptoms": "No acute complaints, feeling well",
        "diagnosis": "Healthy young adult, up to date with preventive care",
        "treatment_plan": "Continue current health maintenance",
        "medications_prescribed": "Continue birth control pill, Multivitamin daily",
        "follow_up_instructions": "Return in 1 year for annual physical",
        "doctor_notes": "Excellent health. Normal physical exam. All preventive care current.",
        "vital_signs": {"blood_pressure_systolic": 106, "blood_pressure_diastolic": 66, "heart_rate": 65, "temperature": 98.3, "weight": 125, "height": 65},
        "lab_results": [
            {"test_name": "Complete Blood Count", "value": "Normal", "status": "normal"},
            {"test_name": "Lipid Panel", "value": "Normal", "status": "normal"}
        ],
        "duration_minutes": 25
    })
    visit_counter += 1
    
    # PAT005 - Michael Brown: Cardiac patient
    patient_id = patient_ids["PAT005"]
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=120),
        "visit_type": "follow-up",
        "chief_complaint": "Post-MI follow-up, 6 months after heart attack",
        "symptoms": "Occasional chest discomfort with heavy exertion",
        "diagnosis": "Coronary artery disease, post-MI, stable",
        "treatment_plan": "Continue dual antiplatelet therapy, cardiac rehab",
        "medications_prescribed": "Aspirin 81mg, Clopidogrel 75mg, Metoprolol 50mg BID, Atorvastatin 80mg",
        "follow_up_instructions": "Return in 6 weeks, continue cardiac rehab",
        "doctor_notes": "6 months post-MI. Doing well in cardiac rehab. EKG stable.",
        "vital_signs": {"blood_pressure_systolic": 128, "blood_pressure_diastolic": 78, "heart_rate": 68, "temperature": 98.5, "weight": 205, "height": 71},
        "lab_results": [
            {"test_name": "Troponin", "value": "<0.01", "unit": "ng/mL", "status": "normal"},
            {"test_name": "LDL Cholesterol", "value": "95", "unit": "mg/dL", "status": "target"}
        ],
        "duration_minutes": 35
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=90),
        "visit_type": "follow-up",
        "chief_complaint": "Cardiac rehab progress check",
        "symptoms": "Exercise tolerance improving, no chest pain",
        "diagnosis": "CAD, post-MI, improving functional capacity",
        "treatment_plan": "Continue cardiac rehab, optimize medications",
        "medications_prescribed": "Continue all cardiac medications",
        "follow_up_instructions": "Return in 2 months",
        "doctor_notes": "Excellent progress in rehab. Can walk 30 min without symptoms.",
        "vital_signs": {"blood_pressure_systolic": 124, "blood_pressure_diastolic": 76, "heart_rate": 64, "temperature": 98.4, "weight": 200, "height": 71},
        "duration_minutes": 25
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=60),
        "visit_type": "follow-up",
        "chief_complaint": "Medication adjustment visit",
        "symptoms": "Mild fatigue, possibly from beta blocker",
        "diagnosis": "CAD, post-MI, medication side effects",
        "treatment_plan": "Reduce metoprolol dose, monitor symptoms",
        "medications_prescribed": "Metoprolol reduced to 25mg BID, continue others",
        "follow_up_instructions": "Return in 4 weeks",
        "doctor_notes": "Reduced beta blocker for fatigue. BP and HR still well controlled.",
        "vital_signs": {"blood_pressure_systolic": 122, "blood_pressure_diastolic": 74, "heart_rate": 62, "temperature": 98.5, "weight": 198, "height": 71},
        "duration_minutes": 20
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=30),
        "visit_type": "consultation",
        "chief_complaint": "Stress test evaluation",
        "symptoms": "No chest pain, good exercise tolerance",
        "diagnosis": "CAD, post-MI, negative stress test",
        "treatment_plan": "Continue current medications and exercise program",
        "medications_prescribed": "Continue all medications",
        "follow_up_instructions": "Return in 3 months",
        "doctor_notes": "Stress test negative for ischemia. Excellent functional capacity.",
        "vital_signs": {"blood_pressure_systolic": 120, "blood_pressure_diastolic": 74, "heart_rate": 60, "temperature": 98.5, "weight": 196, "height": 71},
        "lab_results": [{"test_name": "Stress Test", "value": "Negative for ischemia", "status": "normal"}],
        "duration_minutes": 30
    })
    visit_counter += 1
    
    visits.append({
        "visit_id": f"VIS{visit_counter:03d}",
        "patient_id": patient_id,
        "visit_date": datetime.now() - timedelta(days=7),
        "visit_type": "follow-up",
        "chief_complaint": "Routine cardiology follow-up",
        "symptoms": "Mild chest discomfort with exertion, improved exercise tolerance",
        "diagnosis": "Coronary artery disease, stable angina, post-MI",
        "treatment_plan": "Continue dual antiplatelet therapy, cardiac rehabilitation",
        "medications_prescribed": "Continue current cardiac medications",
        "follow_up_instructions": "Return in 3 months, continue cardiac rehab",
        "doctor_notes": "Stable CAD. Good progress in cardiac rehab. EKG shows old inferior MI, no acute changes.",
        "vital_signs": {"blood_pressure_systolic": 120, "blood_pressure_diastolic": 75, "heart_rate": 62, "temperature": 98.5, "weight": 195, "height": 71},
        "lab_results": [
            {"test_name": "Troponin", "value": "<0.01", "unit": "ng/mL", "status": "normal"},
            {"test_name": "BNP", "value": "45", "unit": "pg/mL", "status": "normal"},
            {"test_name": "Lipid Panel", "value": "LDL 85 mg/dL", "status": "target"}
        ],
        "duration_minutes": 40
    })
    
    return visits



async def create_sample_data():
    """Create sample patients and visits in the database."""
    try:
        # Create database engine and session (MySQL + PostgreSQL support)
        database_url = settings.DATABASE_URL
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        elif database_url.startswith("mysql://"):
            database_url = database_url.replace("mysql://", "mysql+aiomysql://")
        
        engine = create_async_engine(database_url)
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
        # Create database engine (MySQL + PostgreSQL support)
        database_url = settings.DATABASE_URL
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        elif database_url.startswith("mysql://"):
            database_url = database_url.replace("mysql://", "mysql+aiomysql://")
        
        engine = create_async_engine(database_url)
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
