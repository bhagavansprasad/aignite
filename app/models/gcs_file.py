# app/models/gcs_file.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BigInteger, Identity, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class GCSFile(Base):
    __tablename__ = "gcs_files"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True) # New primary key
    uri: Mapped[str] = mapped_column(String(255), index=True)  # GCS object ID - Renamed from id
    uri_id: Mapped[int] = mapped_column(ForeignKey("uris.id"), nullable=False)  # Foreign key to URIs
    name: Mapped[str] = mapped_column(String(2048), nullable=False)  # File name with path
    bucket: Mapped[str] = mapped_column(String(255), nullable=False)  # Bucket name
    contenttype: Mapped[str] = mapped_column(String(255), nullable=True)  # Content type
    size: Mapped[int] = mapped_column(BigInteger, nullable=True)  # File size
    md5hash: Mapped[str] = mapped_column(String(255), nullable=True)  # MD5 hash
    crc32c: Mapped[str] = mapped_column(String(255), nullable=True)  # CRC32C checksum
    etag: Mapped[str] = mapped_column(String(255), nullable=True)  # ETag
    timecreated: Mapped[datetime] = mapped_column(DateTime, nullable=True)  # Creation time
    updated: Mapped[datetime] = mapped_column(DateTime, nullable=True)  # Last updated time
    file_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)  # Metadata (JSON)

    uri_obj = relationship("URI", back_populates="gcs_files")  # Relationship with URIs table - Renamed to uri_obj
    
    
    
    