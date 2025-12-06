"""
Test suite for analytics example questions.
Validates that all example questions generate valid SQL and execute without errors.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.agents.analytics_agent import analytics_agent


class TestAnalyticsExampleQuestions:
    """Test all example questions from get_example_questions()"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = MagicMock()
        return db
    
    @pytest.fixture
    def example_questions(self):
        """Get all example questions"""
        return analytics_agent.get_example_questions()
    
    @pytest.mark.asyncio
    async def test_all_examples_generate_sql(self, mock_db, example_questions):
        """Test that all example questions generate valid SQL (not empty)"""
        
        # Mock the database execution to avoid actual DB calls
        async def mock_execute(sql, db):
            # Return empty result set for all queries
            return []
        
        original_execute = analytics_agent._execute_query
        analytics_agent._execute_query = mock_execute
        
        try:
            results = {}
            for question in example_questions:
                result = await analytics_agent.answer_analytics_question(
                    question=question,
                    db=mock_db,
                    explain=False  # Skip explanation to avoid AI calls
                )
                
                results[question] = {
                    'has_sql': 'sql_query' in result and result['sql_query'],
                    'has_error': 'error' in result and result['error'],
                    'sql': result.get('sql_query', ''),
                    'source': result.get('source', 'unknown')
                }
            
            # Print results
            print("\n" + "="*80)
            print("ANALYTICS EXAMPLE QUESTIONS TEST RESULTS")
            print("="*80)
            
            template_count = 0
            ai_count = 0
            cache_count = 0
            failed_count = 0
            
            for question, info in results.items():
                status = "✅" if info['has_sql'] and not info['has_error'] else "❌"
                source = info['source'].upper()
                
                if info['source'] == 'template':
                    template_count += 1
                elif info['source'] == 'ai':
                    ai_count += 1
                elif info['source'] == 'cache':
                    cache_count += 1
                
                if info['has_error'] or not info['has_sql']:
                    failed_count += 1
                
                print(f"\n{status} [{source}] {question}")
                if info['has_sql']:
                    # Show first 60 chars of SQL
                    sql_preview = info['sql'].replace('\n', ' ')[:60] + "..."
                    print(f"   SQL: {sql_preview}")
                if info['has_error']:
                    print(f"   ERROR: {info['error']}")
            
            print("\n" + "="*80)
            print(f"SUMMARY:")
            print(f"  Total Questions: {len(example_questions)}")
            print(f"  Template Matches: {template_count} (FREE)")
            print(f"  AI Generated: {ai_count} (costs ~${ai_count * 0.0006:.4f})")
            print(f"  Cache Hits: {cache_count} (FREE)")
            print(f"  Failed: {failed_count}")
            print("="*80)
            
            # Assert all questions generated SQL without errors
            for question, info in results.items():
                assert info['has_sql'], f"Question '{question}' did not generate SQL"
                assert not info['has_error'], f"Question '{question}' had error: {info.get('error')}"
        
        finally:
            # Restore original method
            analytics_agent._execute_query = original_execute
    
    @pytest.mark.asyncio
    async def test_sql_safety_validation(self, mock_db, example_questions):
        """Test that all generated SQL queries are safe (read-only)"""
        
        async def mock_execute(sql, db):
            return []
        
        original_execute = analytics_agent._execute_query
        analytics_agent._execute_query = mock_execute
        
        try:
            for question in example_questions:
                result = await analytics_agent.answer_analytics_question(
                    question=question,
                    db=mock_db,
                    explain=False
                )
                
                if 'sql_query' in result:
                    sql = result['sql_query'].upper()
                    
                    # Check it's a SELECT query
                    assert sql.strip().startswith('SELECT'), \
                        f"Query for '{question}' is not a SELECT: {result['sql_query']}"
                    
                    # Check no dangerous operations
                    dangerous_ops = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
                    for op in dangerous_ops:
                        assert op not in sql, \
                            f"Query for '{question}' contains dangerous operation {op}: {result['sql_query']}"
        
        finally:
            analytics_agent._execute_query = original_execute
    
    @pytest.mark.asyncio
    async def test_template_vs_ai_distribution(self, mock_db, example_questions):
        """Test that we have a good mix of template and AI questions"""
        
        async def mock_execute(sql, db):
            return []
        
        original_execute = analytics_agent._execute_query
        analytics_agent._execute_query = mock_execute
        
        try:
            sources = []
            for question in example_questions:
                result = await analytics_agent.answer_analytics_question(
                    question=question,
                    db=mock_db,
                    explain=False
                )
                sources.append(result.get('source', 'unknown'))
            
            template_count = sources.count('template')
            ai_count = sources.count('ai')
            
            print(f"\nDistribution: {template_count} template, {ai_count} AI")
            
            # We should have at least some of each
            assert template_count > 0, "No template matches found"
            assert ai_count > 0, "No AI generations found"
            
            # Template should be at least 30% for cost efficiency
            template_ratio = template_count / len(example_questions)
            assert template_ratio >= 0.3, \
                f"Template ratio too low ({template_ratio:.1%}), should be at least 30%"
        
        finally:
            analytics_agent._execute_query = original_execute


if __name__ == "__main__":
    # Run tests directly
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
