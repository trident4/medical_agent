#!/bin/bash
# Docker entrypoint script for database migrations and app startup
# HIPAA Compliance: Ensures schema is migrated securely before app runs

set -e  # Exit on any error

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Create initial admin user
python scripts/create_admin.py

# Execute the main command (Uvicorn)
echo "Starting the application..."
exec "$@"