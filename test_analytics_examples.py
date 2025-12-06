"""
Standalone test script for analytics example questions.
Tests all example questions without requiring pytest.
"""
import asyncio
from unittest.mock import MagicMock
from app.agents.analytics_agent import analytics_agent


async def test_all_example_questions():
    """Test that all example questions generate valid SQL"""
    
    # Mock database session
    mock_db = MagicMock()
    
    # Mock the database execution to avoid actual DB calls
    async def mock_execute(sql, db):
        return []
    
    original_execute = analytics_agent._execute_query
    analytics_agent._execute_query = mock_execute
    
    try:
        example_questions = analytics_agent.get_example_questions()
        
        print("\n" + "="*80)
        print("ANALYTICS EXAMPLE QUESTIONS TEST")
        print("="*80)
        print(f"Testing {len(example_questions)} example questions...\n")
        
        results = {}
        template_count = 0
        ai_count = 0
        cache_count = 0
        failed_count = 0
        
        for i, question in enumerate(example_questions, 1):
            print(f"[{i}/{len(example_questions)}] Testing: {question}")
            
            try:
                result = await analytics_agent.answer_analytics_question(
                    question=question,
                    db=mock_db,
                    explain=False  # Skip explanation to avoid AI calls
                )
                
                has_sql = 'sql_query' in result and result['sql_query']
                has_error = 'error' in result and result['error']
                source = result.get('source', 'unknown')
                sql = result.get('sql_query', '')
                
                # Track source
                if source == 'template':
                    template_count += 1
                elif source == 'ai':
                    ai_count += 1
                elif source == 'cache':
                    cache_count += 1
                
                # Check for errors
                if has_error or not has_sql:
                    failed_count += 1
                    print(f"   ❌ FAILED [{source.upper()}]")
                    if has_error:
                        print(f"      Error: {result['error']}")
                    if not has_sql:
                        print(f"      No SQL generated")
                else:
                    # Validate SQL is safe
                    sql_upper = sql.upper().strip()
                    is_select = sql_upper.startswith('SELECT')
                    
                    dangerous_ops = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
                    has_dangerous = any(op in sql_upper for op in dangerous_ops)
                    
                    if not is_select:
                        print(f"   ❌ NOT A SELECT QUERY [{source.upper()}]")
                        failed_count += 1
                    elif has_dangerous:
                        print(f"   ❌ CONTAINS DANGEROUS OPERATION [{source.upper()}]")
                        failed_count += 1
                    else:
                        print(f"   ✅ PASS [{source.upper()}]")
                        # Show SQL preview
                        sql_preview = sql.replace('\n', ' ')[:70]
                        print(f"      SQL: {sql_preview}...")
                
                results[question] = {
                    'has_sql': has_sql,
                    'has_error': has_error,
                    'sql': sql,
                    'source': source
                }
                
            except Exception as e:
                print(f"   ❌ EXCEPTION: {str(e)}")
                failed_count += 1
                results[question] = {
                    'has_sql': False,
                    'has_error': True,
                    'sql': '',
                    'source': 'error',
                    'exception': str(e)
                }
            
            print()
        
        # Print summary
        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total Questions:     {len(example_questions)}")
        print(f"Passed:              {len(example_questions) - failed_count}")
        print(f"Failed:              {failed_count}")
        print()
        print(f"Template Matches:    {template_count} (FREE)")
        print(f"AI Generated:        {ai_count} (costs ~${ai_count * 0.0006:.4f})")
        print(f"Cache Hits:          {cache_count} (FREE)")
        print()
        
        template_ratio = template_count / len(example_questions) if example_questions else 0
        print(f"Template Ratio:      {template_ratio:.1%}")
        print(f"Cost Efficiency:     {'✅ Good' if template_ratio >= 0.3 else '⚠️  Low'}")
        print("="*80)
        
        # Final result
        if failed_count == 0:
            print("\n🎉 ALL TESTS PASSED!")
            return True
        else:
            print(f"\n❌ {failed_count} TEST(S) FAILED")
            return False
    
    finally:
        # Restore original method
        analytics_agent._execute_query = original_execute


if __name__ == "__main__":
    success = asyncio.run(test_all_example_questions())
    exit(0 if success else 1)
