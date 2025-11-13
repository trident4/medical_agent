"""
Application configuration settings.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator

import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    # Application
    ENVIRONMENT: str = "development"
    APP_NAME: str = "Medical Assistant API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "password")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_FULLNAME: str = os.getenv("ADMIN_FULLNAME", "Admin User")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    # AI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    XAI_API_KEY: str = os.getenv("XAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000", "http://localhost:8080"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
