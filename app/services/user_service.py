# app/services/user_service.py
import logging

from sqlalchemy.orm import Session
from typing import List

from app import models, schemas
from app.core import security

logger = logging.getLogger("app")  # Get logger for this module

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.User]:
    logger.debug(f"Getting users from database (skip={skip}, limit={limit})")
    users = db.query(models.User).offset(skip).limit(limit).all()
    # return [schemas.User.model_validate(user) for user in users]
    return [schemas.User.from_orm(user) for user in users]

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    logger.debug(f"Creating user: {user.email}")
    # Hash the password!  (Important security measure)
    # hashed_password = security.get_password_hash(user.password) # calling your security class
    hashed_password = user.password
    db_user = models.User(
        email=user.email,
        mobile_no=user.mobile_no,
        password=hashed_password,
        full_name=user.full_name,
        role_id=user.role_id  
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User {user.email} successfully registered")
    return db_user
