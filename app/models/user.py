"""
User model for authentication and authorization.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.database.base import Base


class UserRole(str, Enum):
    """User  roles for role-bases access control."""
    ADMIN = "admin"     # Full system access
    DOCTOR = "doctor"   # Full Patient Data access
    NURSE = "nurse"    # Limited Patient Data access
    RECEPTIONIST = "receptionist"  # Scheduling and basic info access


class User(Base):
    """
    User model for authentication and authorization.

    Attributes:
        id: Internal database ID.
        username: Unique username for login.
        email: User's email address.
        hashed_password: Hashed password for secure authentication.
        full_name: User's full name.
        role: Role of the user for access control.
        is_active: Indicates if the user account is active.
        is_verified: Indicates if the user's email is verified.
        created_at: Timestamp of user creation.
        updated_at: Timestamp of last update.
        last_login: Last login timestamp.
    """

    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Authentication fields
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Profile fields
    full_name = Column(String(100), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.DOCTOR)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


# Pydantic Schema for API


class UserBase(BaseModel):
    """ Base user schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = UserRole.DOCTOR


class UserCreate(UserBase):
    """ Schema for creating a user"""
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """ Ensure password meets the security requirements"""
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError(
                "Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError(
                "Password must contain at least one lowercase letter")
        return v


class UserUpdate(BaseModel):
    """ Schema for updating a user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class UserResponse(UserBase):
    """ Schema for user response"""
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """ Schema for user login """
    username: str
    password: str


class Token(BaseModel):
    """ Schema for JWT  token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """ Schema for JWT token data"""
    username: Optional[str] = None
    role: Optional[UserRole] = None
