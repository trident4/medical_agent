#!/usr/bin/env python3
"""
Test that exactly mimics the fallback agent X.AI call.
"""

from app.config import settings
import asyncio
import httpx
import sys
sys.path.append('/Users/chetan/Personal/HobbyProjects/doctors-assistant')


async def test_exact_agent_call():
    """Test the exact same call the agent makes."""
    print("🔍 Testing Exact Agent X.AI Call")
    print("=" * 45)

    system_prompt = "You are a helpful medical assistant. Be concise."
    user_input = "What is a normal heart rate range for adults?"

    print(f"🔑 API Key: [REDACTED]")

    headers = {
        "Authorization": f"Bearer {settings.XAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "grok-3",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "max_tokens": 1500,
        "temperature": 0.7
    }

    print(f"🌐 Payload: {payload}")
    print(f"🔧 Headers: {headers}")

    try:
        async with httpx.AsyncClient() as client:
            print("📡 Making request...")
            response = await client.post(
                "https://api.xai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            print(f"📊 Status: {response.status_code}")
            print(f"📝 Response headers: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()
                print("✅ Success!")
                print(f"📋 Response data: {data}")

                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']
                    print(f"💬 Content: {content}")
                    return True
                else:
                    print(f"❌ No choices in response: {data}")
                    return False
            else:
                error_data = response.text
                print(f"❌ Error: {error_data}")

                # Try to parse as JSON
                try:
                    error_json = response.json()
                    print(f"📋 Error JSON: {error_json}")
                except:
                    print("📋 Error is not JSON")

                return False

    except Exception as e:
        print(f"💥 Exception: {e}")
        return False


async def main():
    success = await test_exact_agent_call()

    if success:
        print("\n🎉 Agent call works perfectly!")
    else:
        print("\n🔧 Agent call failed - need to debug further")


if __name__ == "__main__":
    asyncio.run(main())
