"""
User management endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database.session import get_db
from app.models.user import User, UserCreate, UserUpdate, UserResponse, UserRole
from app.services.user_services import UserService
from app.utils.auth import get_current_active_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create a new user account", description="Create a new user account (Admin only)")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> UserResponse:
    """
    Create a new user account

    only Admins can create new user accounts.
    Args:
        user_data (UserCreate): Data for creating a new user
        db (AsyncSession): Database session
        current_user (User): Currently authenticated user

    Returns:
        Created user data (UserResponse)

    Raise:
        HTTPException: If user with the same email already exists
    """
    # check permission
    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admins can create new user accounts"
        )
    user_service = UserService(db)
    created_user = await user_service.create_user(user_data)
    logger.info("User created successfully: %s", created_user.email)
    return created_user


@router.get("/me", response_model=UserResponse, summary="Get current user", description="Get information about the currently authenticated user")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """
     Get current user's information.

    Args:
        current_user (User): Currently authenticated user  
    Returns:
        UserResponse: Current user's data
    """
    return current_user


@router.get("/", response_model=List[UserResponse], summary="List all users", description="Retrieve a list of all users (Admin only)")
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of records to return"),
    role: Optional[UserRole] = Query(
        None, description="Filter users by role"),
    is_active: Optional[bool] = Query(
        None, description="Filter users by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role([UserRole.ADMIN, UserRole.DOCTOR]))
) -> List[UserResponse]:
    """
    List all users in the system.

    Only Admins and Doctors can access the list of users.
    Args:
        skip (int): Number of records to skip for pagination
        limit (int): Maximum number of records to return
        db (AsyncSession): Database session
        current_user (User): Currently authenticated user

    Returns:
        List[UserResponse]: List of users
    """
    # check permission
    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admins and Doctors can access the list of users"
        )
    user_service = UserService(db)
    users = await user_service.get_users(skip=skip, limit=limit, role=role, is_active=is_active)
    return users


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID", description="Retrieve user information by user ID (Admin and Doctors only)")
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.DOCTOR))
) -> UserResponse:
    """
    Get the user information by user ID.
    Only Admins and Doctors can access user information by ID.
    Args:
        user_id (int): ID of the user to retrieve
        db (AsyncSession): Database session
        current_user (User): Currently authenticated user

    Returns:
        UserResponse: User data
    """
    # check permission
    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctors can only access their own user information"
        )
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse, summary="Update user information", description="Update user information by user ID (Admin only)")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role([UserRole.ADMIN, UserRole.DOCTOR]))
) -> UserResponse:
    """
    Update user information by user ID.

    Only Admins can update user information.
    Args:
        user_id (int): ID of the user to update
        user_data (UserUpdate): Data for updating the user
        db (AsyncSession): Database session
        current_user (User): Currently authenticated user
    Returns:
        Updated user data (UserResponse)
    """
    # check permission
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admins can update user information"
        )
    user_service = UserService(db)
    updated_user = await user_service.update_user(user_id, user_data)
    logger.info("User updated successfully: %s", updated_user.email)
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user", description="Delete a user by user ID (Admin only)")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> None:
    """
    Delete a user by user ID.

    Only Admins can delete users.
    Args:
        user_id (int): ID of the user to delete
        db (AsyncSession): Database session
        current_user (User): Currently authenticated user

    Returns:
        None
    """
    # check permission
    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admins can delete users"
        )
    user_service = UserService(db)
    await user_service.delete_user(user_id)
    logger.info("User with ID %s deleted successfully", user_id)
    return None
