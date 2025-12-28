"""Application configuration."""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings."""

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "lelivre_gold"
    postgres_user: str = "lelivre"
    postgres_password: str  # No default - MUST be in .env

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str  # No default - MUST be in .env
    neo4j_database: str = "neo4j"

    # OpenAI
    openai_api_key: str

    # API
    api_title: str = "Le Livre API"
    api_version: str = "0.1.0"

    # CORS origins - configurable via environment variable
    # In .env: CORS_ORIGINS=http://localhost:5174,http://localhost:5173
    # In production .env: CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
    cors_origins: list[str] = Field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:5174,http://localhost:5173,http://localhost:3000").split(",")
    )

    # JWT Configuration
    jwt_secret_key: str  # No default - MUST be in .env with secure value
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Security
    environment: str = "development"  # Change to "production" in prod

    class Config:
        # Look for .env in project root (two levels up from this file)
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from .env


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
