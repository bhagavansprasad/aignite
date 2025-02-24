# app/database_drivers/postgres_driver.py
import logging

from typing import Generator, Optional, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import DATABASE_URL
from app.models.base import Base
from app.models import user as user_model
from app.database_drivers.base_driver import BaseDriver
from app import schemas
from app.core import security

logger = logging.getLogger("app")  # Get logger for this module

from app.core.database import SessionLocal

def get_db() -> Generator:
    logger.debug("Creating database session.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.debug("Closing database session.")

class PostgresDriver(BaseDriver):
    def __init__(self, db_url: str = DATABASE_URL):
        logger.debug(f"Initializing PostgresDriver with URL: {db_url}")
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_user(self, db: Session, user_id: str) -> Optional[user_model.User]:
        """Retrieve a user by their ID."""
        logger.debug(f"Retrieving user with ID: {user_id}")
        user = db.query(user_model.User).filter(user_model.User.user_id == user_id).first()
        if user:
            logger.debug(f"User found: {user.email}")
        else:
            logger.debug("User not found.")
        return user

    def create_user(self, db: Session, user: schemas.UserCreate) ->  user_model.User:
        """Register a new user."""
        logger.debug(f"Registering a new user with email: {user.email}")
        hashed_password = security.get_password_hash(user.password)

        db_user = user_model.User(
            full_name=user.full_name, 
            email=user.email, 
            mobile_no=user.mobile_no, 
            password=hashed_password, 
            role_id=user.role_id)
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User {user.email} successfully registered")
        return db_user

    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[user_model.User]:
        """Retrieves all users"""
        logger.debug(f"Retrieving all users with skip: {skip} and limit: {limit}")
        users = db.query(user_model.User).offset(skip).limit(limit).all()
        logger.debug(f"Retrieved {len(users)} users.")
        return users

    def create_database(self):
        logger.debug("Creating database.")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database creation complete.")

    def drop_database(self):
        logger.warning("Dropping database.")
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("Database drop complete.")
