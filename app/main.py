import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.database import get_db, engine, Base
from app.core import security
from app.api.router import api_router


# Initialize logging configuration
configure_logging()

logger = logging.getLogger("app")

app = FastAPI()
Base.metadata.create_all(bind=engine)

# --- Database Initialization (Startup Event) ---
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the application...")
    db: Session = None  # Initialize db outside try block
    try:
        db = next(get_db())
    except Exception as e:
        logger.error(f"Error during startup: {e}")
    finally:
        if db:
            db.close()
    logger.info("Application startup tasks completed.")

# --- CORS Configuration ---
if settings.ALLOWED_HOSTS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.ALLOWED_HOSTS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Register Routers (Combined Router) ---
app.include_router(api_router, prefix="/api")

logger.info("FastAPI application started.")
