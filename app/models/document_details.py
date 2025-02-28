# app/models/document_details.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class DocumentDetails(Base):
    __tablename__ = "document_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gcs_file_id: Mapped[int] = mapped_column(ForeignKey("gcs_files.id"), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=True)
    extracted_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    full_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    gcs_file = relationship("GCSFile", backref="document_details") # Correct backref