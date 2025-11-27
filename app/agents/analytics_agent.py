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