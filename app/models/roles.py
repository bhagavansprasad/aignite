# app/models/roles.py
import logging

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base

logger = logging.getLogger("app")

class Role(Base): 
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False) 
    active_flag = Column(Boolean, default=True)

    users = relationship("app.models.users.User", back_populates="role") 
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"
    
logger.debug("User Roles created")
