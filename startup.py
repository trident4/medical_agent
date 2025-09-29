#!/usr/bin/env python3
"""
Simple startup script for development.
"""

import os
import sys


def main():
    """Main startup function."""
    print("🏥 Medical Assistant API")
    print("=" * 50)

    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    ):
        print("⚠️  Warning: Virtual environment not detected")
        print("Please activate your virtual environment first:")
        print("source .venv/bin/activate")
        return

    print("✅ Virtual environment: Active")

    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found")
        print("Please copy .env.example to .env and configure:")
        print("cp .env.example .env")
        print()
        print("Required environment variables:")
        print("- DATABASE_URL (PostgreSQL connection string)")
        print("- OPENAI_API_KEY (for AI features)")
        print("- SECRET_KEY (for security)")
        return

    print("✅ Environment file: Found")

    # Show next steps
    print()
    print("🚀 Ready to start! Next steps:")
    print("1. Ensure PostgreSQL is running")
    print("2. Configure your .env file with proper values")
    print("3. Run: python run_dev.py")
    print()
    print("📚 API Documentation will be available at:")
    print("   http://localhost:8000/docs")
    print()
    print("🔗 Health Check:")
    print("   http://localhost:8000/health")


if __name__ == "__main__":
    main()
