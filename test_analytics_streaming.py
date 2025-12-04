"""
Test script for analytics streaming endpoint.
Tests /analytics/query/stream endpoint using httpx.
"""
import asyncio
import httpx
import json


async def test_analytics_stream():
    """Test the /analytics/query/stream endpoint"""
    print("\n" + "="*80)
    print("Testing /analytics/query/stream endpoint")
    print("="*80)
    
    url = "http://localhost:8000/api/v1/analytics/query/stream"
    
    # Note: This endpoint requires authentication
    # You'll need to provide valid credentials or token
    payload = {
        "question": "How many visits in the last 30 days?",
        "explain": True
    }
    
    print(f"\nSending request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\n⚠️  Note: This endpoint requires authentication (ADMIN or DOCTOR role)")
    print("If you get a 401/403 error, you need to add authentication headers\n")
    print("\nStreaming response:\n")
    
    chunk_count = 0
    metadata_received = False
    explanation_chunks = []
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # TODO: Add authentication headers here
            # headers = {"Authorization": "Bearer YOUR_TOKEN"}
            async with client.stream("POST", url, json=payload) as response:
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 401:
                    print("❌ Unauthorized. Please add authentication token.")
                    return False
                elif response.status_code == 403:
                    print("❌ Forbidden. User doesn't have required role (ADMIN or DOCTOR).")
                    return False
                elif response.status_code != 200:
                    print(f"❌ Error: {response.status_code}")
                    content = await response.aread()
                    print(content.decode())
                    return False
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        chunk_count += 1
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        try:
                            data = json.loads(data_str)
                            msg_type = data.get("type", "unknown")
                            
                            if msg_type == "metadata":
                                metadata_received = True
                                print("\n📊 METADATA RECEIVED:")
                                print(f"  Question: {data.get('question')}")
                                print(f"  SQL Query: {data.get('sql_query')}")
                                print(f"  Row Count: {data.get('row_count')}")
                                print(f"  Source: {data.get('source')} (cache/template/ai)")
                                print(f"\n  Results Preview:")
                                results = data.get('results', [])
                                for i, row in enumerate(results[:3]):
                                    print(f"    {i+1}. {row}")
                                if len(results) > 3:
                                    print(f"    ... and {len(results) - 3} more rows")
                                print("\n📝 STREAMING EXPLANATION:\n")
                            
                            elif msg_type == "chunk":
                                content = data.get("content", "")
                                explanation_chunks.append(content)
                                print(content, end="", flush=True)
                            
                            elif msg_type == "done":
                                print(f"\n\n✅ Stream completed!")
                                print(f"Total chunks received: {data.get('total_chunks', chunk_count)}")
                            
                            elif msg_type == "error":
                                print(f"\n\n❌ Error: {data.get('error')}")
                                return False
                        
                        except json.JSONDecodeError as e:
                            print(f"\n⚠️  Failed to parse JSON: {data_str[:100]}")
                
                if metadata_received:
                    full_explanation = "".join(explanation_chunks)
                    print(f"\n\n" + "="*80)
                    print("SUMMARY")
                    print("="*80)
                    print(f"Metadata received: ✅")
                    print(f"Explanation length: {len(full_explanation)} characters")
                    print("="*80 + "\n")
                    return True
                else:
                    print("\n❌ No metadata received")
                    return False
                
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run analytics streaming test"""
    print("\n" + "="*80)
    print("ANALYTICS STREAMING ENDPOINT TEST")
    print("="*80)
    print("\nMake sure:")
    print("1. The server is running: uvicorn app.main:app --reload")
    print("2. You have authentication set up")
    print("3. You have ADMIN or DOCTOR role\n")
    
    await asyncio.sleep(2)
    
    result = await test_analytics_stream()
    
    print("\n" + "="*80)
    print("TEST RESULT")
    print("="*80)
    print(f"Analytics stream: {'✅ PASS' if result else '❌ FAIL'}")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
