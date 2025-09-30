#!/usr/bin/env python3
"""
Test script to verify environment configuration is loading correctly.
"""

import os
from app.config import settings

print("🔍 Environment Configuration Test")
print("=" * 50)

# Check if .env file exists
env_file_path = ".env"
if os.path.exists(env_file_path):
    print(f"✅ .env file found at: {env_file_path}")
else:
    print(f"❌ .env file not found at: {env_file_path}")

print(f"\n📋 Configuration Values:")
print(f"APP_NAME: {settings.APP_NAME}")
print(f"DATABASE_URL: {settings.DATABASE_URL}")
print(f"API_V1_STR: {settings.API_V1_STR}")

# Check API keys (masked for security)
openai_key = settings.OPENAI_API_KEY
if openai_key:
    print(f"OPENAI_API_KEY: ✅ Set (length: {len(openai_key)})")
else:
    print("OPENAI_API_KEY: ❌ Not set or empty")

anthropic_key = settings.ANTHROPIC_API_KEY
if anthropic_key and anthropic_key != "your-anthropic-api-key":
    print(f"ANTHROPIC_API_KEY: ✅ Set (length: {len(anthropic_key)})")
else:
    print("ANTHROPIC_API_KEY: ❌ Not set or placeholder")

print(f"\n🧪 Testing OpenAI Client Creation:")
try:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    print("✅ OpenAI client created successfully")
except Exception as e:
    print(f"❌ OpenAI client creation failed: {e}")

print(f"\n🤖 Testing PydanticAI Agent Creation:")
try:
    from pydantic_ai import Agent

    # Test with a simple agent
    test_agent = Agent('openai:gpt-4o-mini',
                       system_prompt="You are a test assistant.")
    print("✅ PydanticAI agent created successfully")
except Exception as e:
    print(f"❌ PydanticAI agent creation failed: {e}")

print(f"\n🎯 Recommendations:")
if not openai_key:
    print("- Add OPENAI_API_KEY to .env file")
elif len(openai_key) < 20:
    print("- OPENAI_API_KEY appears to be too short - check if it's complete")
else:
    print("- Configuration looks good!")
