#!/usr/bin/env python3
"""
Enhanced API key test script for multiple AI providers with fallback testing.
"""

import requests
import json
import asyncio
from app.config import settings
from app.agents.base_agent import FallbackAgent


def test_openai_api_key():
    """Test if the OpenAI API key is valid and has credits."""
    print("🔍 Testing OpenAI API Key")
    print("=" * 50)

    api_key = settings.OPENAI_API_KEY

    if not api_key:
        print("❌ No OpenAI API key found in configuration")
        return False

    # Mask the key for security
    print(f"🔑 Testing key: [REDACTED]")

    # Test the API key with a simple request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Simple test payload
    test_payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 5
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=test_payload,
            timeout=10
        )

        if response.status_code == 200:
            print("✅ OpenAI API Key is valid and working!")
            return True
        elif response.status_code == 401:
            print("❌ OpenAI API Key is invalid or expired")
            print("   Error: Unauthorized")
            return False
        elif response.status_code == 429:
            print(
                "⚠️  OpenAI API Key is valid but you've exceeded quota or need billing setup")
            print("   Error: Rate limit or billing issue")
            return False
        else:
            print(
                f"❌ OpenAI API request failed with status: {response.status_code}")
            try:
                error_info = response.json()
                print(f"   Error details: {error_info}")
            except:
                print(f"   Error text: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error testing OpenAI API key: {e}")
        return False


def test_xai_api_key():
    """Test if the X.AI API key is valid."""
    print("\n🔍 Testing X.AI API Key")
    print("=" * 50)

    api_key = settings.XAI_API_KEY

    if not api_key or api_key == "your-xai-api-key-here":
        print("❌ No X.AI API key found in configuration")
        print("   Please add your X.AI API key to .env file")
        return False

    # Mask the key for security
    print(f"🔑 Testing key: [REDACTED]")

    # Test the API key with a simple request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Simple test payload for X.AI/Grok
    test_payload = {
        "model": "grok-beta",  # You may need to adjust this model name
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 5
    }

    try:
        # X.AI endpoint (adjust URL if needed)
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",  # Hypothetical endpoint
            headers=headers,
            json=test_payload,
            timeout=10
        )

        if response.status_code == 200:
            print("✅ X.AI API Key is valid and working!")
            return True
        elif response.status_code == 401:
            print("❌ X.AI API Key is invalid or expired")
            print("   Error: Unauthorized")
            return False
        elif response.status_code == 429:
            print("⚠️  X.AI API Key is valid but you've exceeded quota")
            print("   Error: Rate limit")
            return False
        elif response.status_code == 404:
            print("⚠️  X.AI endpoint not found - checking model/endpoint")
            print("   This might be normal if X.AI uses different endpoints")
            return False
        else:
            print(
                f"❌ X.AI API request failed with status: {response.status_code}")
            try:
                error_info = response.json()
                print(f"   Error details: {error_info}")
            except:
                print(f"   Error text: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error testing X.AI API key: {e}")
        return False


async def test_fallback_system():
    """Test the fallback system with a simple medical question."""
    print("\n🔍 Testing AI Fallback System")
    print("=" * 50)

    # Create a test agent
    system_prompt = "You are a helpful medical assistant. Respond briefly to test queries."

    try:
        agent = FallbackAgent(system_prompt)

        # Get status
        status = agent.get_status()
        available = agent.get_available_providers()

        print(f"🤖 Available providers: {available}")
        print(f"📊 Provider status: {status}")

        if not available:
            print("❌ No AI providers available for testing")
            return False

        # Test with a simple medical question
        test_question = "What is a normal heart rate for adults?"

        print(f"\n🧪 Testing with question: '{test_question}'")

        response = await agent.run_async(test_question)

        print("✅ Fallback system working!")
        print(f"📝 Response preview: {response[:100]}...")

        return True

    except Exception as e:
        print(f"❌ Fallback system test failed: {e}")
        return False


def show_setup_instructions():
    """Show setup instructions for X.AI."""
    print("\n🎯 X.AI Setup Instructions")
    print("=" * 50)

    print("To add X.AI support:")
    print("1. Sign up for X.AI API access")
    print("2. Get your API key from X.AI dashboard")
    print("3. Add to your .env file:")
    print("   XAI_API_KEY=your-actual-xai-key-here")
    print("4. Restart your application")

    print("\n📝 Note: X.AI endpoints and model names may differ")
    print("   You might need to adjust the model name in base_agent.py")
    print("   Common X.AI models might be: grok-beta, grok-1, etc.")


def show_alternatives():
    """Show alternative options for running the application."""
    print("\n🎯 Your Options:")
    print("=" * 50)

    print("\n1️⃣  **Add X.AI API Key (New Option!)**")
    print("   • Get X.AI API access")
    print("   • Add XAI_API_KEY to .env")
    print("   • Automatic fallback from OpenAI to X.AI")

    print("\n2️⃣  **Fix OpenAI Billing**")
    print("   • Go to: https://platform.openai.com/account/billing")
    print("   • Add a credit card")
    print("   • Get $5 free credits")

    print("\n3️⃣  **Use App Without AI (Works Great!)**")
    print("   • Full patient/visit management ✅")
    print("   • Database operations ✅")
    print("   • All CRUD endpoints ✅")
    print("   • No AI features ❌")

    print("\n4️⃣  **Try Anthropic Claude**")
    print("   • Add ANTHROPIC_API_KEY to .env")
    print("   • Third fallback option")


def main():
    """Main test function."""
    print("🏥 Medical Assistant - Enhanced API Key Validator")
    print("=" * 60)

    # Test OpenAI
    openai_status = test_openai_api_key()

    # Test X.AI
    xai_status = test_xai_api_key()

    # Test fallback system
    print("\n" + "=" * 60)
    fallback_status = asyncio.run(test_fallback_system())

    # Summary
    print("\n🎯 **SUMMARY**")
    print("=" * 60)
    print(f"OpenAI Status: {'✅' if openai_status else '❌'}")
    print(f"X.AI Status: {'✅' if xai_status else '❌'}")
    print(f"Fallback System: {'✅' if fallback_status else '❌'}")

    working_providers = sum([openai_status, xai_status])

    if working_providers > 0:
        print(
            f"\n🎉 Great! You have {working_providers} working AI provider(s)!")
        print("Your medical assistant is ready to use AI features.")

        if working_providers > 1:
            print("✨ Bonus: You have multiple providers - automatic fallback enabled!")
    else:
        print("\n⚠️  No AI providers are working")
        show_alternatives()
        show_setup_instructions()

    print(f"\n🚀 **To Enable All Features:**")
    print("1. Fix OpenAI billing OR add X.AI key")
    print("2. Restart your server")
    print("3. Test AI endpoints!")


if __name__ == "__main__":
    main()
