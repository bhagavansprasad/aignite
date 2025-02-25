# app/models/users.py
import logging

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base

logger = logging.getLogger("app")  

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    mobile_no = Column(String, unique=True)
    password = Column(String)  # Store hashed password!
    role_id = Column(Integer, ForeignKey("roles.id")) #, ondelete="SET NULL")
    is_active = Column(Boolean, default=True)

    role = relationship("app.models.roles.Role", back_populates="users") 
    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

logger.debug("User model defined.")
