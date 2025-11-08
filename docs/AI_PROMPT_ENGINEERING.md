# AI Prompt Engineering Guide

A comprehensive guide to understanding how AI prompts work in the Medical Assistant project.

---

## Table of Contents

1. [What is Prompt Engineering?](#what-is-prompt-engineering)
2. [System Prompts - Setting AI Behavior](#system-prompts---setting-ai-behavior)
3. [Context Building - Providing Patient Data](#context-building---providing-patient-data)
4. [Example Prompt Flow](#example-prompt-flow)
5. [Advanced Prompt Techniques](#advanced-prompt-techniques)
6. [Best Practices](#best-practices-for-medical-ai-prompts)

---

## What is Prompt Engineering?

**Prompt Engineering** is the art and science of crafting effective instructions for AI models to get the desired outputs. In our medical assistant, we use prompts to:

- Define the AI's role and capabilities
- Provide patient data context
- Guide response format and structure
- Ensure HIPAA compliance
- Maintain medical accuracy

Think of it like giving instructions to a highly skilled medical assistant - the clearer and more structured your instructions, the better the results.

---

## System Prompts - Setting AI Behavior

### What is a System Prompt?

A **system prompt** is like the AI's "job description" that:

- Defines the AI's role and responsibilities
- Sets behavioral guidelines
- Establishes output format expectations
- Stays consistent across all user interactions
- Is set once when initializing the agent

### Your Medical QA Agent System Prompt

**Location:** `app/agents/qa_agent.py`

```python
MEDICAL_QA_SYSTEM_PROMPT = """
You are a medical assistant AI helping healthcare professionals
analyze patient data and answer clinical questions.

Your capabilities:
1. Answer questions about patient medical history
2. Summarize visit information
3. Compare data across multiple visits
4. Provide clinical insights based on available data

Guidelines:
- Be accurate and evidence-based
- Use medical terminology appropriately
- Cite specific data points from patient records
- Acknowledge limitations when data is insufficient
- Never make diagnoses - only provide information analysis
- Maintain HIPAA compliance in all responses

Response Format:
- Start with a direct answer to the question
- Support with specific data from patient records
- Include relevant vital signs or lab results in Markdown tables
- End with data sources used

When you see formatted tables in the context, preserve them in your response.
"""
```

### Why This Prompt Design Works

Let's break down each component:

#### 1. Clear Role Definition

```python
"You are a medical assistant AI helping healthcare professionals..."
```

**Purpose:** Sets expectations about capabilities and limitations
**Why it matters:** Prevents AI from overstepping boundaries (e.g., making diagnoses)

#### 2. Explicit Capabilities List

```python
Your capabilities:
1. Answer questions about patient medical history
2. Summarize visit information
3. Compare data across multiple visits
4. Provide clinical insights based on available data
```

**Purpose:** Defines what the AI can and should do
**Why it matters:** Helps AI focus on tasks it's designed for

#### 3. Safety Guidelines

```python
- Never make diagnoses - only provide information analysis
- Maintain HIPAA compliance in all responses
```

**Purpose:** Prevents liability issues and ensures compliance
**Why it matters:** Critical for medical applications

#### 4. Format Instructions

```python
Response Format:
- Start with a direct answer to the question
- Support with specific data from patient records
- Include relevant vital signs or lab results in Markdown tables
```

**Purpose:** Ensures consistent, readable outputs
**Why it matters:** Doctors need quick, scannable information

#### 5. Data Citation Requirement

```python
- Cite specific data points from patient records
- End with data sources used
```

**Purpose:** Makes responses traceable and verifiable
**Why it matters:** Medical decisions require source verification

### System Prompt Implementation

**How it's used in code:**

```python
class MedicalQAAgent:
    """Agent for answering questions about patient data."""

    def __init__(self):
        """Initialize the medical QA agent."""
        system_prompt = """
        You are a medical assistant AI helping healthcare professionals...
        [Full system prompt here]
        """

        # Create agent with fallback system
        self.agent = FallbackAgent(system_prompt)
        logger.info("Medical QA Agent initialized with fallback system")
```

---

## Context Building - Providing Patient Data

### The Context is Everything

The AI needs rich, structured context to answer questions effectively. Here's how we build it:

```python
async def answer_question(
    self,
    question: str,
    patient_id: Optional[str] = None,
    visit_id: Optional[str] = None,
    patients: Optional[List[PatientResponse]] = None,
    visits: Optional[List[VisitResponse]] = None
) -> str:
    """Build rich context for the AI."""

    context_parts = []

    # Step 1: Add Patient Demographics
    if patients:
        context_parts.append("## Patient Information\n")
        for patient in patients:
            age = calculate_age(patient.date_of_birth)
            context_parts.append(f"**Patient ID:** {patient.patient_id}")
            context_parts.append(f"**Name:** {patient.first_name} {patient.last_name}")
            context_parts.append(f"**Age:** {age} years old")
            context_parts.append(f"**Gender:** {patient.gender}")

            if patient.medical_history:
                context_parts.append(f"**Medical History:** {patient.medical_history}")

            if patient.allergies:
                context_parts.append(f"**Allergies:** {patient.allergies}")

            if patient.current_medications:
                context_parts.append(f"**Current Medications:** {patient.current_medications}")

            context_parts.append("\n")

    # Step 2: Add Visit Information with Formatted Tables
    if visits:
        context_parts.append("## Recent Medical Visits\n")

        for idx, visit in enumerate(visits[:5], 1):  # Last 5 visits
            context_parts.append(f"### Visit {idx}: {visit.visit_id}")
            context_parts.append(f"**Date:** {visit.visit_date.strftime('%Y-%m-%d %H:%M')}")
            context_parts.append(f"**Type:** {visit.visit_type}")
            context_parts.append(f"**Chief Complaint:** {visit.chief_complaint or 'Not recorded'}")
            context_parts.append(f"**Diagnosis:** {visit.diagnosis or 'Not recorded'}")

            # Add formatted vital signs table
            if visit.vital_signs:
                from app.services.formatting_service import medical_formatter
                vital_signs_table = medical_formatter.format_vital_signs_markdown(
                    json.dumps(visit.vital_signs)
                )
                context_parts.append(vital_signs_table)

            # Add formatted lab results table
            if visit.lab_results:
                from app.services.formatting_service import medical_formatter
                lab_results_table = medical_formatter.format_lab_results_markdown(
                    json.dumps(visit.lab_results)
                )
                context_parts.append(lab_results_table)

            # Add treatment information
            if visit.treatment_plan:
                context_parts.append(f"\n**Treatment Plan:**\n{visit.treatment_plan}")

            if visit.medications_prescribed:
                context_parts.append(f"\n**Medications:**\n{visit.medications_prescribed}")

            if visit.doctor_notes:
                context_parts.append(f"\n**Doctor's Notes:**\n{visit.doctor_notes}")

            context_parts.append("\n---\n")

    # Step 3: Combine Everything
    context = "\n".join(context_parts)

    # Step 4: Create the Full Prompt
    user_prompt = f"""
{context}

## Question
{question}

## Instructions
Based on the patient data above:
1. Answer the question directly and concisely
2. Reference specific data points from the visits
3. If showing vital signs or lab results, preserve the table format
4. Cite which visit(s) you're referencing
5. If data is insufficient, state that clearly

Provide your answer now:
"""

    # Step 5: Send to AI
    response = await self.agent.run_async(user_prompt)

    return response
```

### Why This Context Structure Works

#### 1. Hierarchical Organization

```markdown
## Patient Information

### Visit 1: VIS003

**Vital Signs:**
```

**Benefit:** AI can quickly scan and locate relevant information
**Impact:** Faster, more accurate responses

#### 2. Chronological Order

```python
for idx, visit in enumerate(visits[:5], 1):  # Most recent first
```

**Benefit:** Recent visits are most relevant for clinical questions
**Impact:** AI prioritizes current patient state

#### 3. Pre-formatted Tables

```python
vital_signs_table = medical_formatter.format_vital_signs_markdown(
    json.dumps(visit.vital_signs)
)
context_parts.append(vital_signs_table)
```

**Benefit:** AI doesn't need to create tables, just include them
**Impact:** Consistent formatting, fewer errors

#### 4. Complete Information Package

- Demographics (who)
- Medical history (background)
- Visits (what happened)
- Vital signs (measurements)
- Lab results (tests)
- Treatments (interventions)

**Benefit:** AI has full picture for informed responses
**Impact:** More accurate, comprehensive answers

#### 5. Clear Instructions

```python
## Instructions
Based on the patient data above:
1. Answer the question directly and concisely
2. Reference specific data points from the visits
...
```

**Benefit:** Tells AI exactly how to use the context
**Impact:** Consistent response format

---

## Example Prompt Flow

Let's trace a real question through the entire system.

### User Question

```
"What was the patient's blood pressure trend over the last 3 visits?"
```

### Step 1: Fetch Patient Data

```python
# Endpoint receives request
request_data = {
    "question": "What was the patient's blood pressure trend over the last 3 visits?",
    "patient_id": "PAT001",
    "context_type": "recent"
}

# Service fetches patient
patient = await patient_service.get_patient_by_id("PAT001")

# Service fetches recent visits
visits = await visit_service.get_patient_visits("PAT001", limit=3)
```

### Step 2: Build Context

The AI receives this formatted context:

```markdown
## Patient Information

**Patient ID:** PAT001
**Name:** John Doe
**Age:** 40 years old
**Gender:** Male
**Medical History:** Type 2 Diabetes, Hypertension
**Allergies:** Penicillin
**Current Medications:** Metformin 500mg BID, Lisinopril 10mg daily

## Recent Medical Visits

### Visit 1: VIS003

**Date:** 2025-10-27 14:30
**Type:** Follow-up
**Chief Complaint:** Routine diabetes check-up
**Diagnosis:** Type 2 Diabetes Mellitus - Good control, Essential Hypertension - Improved

**Vital Signs:**

| Measurement    | Value  | Unit | Status      |
| -------------- | ------ | ---- | ----------- |
| Blood Pressure | 128/82 | mmHg | ⚠️ Elevated |
| Heart Rate     | 75     | bpm  | ✅ Normal   |
| Temperature    | 98.4   | °F   | ✅ Normal   |

**Treatment Plan:**
Continue current medications. Patient showing good response to treatment.

**Medications:**
Metformin 500mg BID, Lisinopril 10mg daily

---

### Visit 2: VIS002

**Date:** 2025-09-15 10:15
**Type:** Follow-up
**Chief Complaint:** Medication adjustment follow-up
**Diagnosis:** Type 2 Diabetes - Stable, Hypertension - Stage 1

**Vital Signs:**

| Measurement    | Value  | Unit | Status          |
| -------------- | ------ | ---- | --------------- |
| Blood Pressure | 135/88 | mmHg | 🔶 High Stage 1 |
| Heart Rate     | 78     | bpm  | ✅ Normal       |
| Temperature    | 98.6   | °F   | ✅ Normal       |

**Treatment Plan:**
Increased Lisinopril to 10mg daily. Continue monitoring blood pressure at home.

---

### Visit 3: VIS001

**Date:** 2025-08-10 09:00
**Type:** Initial Consultation
**Chief Complaint:** Elevated blood pressure readings at home
**Diagnosis:** Essential Hypertension - Stage 2, Type 2 Diabetes Mellitus

**Vital Signs:**

| Measurement    | Value  | Unit | Status          |
| -------------- | ------ | ---- | --------------- |
| Blood Pressure | 142/92 | mmHg | 🔴 High Stage 2 |
| Heart Rate     | 82     | bpm  | ✅ Normal       |
| Temperature    | 98.2   | °F   | ✅ Normal       |

**Treatment Plan:**
Started Lisinopril 5mg daily. Ordered follow-up in 5 weeks.

---

## Question

What was the patient's blood pressure trend over the last 3 visits?

## Instructions

Based on the patient data above:

1. Answer the question directly and concisely
2. Reference specific data points from the visits
3. If showing vital signs or lab results, preserve the table format
4. Cite which visit(s) you're referencing
5. If data is insufficient, state that clearly

Provide your answer now:
```

### Step 3: AI Processing

The AI (Grok-3/GPT-4/Claude) processes this and generates:

### Step 4: AI Response

```markdown
**Answer:**

The patient's blood pressure has shown **consistent improvement** over the last 3 visits, indicating positive response to treatment.

**Blood Pressure Trend:**

| Visit Date | Visit ID | Blood Pressure | Status          | Change from Previous |
| ---------- | -------- | -------------- | --------------- | -------------------- |
| 2025-08-10 | VIS001   | 142/92 mmHg    | 🔴 High Stage 2 | Baseline             |
| 2025-09-15 | VIS002   | 135/88 mmHg    | 🔶 High Stage 1 | ↓ 7/4 mmHg           |
| 2025-10-27 | VIS003   | 128/82 mmHg    | ⚠️ Elevated     | ↓ 7/6 mmHg           |

**Clinical Analysis:**

1. **Initial Assessment (VIS001 - Aug 10):**

   - BP: 142/92 mmHg - Stage 2 Hypertension
   - Started on Lisinopril 5mg daily

2. **5-Week Follow-up (VIS002 - Sep 15):**

   - BP: 135/88 mmHg - Improved to Stage 1
   - Reduction: 7 mmHg systolic / 4 mmHg diastolic
   - Medication increased to Lisinopril 10mg daily

3. **6-Week Follow-up (VIS003 - Oct 27):**
   - BP: 128/82 mmHg - Near normal range
   - Additional reduction: 7 mmHg systolic / 6 mmHg diastolic
   - Continuing current medication dosage

**Overall Improvement:** 14 mmHg systolic / 10 mmHg diastolic reduction over 2.5 months

**Key Observations:**

- Patient is responding well to Lisinopril
- Blood pressure trending toward target range (<120/80 mmHg)
- Consistent improvement suggests good medication adherence
- Current status: Elevated (not yet optimal, but significantly improved)

**Recommendation:** Continue monitoring. Patient is on track to reach target BP with current treatment plan.

**Sources:** Visit data from VIS001 (2025-08-10), VIS002 (2025-09-15), VIS003 (2025-10-27)

**Confidence:** High (0.95) - Based on complete vital signs data from 3 consecutive visits
```

### Step 5: Frontend Display

The frontend receives this Markdown and ReactMarkdown renders it as:

- Beautifully formatted tables
- Emoji status indicators
- Clear headings and sections
- Professional medical report format

---

## Advanced Prompt Techniques

### 1. Few-Shot Learning

**Concept:** Show the AI examples of good responses

```python
system_prompt = """
You are a medical assistant. Here are examples of how to respond:

Example 1:
Question: "What was the diagnosis?"
Good Response:
"The patient was diagnosed with Type 2 Diabetes Mellitus based on the HbA1c
level of 7.8% (reference range: 4.0-5.6%) from visit VIS001 on 2025-10-27.
This indicates poor glycemic control."

Bad Response:
"The patient has diabetes."

Example 2:
Question: "Show me the vital signs"
Good Response:
**Vital Signs from Visit VIS001 (2025-10-27):**
| Measurement | Value | Status |
|-------------|-------|--------|
| Blood Pressure | 118/75 mmHg | ✅ Normal |
| Heart Rate | 82 bpm | ✅ Normal |

Source: VIS001

Bad Response:
"BP is 118/75 and heart rate is 82."

Now answer questions following the good response format.
"""
```

**When to use:**

- Training AI on specific response styles
- Ensuring consistent output format
- Complex medical terminology usage

### 2. Chain of Thought Prompting

**Concept:** Ask AI to think step-by-step before answering

```python
user_prompt = f"""
Context:
{patient_context}

Question: {question}

Before answering, think through this step by step:

Step 1: What data from the patient records is relevant to this question?
Step 2: What patterns or trends do you observe in this data?
Step 3: What is the clinical significance of these patterns?
Step 4: What should the healthcare provider know?

Now provide your final answer based on your analysis:
"""
```

**Benefits:**

- More thorough analysis
- Better reasoning
- Catches edge cases
- Explains the logic

**Example Output:**

```markdown
**Step 1: Relevant Data**

- Blood pressure readings from 3 visits
- Medication changes (Lisinopril 5mg → 10mg)
- Timespan: 2.5 months

**Step 2: Observed Patterns**

- Consistent downward trend in both systolic and diastolic pressure
- Regular improvement intervals (5-6 weeks)

**Step 3: Clinical Significance**

- Positive medication response
- Good patient compliance indicated
- On track to reach target BP

**Step 4: Provider Should Know**

- Treatment is effective - continue current plan
- Consider target BP achievement timeline
- Patient education has been successful

**Final Answer:**
[Detailed response here]
```

### 3. Temperature Control

**Concept:** Adjust AI creativity vs accuracy

```python
# For factual medical data (low temperature = deterministic)
factual_agent = Agent(
    model='openai:gpt-4',
    temperature=0.1,  # Very factual, less creative
    system_prompt=medical_system_prompt
)

# Use for: lab results, vital signs, diagnoses
response = await factual_agent.run("What was the patient's HbA1c?")
# Expected: "The patient's HbA1c was 7.8% (measured on 2025-10-27)"

# For explanations (higher temperature = more varied)
explanation_agent = Agent(
    model='openai:gpt-4',
    temperature=0.7,  # More creative, educational
    system_prompt=educational_system_prompt
)

# Use for: patient education, general medical info
response = await explanation_agent.run("Explain what HbA1c means")
# Expected: Detailed, easy-to-understand explanation with analogies
```

**Temperature Guide:**

- **0.0-0.3:** Factual data retrieval, measurements, dates
- **0.4-0.6:** Clinical analysis, recommendations
- **0.7-0.9:** Patient education, general explanations
- **1.0+:** Not recommended for medical applications

### 4. Structured Output with Pydantic

**Concept:** Force AI to return data in specific format

```python
from pydantic import BaseModel

class MedicalSummary(BaseModel):
    """Structured medical summary."""
    patient_name: str
    diagnosis: str
    key_findings: List[str]
    recommendations: List[str]
    follow_up_required: bool
    confidence_score: float

# Create agent that returns structured data
agent = Agent(
    model='openai:gpt-4',
    result_type=MedicalSummary,  # ← Forces structure
    system_prompt=system_prompt
)

# Get structured response
result = await agent.run(user_prompt)

# result.data is guaranteed to match MedicalSummary structure
print(result.data.patient_name)  # "John Doe"
print(result.data.diagnosis)  # "Type 2 Diabetes Mellitus"
print(result.data.key_findings)  # ["HbA1c: 7.8%", "BP: 128/82"]
```

**Benefits:**

- Type-safe responses
- Validation included
- Easy to process programmatically
- No parsing errors

### 5. Role Prompting

**Concept:** Give AI a specific professional role

```python
# Specialist roles for different tasks

CARDIOLOGIST_PROMPT = """
You are a board-certified cardiologist reviewing patient cardiovascular data.
Focus on: blood pressure, heart rate, EKG findings, cardiac medications.
Provide cardiologist-level insights and recommendations.
"""

ENDOCRINOLOGIST_PROMPT = """
You are an endocrinologist specializing in diabetes management.
Focus on: glucose levels, HbA1c, insulin regimens, diabetic complications.
Provide endocrinology-focused analysis.
"""

# Use appropriate specialist for each question
if "blood pressure" in question.lower() or "heart" in question.lower():
    agent = Agent(model='openai:gpt-4', system_prompt=CARDIOLOGIST_PROMPT)
elif "diabetes" in question.lower() or "glucose" in question.lower():
    agent = Agent(model='openai:gpt-4', system_prompt=ENDOCRINOLOGIST_PROMPT)
```

### 6. Prompt Chaining

**Concept:** Break complex tasks into steps

```python
async def comprehensive_patient_analysis(patient_id: str):
    """Multi-step analysis using prompt chaining."""

    # Step 1: Summarize patient history
    history_prompt = f"Summarize the medical history for patient {patient_id}"
    history = await agent.run(history_prompt)

    # Step 2: Analyze recent trends (uses Step 1 output)
    trend_prompt = f"""
    Based on this patient history:
    {history}

    Analyze trends in the last 3 months.
    """
    trends = await agent.run(trend_prompt)

    # Step 3: Generate recommendations (uses Step 1 & 2 outputs)
    recommendation_prompt = f"""
    Patient History:
    {history}

    Recent Trends:
    {trends}

    Provide clinical recommendations.
    """
    recommendations = await agent.run(recommendation_prompt)

    return {
        "history": history,
        "trends": trends,
        "recommendations": recommendations
    }
```

---

## Best Practices for Medical AI Prompts

### DO ✅

#### 1. Be Explicit About Capabilities and Limitations

```python
system_prompt = """
You CAN:
- Summarize patient visit data
- Identify trends in vital signs
- Suggest areas requiring follow-up

You CANNOT:
- Make diagnoses
- Prescribe medications
- Replace physician judgment
- Make treatment decisions
"""
```

#### 2. Require Data Citations

```python
instructions = """
For every statement, cite the source:
- Visit ID and date
- Specific measurement
- Reference ranges used

Example: "BP was 128/82 mmHg (VIS003, 2025-10-27)"
"""
```

#### 3. Provide Structured Context

```python
# Good: Hierarchical, clear sections
context = """
## Patient Demographics
**Name:** John Doe
**Age:** 40

## Medical History
- Type 2 Diabetes (2020)
- Hypertension (2025)

## Recent Visits
### Visit 1: VIS003
...
"""

# Bad: Unstructured dump
context = "Patient John Doe age 40 has diabetes and hypertension..."
```

#### 4. Include Examples of Good Responses

```python
system_prompt = """
Example of a good response:

**Answer:** The patient's HbA1c was 7.8% (measured on 2025-10-27, VIS003).

**Analysis:** This is above the target range of <7.0% for most diabetic patients,
indicating suboptimal glycemic control.

**Sources:** Lab results from VIS003 (2025-10-27)
"""
```

#### 5. Set Appropriate Temperature

```python
# Factual queries: Low temperature
agent = Agent(temperature=0.1)  # For: lab results, vital signs

# Explanations: Medium temperature
agent = Agent(temperature=0.5)  # For: analysis, trends

# Education: Higher temperature
agent = Agent(temperature=0.7)  # For: patient education
```

#### 6. Validate AI Responses Programmatically

```python
async def validate_medical_response(response: str) -> bool:
    """Validate AI response meets quality standards."""
    checks = {
        "has_sources": "VIS" in response or "Visit" in response,
        "has_data": any(term in response for term in ["mmHg", "mg/dL", "%"]),
        "appropriate_length": 50 < len(response) < 2000,
        "no_diagnosis": not any(term in response.lower()
                               for term in ["i diagnose", "diagnosis is"]),
    }

    return all(checks.values())
```

### DON'T ❌

#### 1. Don't Allow AI to Make Diagnoses

```python
# ❌ BAD
system_prompt = "You are a doctor. Diagnose patients based on their symptoms."

# ✅ GOOD
system_prompt = "You are a medical assistant. Summarize patient data for physicians."
```

#### 2. Don't Let AI Prescribe Medications

```python
# ❌ BAD
"Recommend medications for this patient's condition."

# ✅ GOOD
"List the current medications prescribed by the physician."
```

#### 3. Don't Skip Data Validation

```python
# ❌ BAD
response = await agent.run(user_prompt)
return response  # Return whatever AI says

# ✅ GOOD
response = await agent.run(user_prompt)
if await validate_medical_response(response):
    return response
else:
    return "Unable to generate valid response. Please try again."
```

#### 4. Don't Use Vague Instructions

```python
# ❌ BAD
"Tell me about the patient."

# ✅ GOOD
"""
Provide a structured summary including:
1. Patient demographics
2. Current medical conditions
3. Recent visit history (last 3 visits)
4. Active medications
Cite all data sources.
"""
```

#### 5. Don't Mix Multiple Questions

```python
# ❌ BAD
"What's the patient's BP and also explain diabetes and show me lab results?"

# ✅ GOOD - Split into separate queries
question1 = "What was the patient's blood pressure in the last visit?"
question2 = "Show me the patient's recent lab results."
```

#### 6. Don't Forget HIPAA Compliance

```python
# ❌ BAD
logger.info(f"Processing: {patient_data}")  # Logs PHI

# ✅ GOOD
logger.info(f"Processing request for patient ID: {patient.patient_id}")  # No PHI
```

#### 7. Don't Ignore Error Handling

```python
# ❌ BAD
response = await agent.run(prompt)  # What if AI fails?

# ✅ GOOD
try:
    response = await agent.run(prompt)
    if not response:
        return "Unable to generate response. Please try again."
    return response
except Exception as e:
    logger.error(f"AI agent error: {str(e)}")
    return "An error occurred. Please contact support."
```

---

## Prompt Templates Library

### Template 1: Patient Summary

```python
PATIENT_SUMMARY_TEMPLATE = """
Create a comprehensive patient summary for {patient_name} (ID: {patient_id}).

Include:
1. Demographics and contact information
2. Current medical conditions
3. Allergies and contraindications
4. Active medications
5. Recent visit history (last {num_visits} visits)
6. Pending follow-ups or tests

Format as a professional medical summary suitable for physician review.
"""
```

### Template 2: Visit Comparison

```python
VISIT_COMPARISON_TEMPLATE = """
Compare these two visits for patient {patient_id}:

Visit 1 (Baseline): {visit1_date}
Visit 2 (Follow-up): {visit2_date}

Analyze:
1. Changes in vital signs
2. Medication adjustments
3. Symptom progression/improvement
4. Lab result trends
5. Treatment effectiveness

Highlight significant changes and clinical implications.
"""
```

### Template 3: Trend Analysis

```python
TREND_ANALYSIS_TEMPLATE = """
Analyze trends for {measurement_type} over the last {num_visits} visits
for patient {patient_id}.

Provide:
1. Data table showing values and dates
2. Visual description of trend (improving/worsening/stable)
3. Clinical significance
4. Recommendations for continued monitoring

Include confidence assessment based on data completeness.
"""
```

---

## Testing Your Prompts

### How to Test Prompt Effectiveness

```python
import pytest
from app.agents.qa_agent import medical_qa_agent

async def test_prompt_returns_vital_signs_table():
    """Test that AI includes vital signs table in response."""
    question = "What were the patient's vital signs?"

    response = await medical_qa_agent.answer_question(
        question=question,
        patient_id="PAT001",
        visits=[test_visit_with_vitals]
    )

    # Check for table formatting
    assert "| Measurement |" in response
    assert "| Blood Pressure |" in response
    assert "mmHg" in response

async def test_prompt_cites_sources():
    """Test that AI cites data sources."""
    question = "What was the diagnosis?"

    response = await medical_qa_agent.answer_question(
        question=question,
        visits=[test_visit]
    )

    # Check for source citations
    assert "VIS" in response or "Visit" in response
    assert any(date_pattern in response for date_pattern in ["2025-", "202"])

async def test_prompt_no_diagnosis_claims():
    """Test that AI doesn't make diagnostic claims."""
    question = "What's wrong with this patient?"

    response = await medical_qa_agent.answer_question(
        question=question,
        patient_id="PAT001"
    )

    # Check that AI doesn't claim to diagnose
    forbidden_phrases = [
        "i diagnose",
        "my diagnosis is",
        "i conclude that",
        "the patient has" # Without citation
    ]

    response_lower = response.lower()
    for phrase in forbidden_phrases:
        assert phrase not in response_lower
```

---

## Troubleshooting Common Issues

### Issue 1: AI Responses Too Generic

**Problem:**

```
"The patient has diabetes."
```

**Solution: Add specificity requirements**

```python
instructions = """
Be specific. Include:
- Exact measurements with units
- Visit dates
- Reference ranges
- Specific visit IDs

Bad: "The patient has diabetes"
Good: "The patient was diagnosed with Type 2 Diabetes (HbA1c: 7.8%, VIS001, 2025-10-27)"
"""
```

### Issue 2: AI Not Including Tables

**Problem:** AI describes table data but doesn't include the formatted table

**Solution: Be explicit about table preservation**

```python
system_prompt = """
CRITICAL: When you see Markdown tables in the context, you MUST include them
in your response exactly as formatted. Do not describe the table - include the
actual table.

Example:
If context contains:
| Measurement | Value |
|-------------|-------|
| BP | 120/80 |

Your response should include that exact table, not "blood pressure was 120/80"
"""
```

### Issue 3: AI Making Medical Claims

**Problem:** AI says "I recommend..." or "The patient should..."

**Solution: Strengthen role boundaries**

```python
system_prompt = """
YOU ARE NOT A DOCTOR. You are a data analyst helping doctors review information.

Replace phrases like:
❌ "I recommend..."  → ✅ "The data suggests..."
❌ "The patient should..." → ✅ "The physician may consider..."
❌ "This indicates..." → ✅ "This may indicate... (physician review required)"
"""
```

### Issue 4: Inconsistent Response Format

**Problem:** Sometimes gets detailed responses, sometimes brief

**Solution: Use structured output with Pydantic**

```python
from pydantic import BaseModel

class StandardResponse(BaseModel):
    answer: str = Field(min_length=100, description="Detailed answer")
    key_points: List[str] = Field(min_items=3, description="Key findings")
    sources: List[str] = Field(min_items=1, description="Data sources")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")

agent = Agent(result_type=StandardResponse)
```

---

## Advanced: Multi-Turn Conversations

### Maintaining Context Across Questions

```python
class ConversationManager:
    """Manage multi-turn medical conversations."""

    def __init__(self):
        self.message_history = []

    async def ask_question(
        self,
        question: str,
        patient_context: str
    ) -> str:
        """Ask question with conversation history."""

        # Build message history
        if not self.message_history:
            # First question - include full patient context
            user_message = f"{patient_context}\n\nQuestion: {question}"
        else:
            # Subsequent questions - reference previous context
            user_message = f"Follow-up question: {question}"

        # Get AI response
        response = await agent.run_async(
            user_message,
            message_history=self.message_history
        )

        # Update history
        self.message_history.append({
            "role": "user",
            "content": user_message
        })
        self.message_history.append({
            "role": "assistant",
            "content": response
        })

        return response

# Usage
conversation = ConversationManager()

# First question
answer1 = await conversation.ask_question(
    "What was the patient's last BP reading?",
    patient_context=full_patient_data
)
# Response: "128/82 mmHg from visit VIS003..."

# Follow-up question (maintains context)
answer2 = await conversation.ask_question(
    "How does that compare to the previous visit?",
    patient_context=""  # Not needed, uses history
)
# Response: "The previous visit (VIS002) showed 135/88 mmHg,
# so this represents a 7/6 mmHg improvement..."
```

---

## Summary

### Key Takeaways

1. **System Prompts** define AI behavior - craft them carefully
2. **Context is everything** - provide rich, structured patient data
3. **Format matters** - use Markdown tables, headers, and clear structure
4. **Safety first** - never allow diagnoses or prescriptions
5. **Test extensively** - verify AI outputs meet medical standards
6. **Iterate and improve** - prompts get better with real-world testing

### The Prompt Engineering Process

```
1. Define Role → What should the AI be?
2. Set Guidelines → What can/can't it do?
3. Build Context → What data does it need?
4. Format Output → How should it respond?
5. Test & Validate → Does it work correctly?
6. Iterate → Improve based on results
```

### Remember

- Good prompts = Good outputs
- Be specific and explicit
- Include examples
- Validate programmatically
- Prioritize safety and accuracy
- Keep HIPAA compliance in mind

---

_This guide covers the fundamentals of AI prompt engineering in the Medical Assistant project. For more details on specific components, refer to the Architecture Guide._
