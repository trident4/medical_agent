import asyncio
import os
from app.agents.analytics_agent import analytics_agent
from unittest.mock import MagicMock

# Mock DB session since we just want to test the agent's explanation generation
# We can mock the _execute_query method to return a fixed result so we don't need a real DB
async def mock_execute_query(sql, db):
    return [{"visit_count": 6}]

analytics_agent._execute_query = mock_execute_query

async def main():
    print("Running verification...")
    
    # Mock DB session
    mock_db = MagicMock()
    
    result = await analytics_agent.answer_analytics_question(
        question="How many visits in the last 30 days?",
        db=mock_db,
        explain=True
    )
    
    print("\n--- Result ---")
    print(f"Question: {result['question']}")
    print(f"SQL: {result['sql_query']}")
    print(f"Explanation: {result['explanation']}")
    
    if result['explanation'] and len(result['explanation']) > 10:
        print("\n✅ Verification SUCCESS: Explanation generated.")
    else:
        print("\n❌ Verification FAILED: No explanation generated.")

if __name__ == "__main__":
    asyncio.run(main())
