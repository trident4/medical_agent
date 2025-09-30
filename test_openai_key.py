#!/usr/bin/env python3
"""
Test script to check OpenAI API key validity and suggest alternatives.
"""

import requests
import json
from app.config import settings


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
            print("✅ API Key is valid and working!")
            return True
        elif response.status_code == 401:
            print("❌ API Key is invalid or expired")
            print("   Error: Unauthorized")
            return False
        elif response.status_code == 429:
            print("⚠️  API Key is valid but you've exceeded quota or need billing setup")
            print("   Error: Rate limit or billing issue")
            return False
        else:
            print(f"❌ API request failed with status: {response.status_code}")
            try:
                error_info = response.json()
                print(f"   Error details: {error_info}")
            except:
                print(f"   Error text: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error testing API key: {e}")
        return False


def show_alternatives():
    """Show alternative options for running the application."""
    print("\n🎯 Your Options:")
    print("=" * 50)

    print("\n1️⃣  **Add Payment Method to OpenAI (Recommended)**")
    print("   • Go to: https://platform.openai.com/account/billing")
    print("   • Add a credit card (required)")
    print("   • Get $5 free credits (lots of testing)")
    print("   • Very cheap: ~$0.15 per 1M tokens for GPT-4o-mini")

    print("\n2️⃣  **Use App Without AI (Works Great!)**")
    print("   • Full patient/visit management ✅")
    print("   • Database operations ✅")
    print("   • All CRUD endpoints ✅")
    print("   • No AI features ❌")

    print("\n3️⃣  **Try Local AI (Advanced)**")
    print("   • Use Ollama with local models")
    print("   • Completely free but requires setup")
    print("   • Models like llama2, codellama")

    print("\n4️⃣  **Use Anthropic Claude (Alternative)**")
    print("   • Claude has different pricing")
    print("   • May have free tier options")
    print("   • Update ANTHROPIC_API_KEY in .env")


def main():
    """Main test function."""
    print("🏥 Medical Assistant - API Key Validator")
    print("=" * 60)

    # Test OpenAI key
    is_valid = test_openai_api_key()

    if not is_valid:
        show_alternatives()

        print(f"\n💡 **Quick Fix for Testing:**")
        print("=" * 50)
        print("Your app works perfectly without AI! Try these endpoints:")
        print("• http://localhost:8000/docs")
        print("• GET /api/v1/patients")
        print("• POST /api/v1/patients")
        print("• GET /api/v1/visits")
        print("• POST /api/v1/visits")

        print(f"\n🚀 **To Enable AI Features:**")
        print("1. Go to OpenAI billing page")
        print("2. Add payment method")
        print("3. Restart your server")
        print("4. AI endpoints will work!")
    else:
        print(f"\n🎉 Great! Your OpenAI API key is working!")
        print("All AI features should be available.")


if __name__ == "__main__":
    main()
