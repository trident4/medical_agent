#!/usr/bin/env python3
"""
Improved database initialization script for the Medical Assistant API.
"""

import asyncio
import asyncpg
import os
import sys
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine
from app.database.base import Base
from app.config import settings


async def test_postgresql_available():
    """Test if PostgreSQL is available."""
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user=os.getenv("USER"),
            database="postgres"
        )
        await conn.close()
        return True
    except Exception:
        return False


async def create_database():
    """Create the database if it doesn't exist."""
    # Skip if using SQLite
    if settings.DATABASE_URL.startswith("sqlite"):
        print("✅ Using SQLite - database will be created automatically")
        return True

    # Check if PostgreSQL is available
    if not await test_postgresql_available():
        print("❌ PostgreSQL is not available. Please install and start PostgreSQL:")
        print("  brew install postgresql@15")
        print("  brew services start postgresql@15")
        return False

    # Parse the database URL
    parsed = urlparse(settings.DATABASE_URL)
    db_name = parsed.path[1:] if parsed.path else "doctors_assistant"

    print(f"Creating database: {db_name}")

    try:
        # Connect to postgres database
        conn = await asyncpg.connect(
            host=parsed.hostname or "localhost",
            port=parsed.port or 5432,
            user=parsed.username or os.getenv("USER"),
            password=parsed.password,
            database="postgres"
        )

        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )

        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✅ Database '{db_name}' created successfully!")
        else:
            print(f"✅ Database '{db_name}' already exists.")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ Error creating database: {e}")
        print(f"\nTry creating the database manually:")
        print(f"createdb {db_name}")
        return False


async def test_connection():
    """Test database connection."""
    print("\nTesting database connection...")

    try:
        # Prepare the connection URL
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

        engine = create_async_engine(db_url, echo=False)

        async with engine.connect() as conn:
            if db_url.startswith("postgresql+asyncpg://"):
                result = await conn.execute("SELECT version()")
                version = result.scalar()
                print(f"✅ PostgreSQL connection successful!")
                print(f"Version: {version}")
            else:
                result = await conn.execute("SELECT sqlite_version()")
                version = result.scalar()
                print(f"✅ SQLite connection successful!")
                print(f"Version: {version}")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def create_tables():
    """Create all database tables."""
    print("\nCreating database tables...")

    try:
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

        engine = create_async_engine(db_url, echo=True)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await engine.dispose()
        print("✅ Database tables created successfully!")
        return True

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "="*50)
    print("🎉 Database setup complete!")
    print("="*50)
    print("\n📋 Next steps:")
    print("1. Start the application:")
    print("   python -m uvicorn app.main_dev:app --reload")
    print("\n2. Or run the full application (requires OpenAI API key):")
    print("   python -m uvicorn app.main:app --reload")
    print("\n3. Access the API documentation:")
    print("   http://localhost:8000/docs")
    print("\n4. Test the health endpoint:")
    print("   curl http://localhost:8000/health")
    print("\n🔗 Useful commands:")
    print("   # Connect to database directly:")
    if settings.DATABASE_URL.startswith("postgresql"):
        parsed = urlparse(settings.DATABASE_URL)
        db_name = parsed.path[1:] if parsed.path else "doctors_assistant"
        print(f"   psql {db_name}")
    else:
        print("   sqlite3 ./test.db")
    print("\n   # View tables:")
    print("   \\dt (in psql) or .tables (in sqlite)")


async def main():
    """Main initialization function."""
    print("🏥 Medical Assistant Database Setup")
    print("="*40)

    # Check current configuration
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Debug mode: {settings.DEBUG}")

    success = True

    # Create database (if PostgreSQL)
    if not await create_database():
        success = False

    # Test connection
    if not await test_connection():
        success = False

    # Create tables
    if success and not await create_tables():
        success = False

    if success:
        print_next_steps()
    else:
        print("\n❌ Setup incomplete. Please check the errors above.")
        print("\n💡 Quick fixes:")
        print("1. For PostgreSQL issues:")
        print("   brew install postgresql@15")
        print("   brew services start postgresql@15")
        print("   createdb doctors_assistant")
        print("\n2. For testing, you can use SQLite instead:")
        print("   Edit .env and set: DATABASE_URL=sqlite:///./test.db")


if __name__ == "__main__":
    asyncio.run(main())
