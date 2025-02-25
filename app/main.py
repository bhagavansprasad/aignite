# app/main.py
import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import ALLOWED_HOSTS
from app.api import router as api_router
from app.core.logging_config import configure_logging
from app.core.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text

# Initialize logging configuration
configure_logging()

logger = logging.getLogger("app")  # Get logger for this module

app = FastAPI()

# Set all CORS enabled origins
if ALLOWED_HOSTS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in ALLOWED_HOSTS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router)

logger.info("FastAPI application started.")
