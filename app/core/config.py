from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    
    # Subdomains configuration
    SUBDOMAINS_FILE: str = "static/subdomains.json"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Application settings
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
