#!/usr/bin/env python3
"""Debug script to check DATABASE_URL"""
import os
import sys

print("=" * 50)
print("DATABASE_URL DEBUG")
print("=" * 50)
print(f"DATABASE_URL from os.getenv: {os.getenv('DATABASE_URL')}")
print(f"DATABASE_URL from os.environ.get: {os.environ.get('DATABASE_URL')}")

# Try importing config
try:
    from app.config import settings
    print(f"DATABASE_URL from settings: {settings.DATABASE_URL}")
except Exception as e:
    print(f"Error importing settings: {e}")
    sys.exit(1)

print("=" * 50)
