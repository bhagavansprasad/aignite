# app/main.py
import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import ALLOWED_HOSTS
from app.api import router as api_router
from app.core.logging_config import configure_logging
from app.core.database import get_db, engine, Base
from app.core import security  

# Initialize logging configuration
configure_logging()

logger = logging.getLogger("app")  # Get logger for this module

app = FastAPI()

# Initialize the database
Base.metadata.create_all(bind=engine)

# Set all CORS enabled origins
if ALLOWED_HOSTS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in ALLOWED_HOSTS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix="/api")  # Add prefix

# Startup Event to verify all endpoints
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the application...")
    try:
        db: Session = next(get_db())  # Get a database session
        security.verify_all_endpoints_have_roles(app, db)
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Consider exiting the application if startup is critical
        # raise e
    finally:
        db.close()
    logger.info("Application startup tasks completed.")

logger.info("FastAPI application started.")
