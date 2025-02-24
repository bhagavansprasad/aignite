# app/models/tokens.py
import logging

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, func, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text

from app.models.base import Base

logger = logging.getLogger("app")  # Get logger for this module

class Token(Base):
    __tablename__ = "tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    token = Column(String, nullable=False) # changed from Text
    expires_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="tokens")

logger.debug("Token model defined.")
