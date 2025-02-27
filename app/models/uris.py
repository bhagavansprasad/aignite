# app/models/uris.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

if TYPE_CHECKING:
    from app.models.gcs_file import GCSFile

class URI(Base):
    __tablename__ = "uris"

    id = Column(Integer, primary_key=True, index=True)
    uri = Column(String(2048), unique=True, nullable=False)  # Keep as "uri"
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    last_processed_at = Column(DateTime)
    status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)
    created_by_system = Column(String(255), nullable=True)

    user = relationship("User", back_populates="uris")
    gcs_files: Mapped[List["GCSFile"]] = relationship("GCSFile", back_populates="uri_obj", cascade="all, delete-orphan")