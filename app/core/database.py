import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import DATABASE_URL
from typing import Generator, Optional, List

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger("app")  # Get logger for this module

def get_db() -> Generator:
    logger.debug("Creating database session.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.debug("Closing database session.")