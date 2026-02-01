"""Application configuration settings."""
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Aerospace Parts Material Management API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Database - Sync (for Alembic)
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/aerospace_parts"
    
    # Database - Async (for application)
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Convert sync URL to async URL for asyncpg."""
        return self.DATABASE_URL.replace(
            "postgresql://", "postgresql+asyncpg://"
        ).replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://"
        )
    
    # JWT Settings
    SECRET_KEY: str = "8fb66b1765af8de902c19956bf5433aa90fbf6747eda643d06ce30e2f4224c28"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 90  # 90 minutes token expiry
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS - Origins allowed to call the API (browser enforces this)
    # In production set env: ALLOWED_ORIGINS=https://ads.pickupbiz.com (or comma-separated list)
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5055",
        "http://127.0.0.1:5055",
        "https://ads.pickupbiz.com",  # Production frontend
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str]]) -> Union[str, List[str]]:
        """Allow ALLOWED_ORIGINS from env as comma-separated string."""
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Email Notifications (disabled by default)
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@aerospace-materials.com"
    FROM_NAME: str = "Aerospace Materials System"
    
    # Workflow Thresholds (USD)
    PO_AUTO_APPROVE_THRESHOLD: float = 5000.0
    PO_STANDARD_APPROVAL_THRESHOLD: float = 25000.0
    PO_HIGH_VALUE_THRESHOLD: float = 100000.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
