#!/usr/bin/env python3
"""
Simple X.AI API test to verify your key works.
Run this after adding your X.AI API key to .env
"""

import requests
import json
from app.config import settings


def test_xai_key_simple():
    """Simple test of X.AI API key."""
    print("🤖 Testing X.AI API Key")
    print("=" * 40)

    api_key = settings.XAI_API_KEY

    if not api_key or api_key == "your-xai-api-key-here":
        print("❌ No X.AI API key found!")
        print("Please add your X.AI API key to .env file:")
        print("XAI_API_KEY=your-actual-key-here")
        return False

    # Mask key for display
    print(f"🔑 Testing key: [REDACTED]")

    # Try X.AI API (adjust endpoint as needed)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "grok-beta",  # or whatever X.AI uses
        "messages": [{"role": "user", "content": "Hello, test message"}],
        "max_tokens": 10
    }

    # Try different possible X.AI endpoints
    endpoints = [
        "https://api.x.ai/v1/chat/completions",
        "https://api.xai.com/v1/chat/completions",
        "https://grok-api.x.ai/v1/chat/completions"
    ]

    for endpoint in endpoints:
        print(f"\n🌐 Trying endpoint: {endpoint}")
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=15
            )

            print(f"📡 Response status: {response.status_code}")

            if response.status_code == 200:
                print("✅ X.AI API is working!")
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0].get(
                        'message', {}).get('content', 'No content')
                    print(f"🤖 Response: {content}")
                return True
            elif response.status_code == 401:
                print("❌ Unauthorized - check your API key")
            elif response.status_code == 404:
                print("⚠️  Endpoint not found - trying next one...")
                continue
            else:
                print(
                    f"⚠️  Status {response.status_code}: {response.text[:200]}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            continue

    print("\n⚠️  All endpoints failed")
    return False


def show_xai_setup_help():
    """Show help for setting up X.AI."""
    print("\n📋 X.AI Setup Guide:")
    print("=" * 40)
    print("1. Get X.AI API access from their platform")
    print("2. Copy your API key")
    print("3. Add to .env file:")
    print("   XAI_API_KEY=your-actual-key-here")
    print("4. Run this test again")
    print("\n💡 Note: X.AI endpoints and model names may vary")
    print("   Check X.AI documentation for correct:")
    print("   • API endpoint URL")
    print("   • Model names (grok-beta, grok-1, etc.)")
    print("   • Authentication format")


if __name__ == "__main__":
    success = test_xai_key_simple()

    if not success:
        show_xai_setup_help()
    else:
        print("\n🎉 Ready to use X.AI as fallback!")
        print("Your medical assistant will use:")
        print("1. OpenAI (if available)")
        print("2. X.AI (your working key!)")
        print("3. Anthropic (if configured)")
