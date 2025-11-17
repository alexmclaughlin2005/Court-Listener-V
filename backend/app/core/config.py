"""
Application configuration
"""
from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import field_validator


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
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

