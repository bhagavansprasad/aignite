# app/models/users.py

from sqlalchemy.orm import relationship
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.uris import URI  # Import URI for type hinting

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    mobile_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    role = relationship("Role", back_populates="users")
    tokens = relationship("Token", back_populates="user")  # point back to `Token`
    uris: Mapped[List["URI"]] = relationship("URI", back_populates="user")  # Add URI relationship

    def __repr__(self):
        return f"<User(email='{self.email}')>"
