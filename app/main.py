# app/main.py
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings 
from app.core.logging_config import configure_logging
from app.core.database import get_db, engine, Base
from app.core import security
from app.api.documents import router as documents_router  # Import documents router
from app.api.users import router as users_router       # Import users router
from app.api.auth import router as auth_router          # Import auth router

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
        # Consider exiting if startup is critical, or handle gracefully
        # raise e
    finally:
        if db:
            db.close()
    # security.verify_all_endpoints_have_roles(app, db)
    logger.info("Application startup tasks completed.")

# --- CORS Configuration ---
if settings.ALLOWED_HOSTS: # Use settings.ALLOWED_HOSTS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.ALLOWED_HOSTS], # Use settings.ALLOWED_HOSTS
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Register Routers (Explicitly) ---
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])       # Auth endpoints
app.include_router(documents_router, prefix="/api", tags=["Documents"])  # Document endpoints
app.include_router(users_router, prefix="/api/users", tags=["Users"])             # User endpoints

logger.info("FastAPI application started.")
