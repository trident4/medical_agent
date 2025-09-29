# Medical Assistant for Doctors

A comprehensive medical agent system that assists doctors with patient visit data analysis, summarization, and intelligent Q&A capabilities.

## Features

- **Patient Visit Summarization**: Automatically generate concise summaries of patient visits
- **Intelligent Q&A**: Ask questions about patient data and get contextual answers
- **Secure Data Handling**: HIPAA-compliant data processing and storage
- **RESTful API**: Easy integration with existing medical systems
- **Real-time Processing**: Fast response times for clinical workflows

## Technology Stack

- **Backend**: FastAPI (Python)
- **AI Framework**: PydanticAI
- **Database**: SQLAlchemy with PostgreSQL
- **Data Validation**: Pydantic
- **Server**: Uvicorn (ASGI)
- **Testing**: Pytest
- **Documentation**: FastAPI automatic docs

## Quick Start

1. **Installation**

   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Database Setup**

   ```bash
   python -m app.database.init_db
   ```

4. **Run the Application**

   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Application configuration
├── api/                 # API route handlers
│   ├── __init__.py
│   ├── patients.py      # Patient-related endpoints
│   ├── visits.py        # Visit-related endpoints
│   └── agents.py        # AI agent endpoints
├── agents/              # PydanticAI agents
│   ├── __init__.py
│   ├── summarizer.py    # Visit summarization agent
│   └── qa_agent.py      # Question-answering agent
├── models/              # Data models
│   ├── __init__.py
│   ├── patient.py       # Patient data models
│   ├── visit.py         # Visit data models
│   └── schemas.py       # API request/response schemas
├── services/            # Business logic
│   ├── __init__.py
│   ├── patient_service.py
│   └── visit_service.py
└── database/            # Database configuration
    ├── __init__.py
    ├── base.py          # Database base configuration
    └── session.py       # Database session management
```

## API Endpoints

### Patient Management

- `GET /api/v1/patients/` - List all patients
- `POST /api/v1/patients/` - Create new patient
- `GET /api/v1/patients/{patient_id}` - Get patient details
- `PUT /api/v1/patients/{patient_id}` - Update patient
- `DELETE /api/v1/patients/{patient_id}` - Delete patient

### Visit Management

- `GET /api/v1/visits/` - List visits
- `POST /api/v1/visits/` - Create new visit
- `GET /api/v1/visits/{visit_id}` - Get visit details
- `PUT /api/v1/visits/{visit_id}` - Update visit

### AI Agent Services

- `POST /api/v1/agents/summarize` - Generate visit summary
- `POST /api/v1/agents/ask` - Ask questions about patient data

## Security & Compliance

This system is designed with healthcare data security in mind:

- **Data Encryption**: All sensitive data encrypted at rest and in transit
- **Access Control**: Role-based access control (RBAC)
- **Audit Logging**: Comprehensive audit trails
- **HIPAA Compliance**: Follows HIPAA guidelines for patient data handling

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
black app/
flake8 app/
mypy app/
```

### Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the repository.
