"""
Application configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_VERSION: str = "v1"

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # Database (Optional - only needed for Alembic migrations or direct SQL queries)
    DATABASE_URL: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # CORS
    # Default origins include localhost and Vercel production domain
    # Can be overridden via environment variable (comma-separated string)
    # Example: CORS_ORIGINS=http://localhost:3000,https://micro-salz.vercel.app
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:3001,http://localhost:5173,https://gallery-english.vercel.app"
    )

    # Frontend URL (for password reset redirects)
    # Can be overridden via environment variable
    FRONTEND_URL: str = "http://localhost:3000"

    # File Storage
    SUPABASE_STORAGE_BUCKET: str = "artworks"
    MAX_FILE_SIZE: int = 10485760  # 10MB

    # Image Processing Settings
    IMAGE_THUMBNAIL_SIZE: int = 300  # Thumbnail max dimension (width or height)
    IMAGE_MEDIUM_SIZE: int = 1200  # Medium size max dimension
    IMAGE_LARGE_SIZE: int = 2400  # Large size max dimension
    IMAGE_QUALITY_JPEG: int = 85  # JPEG quality (1-100)
    IMAGE_QUALITY_WEBP: int = 85  # WebP quality (1-100)
    IMAGE_OPTIMIZE: bool = True  # Enable image optimization

    # External APIs
    YAMATO_API_KEY: str = ""
    YAMATO_API_URL: str = ""
    PAYMENT_GATEWAY_KEY: str = ""

    # AI/ML Settings
    ML_MODEL_PATH: str = "./app/ml/models"
    ENABLE_GPU: bool = False
    BATCH_SIZE: int = 32

    # Monitoring
    SENTRY_DSN: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
