#!/usr/bin/env python3
"""
Debug X.AI environment variable setup.
"""

from app.config import settings
import os
import sys
sys.path.append('/Users/chetan/Personal/HobbyProjects/doctors-assistant')


def debug_xai_env():
    """Debug X.AI environment setup."""
    print("🔍 X.AI Environment Debug")
    print("=" * 40)

    # Check settings

    # Check environment variable
    env_key = os.environ.get('XAI_API_KEY')

    # Set it manually and test
    if settings.XAI_API_KEY:
        os.environ['XAI_API_KEY'] = settings.XAI_API_KEY
        print("✅ Set XAI_API_KEY in environment")

        # Test again
        env_key_after = os.environ.get('XAI_API_KEY')

    # Show all X.AI related env vars
    print("\n🔧 All XAI environment variables:")
    for key, value in os.environ.items():
        if 'XAI' in key.upper() or 'GROK' in key.upper():
            masked = value[:10] + "..." + \
                value[-4:] if len(value) > 14 else value


if __name__ == "__main__":
    debug_xai_env()
