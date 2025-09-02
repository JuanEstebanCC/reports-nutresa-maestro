from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import os
import json

class Settings(BaseSettings):
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 21
    DATABASE_URL: str = "mysql://root:password@localhost:3306/database_name"
    
    # Subdomains configuration
    SUBDOMAINS_FILE: str = "static/subdomains.json"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Application settings
    DEBUG: bool = False
    LOG_LEVEL: str = "info"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Nutresa Maestro Reports API"
    SECRET_KEY: str = "your-very-secure-secret-key-here-change-this-in-production"
    
    @field_validator('ALLOWED_ORIGINS', 'BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                # Try to parse as JSON first
                return json.loads(v)
            except json.JSONDecodeError:
                # If it's not JSON, split by comma
                return [origin.strip() for origin in v.split(',')]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
