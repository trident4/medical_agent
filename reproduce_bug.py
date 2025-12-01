from app.agents.query_templates import QueryTemplates

def test_template_bug():
    qt = QueryTemplates()
    question = "What's the average heart rate across all visits?"
    
    print(f"Testing question: '{question}'")
    sql = qt.match(question)
    print(f"Generated SQL: {sql}")
    
    if "{field}" in sql:
        print("❌ BUG REPRODUCED: {field} placeholder was not replaced.")
    else:
        print("✅ SUCCESS: {field} was replaced.")

if __name__ == "__main__":
    test_template_bug()
