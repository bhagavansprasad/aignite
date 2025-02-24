# app/services/user_service.py
import logging

from sqlalchemy.orm import Session
from typing import List

from app import models, schemas
from app.core import security
from app.database_drivers.postgres_driver import PostgresDriver

logger = logging.getLogger("app")  # Get logger for this module

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.User]:
    logger.debug(f"Getting users from database (skip={skip}, limit={limit})")
    db_driver = PostgresDriver()
    users = db_driver.get_users(db, skip=skip, limit=limit)
    # return [schemas.User.model_validate(user) for user in users]
    return [schemas.User.from_orm(user) for user in users]


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    logger.debug(f"Creating user: {user.email}")
    # Hash the password!  (Important security measure)
    # hashed_password = security.get_password_hash(user.password) # calling your security class
    db_driver = PostgresDriver()
    db_user = db_driver.create_user(db = db, user = user)
    logger.info(f"User {user.email} successfully registered")
    return db_user
