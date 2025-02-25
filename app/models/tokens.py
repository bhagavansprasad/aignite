# app/models/tokens.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base
from app.models.users import User

class Token(Base):
    __tablename__ = "tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE")) # add ondelete
    token = Column(String, nullable=False)
    expires_at = Column(DateTime)

    user = relationship("User", back_populates="tokens") # point back to user using user

    def __repr__(self):
        return f"<Token(id='{self.id}')>"
