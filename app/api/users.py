# app/api/users.py
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas
from app.schemas.user_schemas import UserRoleListResponse
from app.schemas.user_schemas import UsersListResponse
from app import models
from app.database_drivers.base_driver import BaseDriver
from app.core.database import get_db
from app.services import user_service
from app.core.security import get_current_active_user
router = APIRouter()

logger = logging.getLogger("app") 

@router.get("/detailed", response_model=List[schemas.User])
async def detailed_list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    logger.info("Reading users from the database (detailed).")
    users = user_service.get_users(db, skip=skip, limit=limit)
    logger.debug(f"Read {len(users)} users (detailed).")
    return [schemas.User.model_validate(user) for user in users]


@router.get("/user_roles", response_model=List[UserRoleListResponse]) 
async def list_user_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    logger.info("Reading users from the database (basic).")
    users = user_service.get_users(db, skip=skip, limit=limit)
    logger.debug(f"Read {len(users)} users (basic).")

    user_list = [UserRoleListResponse(full_name=user.full_name, role_id=user.role_id) for user in users]

    return user_list

@router.get("/", response_model=List[UsersListResponse]) 
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    logger.info("Reading users from the database (basic).")
    users = user_service.get_users(db, skip=skip, limit=limit)
    logger.debug(f"Read {len(users)} users (basic).")

    user_list = [UsersListResponse(full_name=user.full_name) for user in users]

    return user_list


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
