# app/core/config.py

import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "postgresql://bhagavan:jnjnuh@localhost/aignite_db")
    ALLOWED_HOSTS: list[str] = ["*"]
    SECRET_KEY: str = "aignite-secret-key"
    ALGORITHM: str = "HS256"
    TEST_DATABASE_URL: str = os.environ.get("TEST_DATABASE_URL", "postgresql://bhagavan:jnjnuh@localhost/aignite_db_test")
    MEDIA_ROOT: str = "app/media"

    # AI Configuration
    ai: dict = {
        "llm_provider": "vertexai",
        "vertexai": {
            "project_id": os.environ.get("VERTEXAI_PROJECT_ID"),  # Replace with your Vertex AI project ID
            "location": os.environ.get("VERTEXAI_LOCATION", "us-central1"),  # Replace with your Vertex AI location
            "model_name": os.environ.get("GEMINI_MODEL_NAME", "gemini-1.5-pro-002")  #Moved Gemini model name here
        },
        "openai": {
            "api_key": os.environ.get("OPENAI_API_KEY"),
        },
        "cohere": {
            "api_key": os.environ.get("COHERE_API_KEY"),
        },
        "huggingface": {
            "api_key": os.environ.get("HUGGINGFACE_API_KEY"),
        }
    }

    class Config:
        env_file = ".env"  # Load from .env file

settings = Settings()