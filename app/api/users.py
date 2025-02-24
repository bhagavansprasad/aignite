# app/api/users.py
import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app import models
from app.database_drivers.base_driver import BaseDriver
from app.database_drivers.postgres_driver import PostgresDriver, get_db
from app.services import user_service

router = APIRouter()

logger = logging.getLogger("app")  # Get logger for this module

@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info("Reading users from the database.")
    users = user_service.get_users(db, skip=skip, limit=limit)
    logger.debug(f"Read {len(users)} users.")
    
    return [schemas.User.model_validate(user) for user in users]


@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user. No authentication required for this example.
    """
    logger.info(f"Creating a new user with email: {user.email}")
    try:
        db_user = user_service.create_user(db=db, user=user)
        logger.info(f"Created a new user with email: {user.email}")
        
        return schemas.User.model_validate(db_user)
    
    except Exception as e:
        logger.exception(f"Error creating user: {e}")
        raise HTTPException(status_code=400, detail=str(e))
