"""
Application configuration settings.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator

import os
from dotenv import load_dotenv

# Only load .env file if DATABASE_URL is not already set
# This prevents Docker from loading local .env when environment variables
# are already provided via docker-compose
if not os.getenv("DATABASE_URL"):
    load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    # Application
    ENVIRONMENT: str = "development"
    APP_NAME: str = "Medical Assistant API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL")
    ADMIN_FULLNAME: str = os.getenv("ADMIN_FULLNAME")

    # Database - PostgreSQL (legacy, optional)
    POSTGRES_USER: str | None = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str | None = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST: str | None = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT: str | None = os.getenv("POSTGRES_PORT")
    POSTGRES_DB: str | None = os.getenv("POSTGRES_DB")
    
    # Database - MySQL (for PythonAnywhere)
    MYSQL_HOST: str | None = os.getenv("MYSQL_HOST")
    MYSQL_PORT: str | None = os.getenv("MYSQL_PORT")
    MYSQL_DATABASE: str | None = os.getenv("MYSQL_DATABASE")
    MYSQL_USER: str | None = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD: str | None = os.getenv("MYSQL_PASSWORD")
    
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info) -> str:
        if isinstance(v, str) and v:
            return v
        
        # Try MySQL first (for PythonAnywhere deployment)
        mysql_user = os.getenv("MYSQL_USER")
        mysql_password = os.getenv("MYSQL_PASSWORD")
        mysql_host = os.getenv("MYSQL_HOST")
        mysql_port = os.getenv("MYSQL_PORT")
        mysql_db = os.getenv("MYSQL_DATABASE")
        
        if all([mysql_user, mysql_password, mysql_host, mysql_port, mysql_db]):
            return f"mysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"
        
        # Fall back to PostgreSQL
        pg_user = os.getenv("POSTGRES_USER")
        pg_password = os.getenv("POSTGRES_PASSWORD")
        pg_host = os.getenv("POSTGRES_HOST")
        pg_port = os.getenv("POSTGRES_PORT")
        pg_db = os.getenv("POSTGRES_DB")
        
        if all([pg_user, pg_password, pg_host, pg_port, pg_db]):
            return f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
        
        raise ValueError("DATABASE_URL not set and unable to construct from components")
    
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL")

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
