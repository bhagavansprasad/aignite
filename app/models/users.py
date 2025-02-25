# app/models/users.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    mobile_no = Column(String(20), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"))  # Foreign key to roles table
    is_active = Column(Boolean, default=True)

    role = relationship("Role", back_populates="users")
    tokens = relationship("Token", back_populates="user") # point back to `Token`

    def __repr__(self):
        return f"<User(email='{self.email}')>"
