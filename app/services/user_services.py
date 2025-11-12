"""
Service layer for user-related operations.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from datetime import datetime
import logging


from app.models.user import (
    User,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserRole
)

from app.utils.auth import AuthService

logger = logging.getLogger(__name__)


class UserService:
    """ Services class for user operation"""

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.

        Args:
            db (AsyncSession): Database session
        """
        self.db = db

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Create a new user.

        Args:
            user_data (UserCreate): Data for creating a new user

        Returns:
        Created user data (UserResponse)

        Raise:
            HTTPException: If user with the same email already exists
        """

        logger.info("Creating user : %s", user_data.email)

        # Check if user with the same email already exists
        existing_user = await self.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with username {user_data.username} already exists"
            )

        # Check if email already exists
        existing_email = await self.get_user_by_email(user_data.email)

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {user_data.email} already exists"
            )

        # Hashed password
        hashed_password = AuthService.get_password_hash(user_data.password)

        # Create user
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            hashed_password=hashed_password,
        )
        self.db.add(db_user)

        try:
            await self.db.commit()
            await self.db.refresh(db_user)
            logger.info("User created with ID: %s", db_user.id)
            return UserResponse.model_validate(db_user)
        except Exception as e:
            await self.db.rollback()
            logger.error("Error creating user: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating user"
            ) from e

    async def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """
        Get user by username

        Args:
            username (str): Username of the user

        Returns:
            User if found, None otherwise
        """
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        user = result.scalars_one_or_none()

        if user:
            return UserResponse.model_validate(user)
        return None

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """
        Get user by email

        Args:
            email (str): Email of the user

        Returns:
            User if found, None otherwise
        """
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        user = result.scalars_one_or_none()

        if user:
            return UserResponse.model_validate(user)
        return None

    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """
        Get user by ID
        Args:
            user_id (int): ID of the user
        Returns:
            User if found, None otherwise
        """
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if user:
            return UserResponse.model_validate(user)
        return None

    async def get_users(self, skip: int = 0, limit: int = 100, role: Optional[str] = None, is_active: Optional[bool] = str) -> List[UserResponse]:
        """
        Get the list of the users 

        Args:
            skip (int): Number of users to skip
            limit (int): Maximum number of users to return
            role (Optional[str]): Filter by user role
            is_active (Optional[bool]): Filter by active status
        Returns:
            List of users
        """
        query = select(User)

        # Apply filters
        if role:
            query = query.where(User.role == role)
        if is_active is not None:
            query = query.where(User.is_active == is_active)

        # Apply pagination
        query = query.offset(skip).limit(
            limit).order_by(User.created_at.desc())

        result = await self.db.execute(query)
        users = result.scalars().all()

        return [UserResponse.model_validate(user) for user in users]

    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        """
        Update the user information
            Args:
                user_id (int): ID of the user to update
                user_data (UserUpdate): Data for updating the user
            Returns:
                Updated user data

            Raise:
                HTTPException: If user not found
        """
        logger.info("Updating user with ID: %s", user_id)
        existing_user = await self.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )

        # Check email uniqueness if updating email
        if user_data.email and user_data.email != existing_user.email:
            email_user = await self.get_user_by_email(user_data.email)
            if email_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email {user_data.email} is already in use"
                )

        # Update fields
        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(existing_user, key, value)

        try:
            await self.db.commit()
            await self.db.refresh(existing_user)
            logger.info("User with ID %s updated successfully", user_id)
            return UserResponse.model_validate(existing_user)
        except Exception as e:
            await self.db.rollback()
            logger.error("Error updating user: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating user"
            ) from e

    async def delete_user(self, user_id: int) -> bool:
        """
        Delete a user by ID.
        Args:
            user_id (int): ID of the user to delete
        Returns:
            True if deletion was successful
        Raise:
            HTTPException: If user not found
        """
        logger.info("Deleting user with ID: %s", user_id)
        existing_user = await self.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        existing_user.is_active = False  # Soft delete
        try:
            await self.db.commit()
            logger.info("User with ID %s deleted successfully", user_id)
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error("Error deleting user: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting user"
            ) from e

    async def update_last_login(self, user_id: int) -> bool:
        """
        Update the last login timestamp for a user.

        Args:
            user_id (int): ID of the user to
        Returns:
            None
        """
        logger.info("Updating last login for user ID: %s", user_id)
        existing_user = await self.get_user_by_id(user_id)
        if not existing_user:
            logger.warning("User with ID %s not found", user_id)
            return
        existing_user.last_login = datetime.utcnow()
        try:
            await self.db.commit()
            logger.info(
                "Last login for user ID %s updated successfully", user_id)
            return True
        except Exception as e:
            logger.error("Error updating last login: %s", e)
            await self.db.rollback()
            return False
