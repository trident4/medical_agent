"""
Script to create an admin user for Doctors Assistant application.

Usage:
    python scripts/create_admin.py 

Security Notes:
    - Password is hashed using bcrypt before storing in the database.
    - Admin creation is logged for HIPAA audit trail compliance.
    - Default credentials should be changed immediately after first login.
    - Run this script only once during initial setup.

HIPAA Compliance:
    - Secure password hashing with salt
    - Audit logging for user creation events
    - No sensitive data exposure in logs
"""
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Configure logging for HIPAA compliance
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CRITICAL: Add parent directory to sys.path BEFORE importing app modules
# This must remain above all app imports to prevent ModuleNotFoundError
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import SQLAlchemy modules


async def create_admin_user() -> None:
    """
    Create initial admin user with secure password hashing.

    Performs validation to prevent duplicate admin accounts and ensures
    HIPAA compliance through secure password handling and audit logging.

    Raises:
        Exception: If database operations fail or admin already exists
    """
    # Import app modules inside function to prevent isort reorganization
    from app.config import settings
    from app.models.user import User, UserRole
    from app.utils.auth import AuthService

    try:
        # Validate configuration
        if not settings.ADMIN_USERNAME or not settings.ADMIN_PASSWORD:
            raise ValueError(
                "ADMIN_USERNAME and ADMIN_PASSWORD must be set in config")

        # Create async engine with appropriate driver (matches session.py)
        database_url = settings.DATABASE_URL
        
        # Handle driver-specific URL schemes
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        elif database_url.startswith("mysql://"):
            database_url = database_url.replace("mysql://", "mysql+aiomysql://")
        
        engine = create_async_engine(
            database_url,
            echo=settings.DEBUG,
            pool_pre_ping=True,  # Verify connections before use
            pool_size=5,         # Connection pool size
            max_overflow=10      # Max overflow connections
        )

        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session() as session:
            # Check if admin already exists (prevent duplicates)
            result = await session.execute(
                select(User).where(User.username == settings.ADMIN_USERNAME)
            )
            existing_admin: Optional[User] = result.scalar_one_or_none()

            if existing_admin:
                logger.warning(
                    "Admin user '%s' already exists",
                    settings.ADMIN_USERNAME,
                    extra={
                        "event": "admin_creation_attempted",
                        "existing_user_id": existing_admin.id
                    }
                )
                print(
                    f"❌ Admin user '{settings.ADMIN_USERNAME}' already exists!")
                return

            # Create new admin user with secure password hashing
            logger.info(
                "Creating initial admin user",
                extra={"event": "admin_creation_started"}
            )

            hashed_password = AuthService.get_password_hash(
                settings.ADMIN_PASSWORD)

            new_admin = User(
                username=settings.ADMIN_USERNAME,
                full_name=settings.ADMIN_FULLNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=hashed_password,
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )

            session.add(new_admin)
            await session.commit()
            await session.refresh(new_admin)

            logger.info(
                "Admin user '%s' created successfully",
                settings.ADMIN_USERNAME,
                extra={
                    "event": "admin_creation_successful",
                    "user_id": new_admin.id,
                    "username": new_admin.username,
                    "role": new_admin.role.value
                }
            )

            print(
                f"✅ Admin user '{settings.ADMIN_USERNAME}' created successfully!")
            print(f"\n📋 Login credentials:")
            print(f"\n⚠️  IMPORTANT: Change the password immediately after first login!")
            print(f"   Login at: http://localhost:8000/docs")

    except Exception as e:
        logger.error(
            "Failed to create admin user: %s",
            e,
            extra={
                "event": "admin_creation_failed",
                "error": str(e)
            }
        )
        print(f"❌ Failed to create admin user: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(create_admin_user())
