#!/usr/bin/env python3
"""
Simple test of X.AI grok-3 integration.
"""

from app.agents.base_agent import FallbackAgent
import asyncio
import sys
sys.path.append('/Users/chetan/Personal/HobbyProjects/doctors-assistant')


async def test_xai_grok3():
    """Test X.AI with grok-3 model directly."""
    print("🤖 Testing X.AI Grok-3 Integration")
    print("=" * 50)

    # Create a simple agent
    agent = FallbackAgent("You are a helpful medical assistant. Be concise.")

    # Check status
    status = agent.get_status()
    available = agent.get_available_providers()

    print(f"📊 Available providers: {available}")
    print(f"🔧 Provider status: {status}")

    if 'xai' not in available:
        print("❌ X.AI not available. Check your XAI_API_KEY in .env")
        return False

    # Test a simple medical question
    test_question = "What is a normal heart rate range for adults?"

    print(f"\n🧪 Testing question: '{test_question}'")

    try:
        response = await agent.run_async(test_question)
        print("✅ X.AI response received!")
        print(f"📝 Response: {response[:200]}...")

        if len(response) > 10:  # Reasonable response length
            print("🎉 X.AI Grok-3 is working properly!")
            return True
        else:
            print("⚠️ Response too short, might be an issue")
            return False

    except Exception as e:
        print(f"❌ X.AI test failed: {e}")
        return False


async def main():
    """Main test function."""
    success = await test_xai_grok3()

    if success:
        print("\n🎯 Ready for Production!")
        print("✅ X.AI Grok-3 fallback is working")
        print("✅ Your medical assistant now has:")
        print("   1. OpenAI (when billing fixed)")
        print("   2. X.AI Grok-3 (working now!)")
        print("   3. Anthropic (if configured)")
    else:
        print("\n⚠️ X.AI needs attention")
        print("🔧 Check your XAI_API_KEY and try again")


if __name__ == "__main__":
    asyncio.run(main())
