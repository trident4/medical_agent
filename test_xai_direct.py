#!/usr/bin/env python3
"""
Direct X.AI API test to troubleshoot authentication.
"""

import httpx
import asyncio
from app.config import settings


async def test_xai_direct():
    """Test X.AI API directly with different models."""
    print("🔍 Testing X.AI API Direct")
    print("=" * 40)

    api_key = settings.XAI_API_KEY
    if not api_key:
        print("❌ No X.AI API key found")
        return

    print(f"🔑 Using key: [REDACTED]")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Try different models
    models_to_test = ["grok-3", "grok-beta", "grok-1", "grok"]

    for model in models_to_test:
        print(f"\n🤖 Testing model: {model}")

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Hello, test message"}
            ],
            "max_tokens": 50
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.xai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=15
                )

                print(f"📡 Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {model} works!")
                    if 'choices' in data:
                        content = data['choices'][0]['message']['content']
                        print(f"📝 Response: {content}")
                    return model  # Return the working model
                else:
                    error_data = response.json() if response.headers.get(
                        'content-type', '').startswith('application/json') else response.text
                    print(f"❌ {model} failed: {error_data}")

        except Exception as e:
            print(f"❌ {model} error: {e}")

    print("\n⚠️ No models worked")
    return None


async def main():
    working_model = await test_xai_direct()

    if working_model:
        print(f"\n🎉 Found working model: {working_model}")
        print("Update your base_agent.py to use this model!")
    else:
        print("\n🔧 Troubleshooting suggestions:")
        print("1. Check your X.AI API key is correct")
        print("2. Verify your account has API access")
        print("3. Check X.AI documentation for correct models")
        print("4. Ensure your account has sufficient credits")


if __name__ == "__main__":
    asyncio.run(main())
