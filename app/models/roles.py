# app/models/roles.py
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)

    users = relationship("User", back_populates="role")  # Add relationship to User

    def __repr__(self):
        return f"<Role(name='{self.name}')>"
