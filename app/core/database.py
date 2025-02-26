import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings 
from typing import Generator, Optional, List
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()  

logger = logging.getLogger("app")  

def get_db() -> Generator:
    logger.debug("Creating database session.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.debug("Closing database session.")