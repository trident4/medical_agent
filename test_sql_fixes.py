import re
from typing import Optional

# Test 1: SQL Extraction Fix
def test_extract_sql():
    """Test that multi-line SQL is extracted correctly"""
    
    def _extract_sql(response: str) -> str:
        """Extract clean SQL from AI response"""
        # Remove markdown code blocks
        response = re.sub(r'```sql\n?', '', response)
        response = re.sub(r'```\n?', '', response)
        
        # Remove common prefixes
        response = re.sub(r'^(SQL:|Query:)\s*', '', response, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean up the response
        response = response.strip()
        
        # If there's a semicolon, take everything up to and including the first semicolon
        # This handles multi-line SQL queries properly
        if ';' in response:
            sql = response.split(';')[0] + ';'
        else:
            # If no semicolon, take the entire response and add one
            sql = response + ';'
        
        # Remove any trailing explanations after the semicolon
        sql = sql.split('\n\n')[0]  # Stop at double newline (explanation separator)
        
        return sql.strip()
    
    # Test case 1: Multi-line SQL
    multiline_response = """SELECT 
    DATE_FORMAT(visit_date, '%Y-%m') as month,
    COUNT(*) as visit_count
FROM visits
GROUP BY month
ORDER BY month DESC;"""
    
    result = _extract_sql(multiline_response)
    print("Test 1 - Multi-line SQL:")
    print(f"Input:\n{multiline_response}")
    print(f"\nOutput:\n{result}")
    
    if "SELECT" in result and "FROM visits" in result and "GROUP BY" in result:
        print("✅ PASS: Multi-line SQL preserved\n")
    else:
        print("❌ FAIL: Multi-line SQL was truncated\n")
    
    # Test case 2: SQL with markdown
    markdown_response = """```sql
SELECT COUNT(*) as total FROM visits;
```"""
    
    result2 = _extract_sql(markdown_response)
    print("Test 2 - Markdown SQL:")
    print(f"Input:\n{markdown_response}")
    print(f"\nOutput:\n{result2}")
    
    if result2 == "SELECT COUNT(*) as total FROM visits;":
        print("✅ PASS: Markdown removed correctly\n")
    else:
        print("❌ FAIL: Markdown not removed correctly\n")


# Test 2: Query Templates
class QueryTemplates:
    def __init__(self):
        self.templates = {
            'visit_trends_month': {
                'patterns': [
                    r'visit.*trends.*month',
                    r'visits.*by month',
                    r'monthly.*visit',
                    r'visits.*per month'
                ],
                'sql': """SELECT 
                         DATE_FORMAT(visit_date, '%Y-%m') as month,
                         COUNT(*) as visit_count
                         FROM visits
                         GROUP BY month
                         ORDER BY month DESC
                         LIMIT 12;""",
                'params': []
            }
        }
    
    def match(self, question: str) -> Optional[str]:
        question_lower = question.lower().strip()
        
        for template_name, template_data in self.templates.items():
            for pattern in template_data['patterns']:
                match = re.search(pattern, question_lower)
                if match:
                    return template_data['sql']
        return None


def test_templates():
    """Test that new templates match correctly"""
    qt = QueryTemplates()
    
    test_questions = [
        "Show visit trends by month",
        "visits by month",
        "monthly visit trends"
    ]
    
    print("Test 3 - Template Matching:")
    for question in test_questions:
        result = qt.match(question)
        print(f"\nQuestion: '{question}'")
        if result:
            print(f"✅ MATCHED: {result[:50]}...")
        else:
            print("❌ NO MATCH")


if __name__ == "__main__":
    print("="*60)
    print("Testing SQL Extraction and Template Fixes")
    print("="*60 + "\n")
    
    test_extract_sql()
    print("\n" + "="*60 + "\n")
    test_templates()
    print("\n" + "="*60)
