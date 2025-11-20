# Docker Setup Challenges & Solutions

This document outlines the challenges faced while setting up the Docker environment for the Doctors Assistant application and the solutions implemented to resolve them.

## 1. Database Migrations Failure

### Challenge
When running `docker-compose up --build`, the application failed during the migration stage (`alembic upgrade head`).
- **Root Cause:** The existing Alembic migration files contained `ALTER TABLE` statements but lacked the initial `CREATE TABLE` statements. This worked locally where tables might have been created manually or via `Base.metadata.create_all`, but failed on a fresh Docker database.

### Solution
- **Created Initial Migration:** Generated a new migration file `alembic/versions/0001_initial_schema.py` that explicitly creates all tables (`users`, `patients`, `visits`) with their complete schema (indexes, constraints, JSONB types).
- **Reordered Chain:** Updated the `down_revision` of the oldest existing migration to point to this new initial schema, ensuring a continuous and valid migration history.

## 2. Database Connection to Localhost

### Challenge
The `web` container was constantly restarting, and logs showed it was trying to connect to `localhost:5432` instead of the `db` service.
- **Root Cause:** The `docker-compose.yml` file passed `DATABASE_URL=${DATABASE_URL}`. Docker Compose was substituting this variable with the value from the host machine's `.env` file (which pointed to `localhost`), overriding the `.env_docker` file intended for the container.

### Solution
- **Environment Variable Precedence:** Removed `DATABASE_URL` from the `environment` section of `docker-compose.yml`. This forced the container to use the values defined in `env_file` (`.env_docker`).
- **Conditional Config Loading:** Updated `app/config.py` to only load the local `.env` file if `DATABASE_URL` is not already set in the environment.

## 3. Hardcoded vs. Dynamic Configuration

### Challenge
The application relied on a pre-constructed `DATABASE_URL` string. Changing the database user or password in `docker-compose.yml` (e.g., via environment variables) didn't automatically update the connection string used by the application, leading to authentication failures if credentials were changed.

### Solution
- **Dynamic URL Construction:** Refactored `app/config.py` to accept individual connection parameters (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`).
- **Validator:** Added a Pydantic validator to dynamically construct the `DATABASE_URL` from these parameters if the full URL isn't explicitly provided.
- **Docker Compose Update:** Updated `docker-compose.yml` to pass these individual parameters to the `web` service, ensuring the application always connects with the credentials defined in the Compose file.

## 4. Missing Admin User

### Challenge
After successfully starting the application in Docker with a fresh database, there was no admin user available to log in, as the local database's data wasn't copied over.

### Solution
- **Automated Script:** Identified the existing `scripts/create_admin.py` script which handles secure admin creation.
- **Entrypoint Integration:** Modified `docker-entrypoint.sh` to execute `python scripts/create_admin.py` after running migrations and before starting the application.
- **Result:** The admin user is now automatically created on container startup if it doesn't exist, using credentials from environment variables.

## Summary of Best Practices Implemented
1.  **Explicit Schema Definition:** Always ensure migrations cover the full schema creation from scratch.
2.  **Environment Isolation:** Prevent host environment variables from accidentally overriding container configuration.
3.  **Dynamic Configuration:** Construct connection strings from individual components to maintain consistency across services.
4.  **Automated Initialization:** Use entrypoint scripts to handle idempotent initialization tasks like migrations and default user creation.
