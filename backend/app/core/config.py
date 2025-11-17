"""
Application configuration
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Import settings
    CSV_DATA_DIR: str = ".."  # CSV files are in project root
    IMPORT_BATCH_SIZE: int = 10000
    IMPORT_WORKERS: int = 8
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

