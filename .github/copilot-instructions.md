<!-- Medical Assistant Project Instructions -->

This is a medical agent project designed to assist doctors with:

- Summarizing patient visit data
- Answering questions about patient information
- Using PydanticAI for intelligent processing
- FastAPI for REST API endpoints

## Technology Stack

- Python 3.9+
- FastAPI for API framework
- PydanticAI for AI agent functionality
- SQLAlchemy for database operations
- Pydantic for data validation
- Uvicorn for ASGI server

## Project Structure

- `app/` - Main application code
- `app/models/` - Pydantic models and database schemas
- `app/api/` - FastAPI route handlers
- `app/agents/` - PydanticAI agents
- `app/services/` - Business logic
- `app/database/` - Database configuration
- `tests/` - Test files
- `docs/` - Documentation

## Development Guidelines

- Follow HIPAA compliance for medical data
- Use type hints throughout
- Implement proper error handling
- Add comprehensive logging
- Include unit and integration tests
