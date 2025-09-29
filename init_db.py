#!/usr/bin/env python3
"""
Database initialization script for the Medical Assistant API.
"""

import asyncio
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from app.database.base import Base
from app.config import settings


async def create_database():
    """Create the database if it doesn't exist."""
    # Parse the database URL to get connection info
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    # Extract database name
    db_name = db_url.split("/")[-1]
    base_url = "/".join(db_url.split("/")[:-1])

    print(f"Creating database: {db_name}")

    try:
        # Connect to postgres database to create our database
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="",  # Update with your password
            database="postgres"
        )

        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )

        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Database '{db_name}' created successfully!")
        else:
            print(f"Database '{db_name}' already exists.")

        await conn.close()

    except Exception as e:
        print(f"Error creating database: {e}")
        print("Please ensure PostgreSQL is running and create the database manually:")
        print(f"CREATE DATABASE {db_name};")


async def create_tables():
    """Create all database tables."""
    print("Creating database tables...")

    try:
        engine = create_async_engine(
            settings.DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://"),
            echo=True
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await engine.dispose()
        print("Tables created successfully!")

    except Exception as e:
        print(f"Error creating tables: {e}")


async def main():
    """Main initialization function."""
    print("Initializing Medical Assistant Database...")

    # Create database
    await create_database()

    # Create tables
    await create_tables()

    print("\nDatabase initialization complete!")
    print("You can now start the application with: python run_dev.py")


if __name__ == "__main__":
    asyncio.run(main())
