# app/models/user.py
import logging

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base

logger = logging.getLogger("app")  # Get logger for this module

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    mobile_no = Column(String, unique=True)
    password = Column(String) 
    role_id = Column(Integer) 
    is_active = Column(Boolean, default=True)

logger.debug("User model defined.")
