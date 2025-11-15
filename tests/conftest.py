"""
Shared test fixture for medical assistant application tests.
"""

import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database.session import get_db
from app.main import app
from app.config import settings


# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"  # Use in-memory database


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """
    Create a test database engine.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    from app.models.user import User
    from app.models.patient import Patient
    from app.models.visit import Visit
    from app.database.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(loop_scope="session")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database dependency override."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Use ASGITransport to wrap the FastAPI app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(loop_scope="session")
async def admin_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """Create and return admin JWT for testing."""
    from app.models.user import User, UserRole
    from app.utils.auth import AuthService

    # Create admin user directly in database
    hashed_password = AuthService.get_password_hash("adminpass123")
    admin_user = User(
        username="admin",
        full_name="Admin User",
        email="admin@example.com",
        hashed_password=hashed_password,
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )

    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    # Login to get token
    login_data = {
        "username": "admin",
        "password": "adminpass123"
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture(loop_scope="session")
async def doctor_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """Create and return doctor JWT for testing."""
    from app.models.user import User, UserRole
    from app.utils.auth import AuthService

    # Create doctor user directly in database
    hashed_password = AuthService.get_password_hash("doctorpass123")
    doctor_user = User(
        username="doctor",
        full_name="Doctor User",
        email="doctor@example.com",
        hashed_password=hashed_password,
        role=UserRole.DOCTOR,
        is_active=True,
        is_verified=True
    )

    db_session.add(doctor_user)
    await db_session.commit()
    await db_session.refresh(doctor_user)

    # Login to get token
    login_data = {
        "username": "doctor",
        "password": "doctorpass123"
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    return response.json()["access_token"]
