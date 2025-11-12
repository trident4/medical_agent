"""
Authentication endpoints for the API.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
import logging

from app.database.session import get_db
from app.models.user import Token, UserLogin
from app.utils.auth import AuthService, ACCESS_TOKEN_EXPIRE_MINUTES
from app.services.user_services import UserService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=Token, summary="Login to get access token", description="Authenticate user and return JWT access token."
             )
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Login endpoint using OAuth2 password flow.

    Args:
        form_data (OAuth2PasswordRequestForm): Form data containing username and password
        db (AsyncSession): Database session
    Returns:
        Token: JWT access token

    Raise:
        HTTPException: If authentication fails

    """
    # Authenticate user
    user = await AuthService.authenticate_user(db, form_data.username, form_data.password)

    if not user:
        logger.warning("Failed login attempt for username: %s",
                       form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": user.username, "role": user.role.value}, expires_delta=access_token_expires)

    # Update the last login time
    user_service = UserService(db)
    await user_service.update_last_login(user_id=user.id)
    logger.info("User %s logged in successfully", user.username)

    return Token(access_token=access_token, token_type="bearer")


@router.post("/login/json", response_model=Token, summary="Login with JSON body to get access token", description="Authenticate user using JSON body and return JWT access token.")
async def login_json(user_login: UserLogin, db: AsyncSession = Depends(get_db)) -> Token:
    """
    Login endpoint using JSON body.
    Args:
        user_logon (UserLogin): User login data containing username and password
        db (AsyncSession): Database session
    Returns:
        Token: JWT access token
    Raise:
        HTTPException: If authentication fails
    """
    user = await AuthService.authenticate_user(db, user_login.username, user_login.password)
    if not user:
        logger.warning("Failed login attempt for username: %s",
                       user_login.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        {"sub": user.username, "role": user.role.value}, expires_delta=access_token_expires)

    # Update the last login time
    user_service = UserService(db)
    await user_service.update_last_login(user_id=user.id)
    logger.info("User %s logged in successfully", user.username)

    return Token(access_token=access_token, token_type="bearer")
