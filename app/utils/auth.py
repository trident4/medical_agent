"""
Authentication and authorization utilities

"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.user import User, TokenData, UserRole
from app.database.session import get_db
from app.config import settings


logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 schema for token authentication
oauth2_schema = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# JWT settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES  # 1 hour


class AuthService:
    """ Service for handling authentication and authorization """

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """ Verify a plain password against the hashed password  """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """ Hash a plain password """
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """ Create a JWT access token """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """ Retrieve a user by username"""
        query = select(User).where(User.username == username)
        result = await db.execute(query)
        return result.scalars_one_or_none()

    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """ Authenticate user credentials

            Args:
                db (AsyncSession): Database session
                username (str): Username
                password (str): Plain password

            Returns:
                Optional[User]: Authenticated user or None
        """
        user = await AuthService.get_user_by_username(db, username)
        if not user:
            logger.warning(
                "Authentication failed: User '%s' not found", username)
            return None
        if not user.is_active:
            logger.warning(
                "Authentication failed: User '%s' is inactive", username)
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            logger.warning(
                "Authentication failed: Incorrect password for user '%s'", username)
            return None
        return user


async def get_current_user(
        token: str = Depends(oauth2_schema),
        db: AsyncSession = Depends(get_db)
) -> User:
    """ Get the current authenticated user from the JWT token

        Args:
            token (str): JWT token
            db (AsyncSession): Database session
        Returns:
            User: Authenticated user

    """
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            return credential_exception

        token_data = TokenData(
            username=username, role=UserRole(payload.get("role")))
    except JWTError as e:
        logger.error("JWT decoding error: %s", str(e))
        raise credential_exception

    user = await AuthService.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credential_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (additional check).

    Args:
        current_user: Current user from token

    Returns:
        Current user if active

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Dependency to check if user has required role.

    Usage:
        @router.get("/admin")
        async def admin_only(user: User = Depends(require_role(UserRole.ADMIN))):
            pass

    Args:
        allowed_roles: Roles that are allowed access

    Returns:
        Dependency function
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                "Access denied: User '%s' with role '%s' attempted to access resource requiring roles: %s",
                current_user.username,
                current_user.role,
                allowed_roles
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join([r.value for r in allowed_roles])}"
            )
        return current_user

    return role_checker
