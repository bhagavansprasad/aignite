# app/database_drivers/base_driver.py
import logging

from abc import ABC, abstractmethod
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import user as user_model
from app import schemas

logger = logging.getLogger("app")  # Get logger for this module

class BaseDriver(ABC):
    @abstractmethod
    def get_user(self, db: Session, user_id: str) -> Optional[user_model.User]:
        """Abstract method to retrieve a user by their ID."""
        pass

    @abstractmethod
    def create_user(self, db: Session, user: schemas.UserCreate) ->  user_model.User:
        """Abstract method to register a new user."""
        pass

    @abstractmethod
    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[user_model.User]:
        """Abstract method to retrieve all the users."""
        pass
