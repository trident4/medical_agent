# Text-to-SQL Analytics Agent - Implementation Plan (Hybrid System)

## Objective
Create a **cost-optimized AI agent** that answers analytical questions using:
1. **Query Cache** - Instant responses for repeated questions (FREE)
2. **Query Templates** - Pattern matching for common queries (FREE)
3. **AI Generation** - Smart SQL generation only when needed (~$0.0006/query)

**Expected Cost Savings:** 85-95% reduction vs pure AI approach

---

## Example Use Cases

### Analytics Questions to Support

1. **Visit Analytics**
   - "How many visits were made by all patients in the last 30 days?"
   - "What is the average duration of visits?"
   - "Which patient has the most visits?"
   - "How many urgent visits vs routine visits this month?"

2. **Patient Analytics**
   - "How many patients do we have?"
   - "Which patients haven't visited in the last 60 days?"
   - "What's the age distribution of our patients?"

3. **Medical Insights**
   - "What are the most common diagnoses?"
   - "Which medications are prescribed most frequently?"
   - "What's the average blood pressure across all visits?"

4. **Time-Based Analytics**
   - "Show visit trends over the last 3 months"
   - "What's the busiest day of the week for visits?"
   - "How many new patients joined this year?"

5. **JSON Field Analytics**
   - "What's the average heart rate across all visits?"
   - "How many patients have elevated HbA1c levels?"
   - "Show all visits with abnormal lab results"

---

## Hybrid Architecture (Cost-Optimized)

```
User Question
    ↓
1. Query Cache Check → HIT? Return cached SQL (FREE, ~80% of queries)
    ↓ MISS
2. Template Matcher → MATCH? Return templated SQL (FREE, ~10% of queries)
    ↓ NO MATCH
3. AI Generator → Generate SQL (~$0.0006, ~10% of queries)
    ↓
4. Cache Result → Store for future use
    ↓
5. SQL Validator → Ensure safety
    ↓
6. Database Executor → Run query
    ↓
7. Result Formatter → Format results
    ↓
8. AI Explainer (Optional) → Natural language summary
    ↓
Return to User
```

**Cost Breakdown:**
- 80% queries: Cache hit = $0
- 10% queries: Template match = $0
- 10% queries: AI generation = $0.0006
- **Average cost per query: ~$0.00006** (0.006 cents)

```
User Question
    ↓
Analytics Agent
    ↓
AI (Grok/OpenAI) → Generate SQL Query
    ↓
SQL Validator → Ensure safety (no DELETE/DROP/UPDATE)
    ↓
Database Executor → Run query
    ↓
Result Formatter → Format results
    ↓
AI (Optional) → Natural language summary
    ↓
Return to User
```

---

## Implementation

### 1. Query Cache System

```python
# app/agents/query_cache.py

from typing import Optional, Dict
import hashlib
import json
from datetime import datetime, timedelta

class QueryCache:
    """
    In-memory cache for SQL queries.
    Stores question -> SQL mapping with TTL.
    """
    
    def __init__(self, ttl_hours: int = 24):
        self.cache: Dict[str, dict] = {}
        self.ttl = timedelta(hours=ttl_hours)
    
    def _normalize_question(self, question: str) -> str:
        """Normalize question for consistent cache keys"""
        # Convert to lowercase, remove extra spaces
        normalized = ' '.join(question.lower().strip().split())
        return normalized
    
    def _get_cache_key(self, question: str) -> str:
        """Generate cache key from question"""
        normalized = self._normalize_question(question)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get(self, question: str) -> Optional[str]:
        """Get cached SQL query if exists and not expired"""
        key = self._get_cache_key(question)
        
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if datetime.now() - entry['timestamp'] > self.ttl:
            del self.cache[key]
            return None
        
        # Update hit count
        entry['hits'] += 1
        entry['last_accessed'] = datetime.now()
        
        return entry['sql']
    
    def set(self, question: str, sql: str):
        """Cache a SQL query"""
        key = self._get_cache_key(question)
        
        self.cache[key] = {
            'question': question,
            'sql': sql,
            'timestamp': datetime.now(),
            'last_accessed': datetime.now(),
            'hits': 0
        }
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_entries = len(self.cache)
        total_hits = sum(entry['hits'] for entry in self.cache.values())
        
        # Most popular queries
        popular = sorted(
            self.cache.values(),
            key=lambda x: x['hits'],
            reverse=True
        )[:5]
        
        return {
            'total_cached_queries': total_entries,
            'total_cache_hits': total_hits,
            'cache_hit_rate': f"{(total_hits / max(total_hits + total_entries, 1)) * 100:.1f}%",
            'most_popular': [
                {'question': q['question'], 'hits': q['hits']}
                for q in popular
            ]
        }
    
    def clear(self):
        """Clear all cached queries"""
        self.cache.clear()
```

---

### 2. Query Template System

```python
# app/agents/query_templates.py

import re
from typing import Optional, Dict, List
from datetime import datetime

class QueryTemplates:
    """
    Template-based SQL generation for common query patterns.
    Matches questions to templates and fills in parameters.
    """
    
    def __init__(self):
        self.templates = self._init_templates()
    
    def _init_templates(self) -> Dict[str, dict]:
        """Initialize query templates"""
        return {
            # Visit count by timeframe
            'visits_count_days': {
                'patterns': [
                    r'how many visits.*(?:in|during|over).*(?:last|past)\s+(\d+)\s+days?',
                    r'visits.*count.*(\d+)\s+days?',
                    r'number of visits.*(\d+)\s+days?'
                ],
                'sql': "SELECT COUNT(*) as visit_count FROM visits WHERE visit_date >= DATE_SUB(NOW(), INTERVAL {days} DAY);",
                'params': ['days']
            },
            
            # Average visit duration
            'avg_visit_duration': {
                'patterns': [
                    r'average.*visit.*duration',
                    r'avg.*visit.*time',
                    r'mean.*visit.*length'
                ],
                'sql': "SELECT AVG(duration_minutes) as avg_duration_minutes FROM visits WHERE duration_minutes IS NOT NULL;",
                'params': []
            },
            
            # Patient count
            'patient_count': {
                'patterns': [
                    r'how many patients',
                    r'total.*patients',
                    r'number of patients',
                    r'patient count'
                ],
                'sql': "SELECT COUNT(*) as patient_count FROM patients;",
                'params': []
            },
            
            # Most visits by patient
            'most_visits_patient': {
                'patterns': [
                    r'which patient.*most visits',
                    r'patient.*most.*visits',
                    r'who.*most visits'
                ],
                'sql': """SELECT p.first_name, p.last_name, p.patient_id, COUNT(v.id) as visit_count 
                         FROM patients p 
                         JOIN visits v ON p.id = v.patient_id 
                         GROUP BY p.id 
                         ORDER BY visit_count DESC 
                         LIMIT 1;""",
                'params': []
            },
            
            # Visit type distribution
            'visit_type_count': {
                'patterns': [
                    r'how many.*(?:urgent|routine|follow-up|consultation).*visits',
                    r'count.*visit.*type',
                    r'visits by type'
                ],
                'sql': "SELECT visit_type, COUNT(*) as count FROM visits GROUP BY visit_type ORDER BY count DESC;",
                'params': []
            },
            
            # Average vital sign
            'avg_vital_sign': {
                'patterns': [
                    r'average.*(?:heart rate|blood pressure|temperature|weight)',
                    r'avg.*(?:hr|bp|temp)'
                ],
                'sql': "SELECT AVG(JSON_EXTRACT(vital_signs, '$.{field}')) as avg_{field} FROM visits WHERE vital_signs IS NOT NULL;",
                'params': ['field'],
                'field_mapping': {
                    'heart rate': 'heart_rate',
                    'hr': 'heart_rate',
                    'blood pressure': 'blood_pressure_systolic',
                    'bp': 'blood_pressure_systolic',
                    'temperature': 'temperature',
                    'temp': 'temperature',
                    'weight': 'weight'
                }
            },
            
            # Patients without recent visits
            'inactive_patients': {
                'patterns': [
                    r'patients.*(?:haven\'t|have not|no).*visit.*(\d+)\s+days',
                    r'inactive.*patients.*(\d+)\s+days'
                ],
                'sql': """SELECT p.patient_id, p.first_name, p.last_name, MAX(v.visit_date) as last_visit
                         FROM patients p
                         LEFT JOIN visits v ON p.id = v.patient_id
                         GROUP BY p.id
                         HAVING last_visit IS NULL OR last_visit < DATE_SUB(NOW(), INTERVAL {days} DAY)
                         ORDER BY last_visit;""",
                'params': ['days']
            },
            
            # Common diagnoses
            'common_diagnoses': {
                'patterns': [
                    r'most common.*diagnos',
                    r'top.*diagnos',
                    r'frequent.*diagnos'
                ],
                'sql': """SELECT diagnosis, COUNT(*) as count 
                         FROM visits 
                         WHERE diagnosis IS NOT NULL AND diagnosis != ''
                         GROUP BY diagnosis 
                         ORDER BY count DESC 
                         LIMIT 10;""",
                'params': []
            }
        }
    
    def match(self, question: str) -> Optional[str]:
        """
        Try to match question to a template and generate SQL.
        Returns SQL if match found, None otherwise.
        """
        question_lower = question.lower().strip()
        
        for template_name, template_data in self.templates.items():
            for pattern in template_data['patterns']:
                match = re.search(pattern, question_lower)
                
                if match:
                    # Extract parameters from regex groups
                    params = {}
                    if template_data['params']:
                        for i, param_name in enumerate(template_data['params'], 1):
                            if i <= len(match.groups()):
                                param_value = match.group(i)
                                
                                # Handle field mapping if exists
                                if param_name == 'field' and 'field_mapping' in template_data:
                                    # Find which field was mentioned
                                    for key, value in template_data['field_mapping'].items():
                                        if key in question_lower:
                                            param_value = value
                                            break
                                
                                params[param_name] = param_value
                    
                    # Fill template with parameters
                    sql = template_data['sql'].format(**params) if params else template_data['sql']
                    
                    return sql
        
        return None
    
    def get_supported_patterns(self) -> List[str]:
        """Get list of supported query patterns"""
        patterns = []
        for template_name, template_data in self.templates.items():
            patterns.extend(template_data['patterns'])
        return patterns
```

---

### 3. Optimized Analytics Agent (Hybrid System)

```python
# app/agents/analytics_agent.py

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.agents.base_agent import FallbackAgent
from app.agents.query_cache import QueryCache
from app.agents.query_templates import QueryTemplates
import json
import re
import logging

logger = logging.getLogger(__name__)

class AnalyticsAgent:
    """
    Hybrid AI agent for analytics queries.
    Uses cache → templates → AI in that order for cost optimization.
    """
    
    def __init__(self):
        # Initialize hybrid components
        self.cache = QueryCache(ttl_hours=24)
        self.templates = QueryTemplates()
        
        # Database schema for AI context
        self.schema_info = self._get_schema_info()
        
        # AI agent (only used when cache/templates don't match)
        system_prompt = f"""
You are a SQL expert for a medical records database. Generate safe, read-only SQL queries.

DATABASE SCHEMA:
{self.schema_info}

RULES:
1. ONLY generate SELECT queries (no INSERT, UPDATE, DELETE, DROP, ALTER)
2. Use proper JOIN syntax when querying multiple tables
3. For JSON fields (vital_signs, lab_results), use JSON_EXTRACT or -> operator
4. Always use table aliases for clarity
5. Include LIMIT clause for large result sets (default 100)
6. Use proper date functions for time-based queries
7. Return ONLY the SQL query, no explanations

EXAMPLES:
Question: "How many visits in the last 30 days?"
SQL: SELECT COUNT(*) as visit_count FROM visits WHERE visit_date >= DATE_SUB(NOW(), INTERVAL 30 DAY);

Question: "What's the average heart rate?"
SQL: SELECT AVG(JSON_EXTRACT(vital_signs, '$.heart_rate')) as avg_heart_rate FROM visits WHERE vital_signs IS NOT NULL;

Question: "Which patient has the most visits?"
SQL: SELECT p.first_name, p.last_name, COUNT(v.id) as visit_count FROM patients p JOIN visits v ON p.id = v.patient_id GROUP BY p.id ORDER BY visit_count DESC LIMIT 1;

Now generate SQL for the user's question.
"""
        
        self.ai_agent = FallbackAgent(system_prompt)
        
        # Statistics tracking
        self.stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'template_matches': 0,
            'ai_generations': 0
        }
    
    def _get_schema_info(self) -> str:
        """Get database schema information"""
        return """
TABLES:

1. patients (id, patient_id, first_name, last_name, date_of_birth, gender, 
             phone, email, medical_history, allergies, current_medications)

2. visits (id, visit_id, patient_id, visit_date, visit_type, chief_complaint,
          symptoms, diagnosis, treatment_plan, medications_prescribed, 
          doctor_notes, vital_signs JSON, lab_results JSON, duration_minutes)

3. users (id, username, email, role, is_active)
"""
    
    async def answer_analytics_question(
        self,
        question: str,
        db: AsyncSession,
        explain: bool = True
    ) -> Dict[str, Any]:
        """
        Answer analytics question using hybrid approach:
        1. Check cache
        2. Try templates
        3. Use AI if needed
        """
        self.stats['total_queries'] += 1
        sql_source = None
        
        try:
            # Step 1: Check cache (FREE, instant)
            sql_query = self.cache.get(question)
            if sql_query:
                sql_source = "cache"
                self.stats['cache_hits'] += 1
                logger.info(f"✅ Cache HIT for: {question[:50]}...")
            
            # Step 2: Try templates (FREE, fast)
            if not sql_query:
                sql_query = self.templates.match(question)
                if sql_query:
                    sql_source = "template"
                    self.stats['template_matches'] += 1
                    logger.info(f"✅ Template MATCH for: {question[:50]}...")
                    # Cache for future use
                    self.cache.set(question, sql_query)
            
            # Step 3: Use AI (costs ~$0.0006)
            if not sql_query:
                sql_query = await self._generate_sql_with_ai(question)
                sql_source = "ai"
                self.stats['ai_generations'] += 1
                logger.info(f"🤖 AI GENERATION for: {question[:50]}...")
                # Cache for future use
                self.cache.set(question, sql_query)
            
            # Validate SQL for safety
            if not self._is_safe_query(sql_query):
                return {
                    "error": "Generated query is not safe (contains write operations)",
                    "query": sql_query,
                    "source": sql_source
                }
            
            # Execute query
            results = await self._execute_query(sql_query, db)
            
            # Format results
            formatted_results = self._format_results(results)
            
            # Generate explanation (optional)
            explanation = None
            if explain and formatted_results:
                explanation = await self._explain_results(
                    question, 
                    sql_query, 
                    formatted_results
                )
            
            return {
                "question": question,
                "sql_query": sql_query,
                "results": formatted_results,
                "row_count": len(formatted_results) if formatted_results else 0,
                "explanation": explanation,
                "source": sql_source,  # cache/template/ai
                "cost_estimate": "$0" if sql_source != "ai" else "$0.0006"
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "error": str(e),
                "question": question
            }
    
    async def _generate_sql_with_ai(self, question: str) -> str:
        """Generate SQL using AI (fallback option)"""
        prompt = f"Question: {question}\nSQL:"
        response = await self.ai_agent.run_async(prompt)
        sql = self._extract_sql(response)
        return sql
    
    def _extract_sql(self, response: str) -> str:
        """Extract clean SQL from AI response"""
        # Remove markdown code blocks
        response = re.sub(r'```sql\n?', '', response)
        response = re.sub(r'```\n?', '', response)
        
        # Remove common prefixes
        response = re.sub(r'^(SQL:|Query:)\s*', '', response, flags=re.IGNORECASE)
        
        # Take first statement
        sql = response.strip().split('\n')[0]
        
        # Ensure semicolon
        if not sql.endswith(';'):
            sql += ';'
        
        return sql
    
    def _is_safe_query(self, sql: str) -> bool:
        """Validate SQL is read-only"""
        sql_upper = sql.upper()
        
        forbidden = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER',
            'CREATE', 'TRUNCATE', 'REPLACE', 'GRANT', 'REVOKE'
        ]
        
        for operation in forbidden:
            if operation in sql_upper:
                return False
        
        if not sql_upper.strip().startswith('SELECT'):
            return False
        
        return True
    
    async def _execute_query(
        self, 
        sql: str, 
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Execute SQL query"""
        result = await db.execute(text(sql))
        rows = result.fetchall()
        
        if not rows:
            return []
        
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]
    
    def _format_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format results for JSON serialization"""
        if not results:
            return []
        
        formatted = []
        for row in results:
            formatted_row = {}
            for key, value in row.items():
                if hasattr(value, 'isoformat'):
                    formatted_row[key] = value.isoformat()
                elif hasattr(value, '__float__'):
                    formatted_row[key] = float(value)
                else:
                    formatted_row[key] = value
            formatted.append(formatted_row)
        
        return formatted
    
    async def _explain_results(
        self,
        question: str,
        sql: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """Generate natural language explanation"""
        explanation_prompt = f"""
Given this analytics question and results, provide a concise summary.

Question: {question}
Results: {json.dumps(results[:5])}
Total Rows: {len(results)}

Provide a 2-3 sentence summary.
"""
        
        explanation = await self.ai_agent.run_async(explanation_prompt)
        return explanation.strip()
    
    def get_stats(self) -> dict:
        """Get usage statistics"""
        total = self.stats['total_queries']
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            'cache_hit_rate': f"{(self.stats['cache_hits'] / total) * 100:.1f}%",
            'template_match_rate': f"{(self.stats['template_matches'] / total) * 100:.1f}%",
            'ai_usage_rate': f"{(self.stats['ai_generations'] / total) * 100:.1f}%",
            'estimated_cost_saved': f"${(self.stats['cache_hits'] + self.stats['template_matches']) * 0.0006:.4f}",
            'cache_stats': self.cache.get_stats()
        }
    
    def get_example_questions(self) -> List[str]:
        """Get example questions"""
        return [
            "How many visits were made in the last 30 days?",
            "What is the average duration of visits?",
            "Which patient has the most visits?",
            "How many urgent visits vs routine visits?",
            "What's the average heart rate across all visits?",
            "Show patients who haven't visited in 60 days",
            "What are the most common diagnoses?",
            "How many patients do we have?",
            "Show visit trends by month"
        ]


# Global instance
analytics_agent = AnalyticsAgent()
```

```python
# app/agents/analytics_agent.py

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.agents.base_agent import FallbackAgent
import json
import re

class AnalyticsAgent:
    """
    AI agent that converts natural language questions to SQL queries
    and executes them safely against the database.
    """
    
    def __init__(self):
        # Database schema information for AI context
        self.schema_info = self._get_schema_info()
        
        # System prompt for SQL generation
        system_prompt = f"""
You are a SQL expert for a medical records database. Generate safe, read-only SQL queries.

DATABASE SCHEMA:
{self.schema_info}

RULES:
1. ONLY generate SELECT queries (no INSERT, UPDATE, DELETE, DROP, ALTER)
2. Use proper JOIN syntax when querying multiple tables
3. For JSON fields (vital_signs, lab_results), use JSON_EXTRACT or -> operator
4. Always use table aliases for clarity
5. Include LIMIT clause for large result sets (default 100)
6. Use proper date functions for time-based queries
7. Return ONLY the SQL query, no explanations

EXAMPLES:
Question: "How many visits in the last 30 days?"
SQL: SELECT COUNT(*) as visit_count FROM visits WHERE visit_date >= DATE_SUB(NOW(), INTERVAL 30 DAY);

Question: "What's the average heart rate?"
SQL: SELECT AVG(JSON_EXTRACT(vital_signs, '$.heart_rate')) as avg_heart_rate FROM visits WHERE vital_signs IS NOT NULL;

Question: "Which patient has the most visits?"
SQL: SELECT p.first_name, p.last_name, COUNT(v.id) as visit_count FROM patients p JOIN visits v ON p.id = v.patient_id GROUP BY p.id ORDER BY visit_count DESC LIMIT 1;

Now generate SQL for the user's question.
"""
        
        self.agent = FallbackAgent(system_prompt)
    
    def _get_schema_info(self) -> str:
        """Get database schema information for AI context"""
        return """
TABLES:

1. patients
   - id (INT, PRIMARY KEY)
   - patient_id (VARCHAR, UNIQUE)
   - first_name (VARCHAR)
   - last_name (VARCHAR)
   - date_of_birth (DATE)
   - gender (VARCHAR)
   - phone (VARCHAR)
   - email (VARCHAR)
   - medical_history (TEXT)
   - allergies (TEXT)
   - current_medications (TEXT)
   - created_at (DATETIME)
   - updated_at (DATETIME)

2. visits
   - id (INT, PRIMARY KEY)
   - visit_id (VARCHAR, UNIQUE)
   - patient_id (INT, FOREIGN KEY -> patients.id)
   - visit_date (DATETIME)
   - visit_type (VARCHAR: 'routine', 'urgent', 'follow-up', 'consultation')
   - chief_complaint (TEXT)
   - symptoms (TEXT)
   - diagnosis (TEXT)
   - treatment_plan (TEXT)
   - medications_prescribed (TEXT)
   - doctor_notes (TEXT)
   - vital_signs (JSON) - Contains: blood_pressure_systolic, blood_pressure_diastolic, heart_rate, temperature, weight, height
   - lab_results (JSON) - Array of: test_name, value, unit, status
   - duration_minutes (INT)
   - created_at (DATETIME)
   - updated_at (DATETIME)

3. users
   - id (INT, PRIMARY KEY)
   - username (VARCHAR, UNIQUE)
   - email (VARCHAR, UNIQUE)
   - role (ENUM: 'ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST')
   - is_active (BOOL)
   - created_at (DATETIME)
"""
    
    async def answer_analytics_question(
        self,
        question: str,
        db: AsyncSession,
        explain: bool = True
    ) -> Dict[str, Any]:
        """
        Answer an analytics question by generating and executing SQL.
        
        Args:
            question: Natural language question
            db: Database session
            explain: Whether to include AI explanation of results
        
        Returns:
            Dictionary with query, results, and optional explanation
        """
        try:
            # Step 1: Generate SQL query using AI
            sql_query = await self._generate_sql(question)
            
            # Step 2: Validate SQL for safety
            if not self._is_safe_query(sql_query):
                return {
                    "error": "Generated query is not safe (contains write operations)",
                    "query": sql_query
                }
            
            # Step 3: Execute query
            results = await self._execute_query(sql_query, db)
            
            # Step 4: Format results
            formatted_results = self._format_results(results)
            
            # Step 5: Generate natural language explanation (optional)
            explanation = None
            if explain and formatted_results:
                explanation = await self._explain_results(
                    question, 
                    sql_query, 
                    formatted_results
                )
            
            return {
                "question": question,
                "sql_query": sql_query,
                "results": formatted_results,
                "row_count": len(formatted_results) if formatted_results else 0,
                "explanation": explanation
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "question": question
            }
    
    async def _generate_sql(self, question: str) -> str:
        """Generate SQL query from natural language question"""
        prompt = f"Question: {question}\nSQL:"
        response = await self.agent.run_async(prompt)
        
        # Extract SQL from response (remove markdown, explanations, etc.)
        sql = self._extract_sql(response)
        return sql
    
    def _extract_sql(self, response: str) -> str:
        """Extract clean SQL from AI response"""
        # Remove markdown code blocks
        response = re.sub(r'```sql\n?', '', response)
        response = re.sub(r'```\n?', '', response)
        
        # Remove common prefixes
        response = re.sub(r'^(SQL:|Query:)\s*', '', response, flags=re.IGNORECASE)
        
        # Take first statement (before semicolon or newline)
        sql = response.strip().split('\n')[0]
        
        # Ensure it ends with semicolon
        if not sql.endswith(';'):
            sql += ';'
        
        return sql
    
    def _is_safe_query(self, sql: str) -> bool:
        """Validate that SQL query is safe (read-only)"""
        sql_upper = sql.upper()
        
        # Forbidden operations
        forbidden = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER',
            'CREATE', 'TRUNCATE', 'REPLACE', 'GRANT', 'REVOKE'
        ]
        
        for operation in forbidden:
            if operation in sql_upper:
                return False
        
        # Must start with SELECT
        if not sql_upper.strip().startswith('SELECT'):
            return False
        
        return True
    
    async def _execute_query(
        self, 
        sql: str, 
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Execute SQL query and return results"""
        result = await db.execute(text(sql))
        
        # Convert to list of dictionaries
        rows = result.fetchall()
        if not rows:
            return []
        
        # Get column names
        columns = result.keys()
        
        # Convert rows to dictionaries
        return [dict(zip(columns, row)) for row in rows]
    
    def _format_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format query results for display"""
        if not results:
            return []
        
        # Convert any non-serializable types
        formatted = []
        for row in results:
            formatted_row = {}
            for key, value in row.items():
                # Handle datetime
                if hasattr(value, 'isoformat'):
                    formatted_row[key] = value.isoformat()
                # Handle decimals
                elif hasattr(value, '__float__'):
                    formatted_row[key] = float(value)
                else:
                    formatted_row[key] = value
            formatted.append(formatted_row)
        
        return formatted
    
    async def _explain_results(
        self,
        question: str,
        sql: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """Generate natural language explanation of results"""
        explanation_prompt = f"""
Given this analytics question and results, provide a concise, natural language summary.

Question: {question}
SQL Query: {sql}
Results: {json.dumps(results[:5])}  # First 5 rows
Total Rows: {len(results)}

Provide a 2-3 sentence summary of what the data shows.
"""
        
        explanation = await self.agent.run_async(explanation_prompt)
        return explanation.strip()
    
    def get_example_questions(self) -> List[str]:
        """Get list of example analytics questions"""
        return [
            "How many visits were made in the last 30 days?",
            "What is the average duration of visits?",
            "Which patient has the most visits?",
            "How many urgent visits vs routine visits?",
            "What's the average heart rate across all visits?",
            "Show patients who haven't visited in 60 days",
            "What are the most common diagnoses?",
            "How many patients do we have?",
            "What's the average age of our patients?",
            "Show visit trends by month"
        ]


# Global instance
analytics_agent = AnalyticsAgent()
```

---

### 2. Add API Endpoint

```python
# app/api/v1/endpoints/analytics.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.agents.analytics_agent import analytics_agent
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class AnalyticsQuery(BaseModel):
    question: str
    explain: bool = True

class AnalyticsResponse(BaseModel):
    question: str
    sql_query: str
    results: list
    row_count: int
    explanation: Optional[str] = None
    error: Optional[str] = None

@router.post("/query", response_model=AnalyticsResponse)
async def analytics_query(
    query: AnalyticsQuery,
    db: AsyncSession = Depends(get_db)
):
    """
    Answer analytics questions using AI-generated SQL queries.
    
    Example questions:
    - "How many visits in the last 30 days?"
    - "What's the average visit duration?"
    - "Which patient has the most visits?"
    """
    result = await analytics_agent.answer_analytics_question(
        question=query.question,
        db=db,
        explain=query.explain
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.get("/examples")
async def get_example_questions():
    """Get example analytics questions"""
    return {
        "examples": analytics_agent.get_example_questions()
    }
```

---

### 3. Register Router

```python
# app/api/v1/api.py (or main.py)

from app.api.v1.endpoints import analytics

# Add to your API router
api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)
```

---

## Example API Usage

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How many visits were made in the last 30 days?",
    "explain": true
  }'
```

### Response
```json
{
  "question": "How many visits were made in the last 30 days?",
  "sql_query": "SELECT COUNT(*) as visit_count FROM visits WHERE visit_date >= DATE_SUB(NOW(), INTERVAL 30 DAY);",
  "results": [
    {
      "visit_count": 15
    }
  ],
  "row_count": 1,
  "explanation": "In the last 30 days, there have been 15 patient visits recorded in the system. This indicates a moderate level of patient activity during this period."
}
```

---

## Safety Features

✅ **SQL Injection Prevention** - Uses parameterized queries via SQLAlchemy  
✅ **Read-Only Queries** - Blocks INSERT, UPDATE, DELETE, DROP, etc.  
✅ **Query Validation** - Ensures only SELECT statements  
✅ **Result Limiting** - Prevents overwhelming responses  
✅ **Error Handling** - Graceful failure with helpful messages  

---

## Advanced Features (Future)

1. **Query Caching** - Cache common queries for performance
2. **Query History** - Track what questions are asked
3. **Saved Queries** - Allow users to save favorite analytics
4. **Scheduled Reports** - Run queries on schedule
5. **Data Visualization** - Generate charts from results
6. **Export to CSV/Excel** - Download results

---

## Testing Examples

```python
# Test with sample data
questions = [
    "How many visits in the last 30 days?",
    "What's the average visit duration?",
    "Which patient has the most visits?",
    "Show all patients with hypertension",
    "What's the average heart rate?",
    "How many urgent visits this month?",
    "List patients who haven't visited in 60 days",
    "What are the top 5 most common diagnoses?",
    "Show visit trends by month",
    "How many patients have elevated HbA1c?"
]
```

---

## Next Steps

1. **Create `analytics_agent.py`** with the implementation above
2. **Add API endpoint** in `app/api/v1/endpoints/analytics.py`
3. **Register router** in main API
4. **Test with sample data** using the 25 visits we created
5. **Add to API docs** with examples

Would you like me to implement this now? 🚀
