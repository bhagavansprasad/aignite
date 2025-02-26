# app/core/config.py
import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "postgresql://bhagavan:jnjnuh@localhost/aignite_db")
    ALLOWED_HOSTS: list[str] = ["*"]  
    SECRET_KEY: str = "aignite-secret-key"  # !!! WARNING !!! See below
    ALGORITHM: str = "HS256"
    TEST_DATABASE_URL: str = os.environ.get("TEST_DATABASE_URL", "postgresql://bhagavan:jnjnuh@localhost/aignite_db_test")
    MEDIA_ROOT: str = "app/media"  
    GEMINI_MODEL_NAME: str = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.0-pro-exp-02-05")


    class Config:
        env_file = ".env"  # Load from .env file

settings = Settings()