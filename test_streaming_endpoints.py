"""
Test script for streaming endpoints.
Tests /summarize/stream and /ask/stream endpoints using httpx.
"""
import asyncio
import httpx
import json


async def test_ask_stream():
    """Test the /ask/stream endpoint"""
    print("\n" + "="*80)
    print("Testing /ask/stream endpoint")
    print("="*80)
    
    url = "http://localhost:8000/api/v1/agents/ask/stream"
    payload = {
        "question": "What is diabetes?",
        "context_type": "all"
    }
    
    print(f"\nSending request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nStreaming response:\n")
    
    chunk_count = 0
    total_content = ""
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                print(f"Status Code: {response.status_code}")
                print(f"Headers: {dict(response.headers)}\n")
                
                if response.status_code != 200:
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
                            content = data.get("content", "")
                            is_done = data.get("done", False)
                            
                            if msg_type == "chunk":
                                total_content += content
                                # Print chunk with visual indicator
                                print(f"[Chunk {chunk_count}] {content}", end="", flush=True)
                            elif msg_type == "done":
                                print(f"\n\n✅ Stream completed!")
                                print(f"Total chunks received: {data.get('total_chunks', chunk_count)}")
                            elif msg_type == "error":
                                print(f"\n\n❌ Error: {data.get('error')}")
                                return False
                            elif msg_type == "start":
                                print(f"🚀 Stream started at {data.get('timestamp')}")
                        
                        except json.JSONDecodeError as e:
                            print(f"\n⚠️  Failed to parse JSON: {data_str[:100]}")
                
                print(f"\n\nFull response ({len(total_content)} characters):")
                print("-" * 80)
                print(total_content)
                print("-" * 80)
                
                return True
                
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_summarize_stream():
    """Test the /summarize/stream endpoint"""
    print("\n" + "="*80)
    print("Testing /summarize/stream endpoint")
    print("="*80)
    
    url = "http://localhost:8000/api/v1/agents/summarize/stream"
    payload = {
        "visit_id": "V001",  # You'll need to use a real visit ID from your DB
        "summary_type": "comprehensive",
        "include_patient_history": True
    }
    
    print(f"\nSending request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\n⚠️  Note: This test requires a valid visit_id in your database")
    print("If you get a 404 error, update the visit_id in the test script\n")
    print("\nStreaming response:\n")
    
    chunk_count = 0
    total_content = ""
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 404:
                    print("❌ Visit not found. Please update visit_id in test script.")
                    return False
                elif response.status_code != 200:
                    print(f"❌ Error: {response.status_code}")
                    content = await response.aread()
                    print(content.decode())
                    return False
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        chunk_count += 1
                        data_str = line[6:]
                        
                        try:
                            data = json.loads(data_str)
                            msg_type = data.get("type", "unknown")
                            content = data.get("content", "")
                            
                            if msg_type == "chunk":
                                total_content += content
                                print(f"[Chunk {chunk_count}] {content}", end="", flush=True)
                            elif msg_type == "done":
                                print(f"\n\n✅ Stream completed!")
                                print(f"Total chunks: {data.get('total_chunks', chunk_count)}")
                            elif msg_type == "error":
                                print(f"\n\n❌ Error: {data.get('error')}")
                                return False
                        
                        except json.JSONDecodeError:
                            pass
                
                print(f"\n\nFull summary ({len(total_content)} characters):")
                print("-" * 80)
                print(total_content)
                print("-" * 80)
                
                return True
                
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all streaming tests"""
    print("\n" + "="*80)
    print("STREAMING ENDPOINTS TEST SUITE")
    print("="*80)
    print("\nMake sure the server is running: uvicorn app.main:app --reload")
    print("Press Ctrl+C to cancel\n")
    
    await asyncio.sleep(2)  # Give user time to read
    
    # Test /ask/stream (should work without DB data)
    ask_result = await test_ask_stream()
    
    # Test /summarize/stream (requires valid visit_id)
    # Uncomment when you have a valid visit_id
    # summarize_result = await test_summarize_stream()
    
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    print(f"/ask/stream:       {'✅ PASS' if ask_result else '❌ FAIL'}")
    # print(f"/summarize/stream: {'✅ PASS' if summarize_result else '❌ FAIL'}")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
