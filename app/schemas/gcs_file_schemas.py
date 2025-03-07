# app/schemas/gcs_file_schemas.py

from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class GCSFileCreate(BaseModel):
    uri: str  # Renamed from id
    name: str
    bucket: str
    contenttype: Optional[str] = None
    size: Optional[int] = None
    md5hash: Optional[str] = None
    crc32c: Optional[str] = None
    etag: Optional[str] = None
    timecreated: Optional[datetime] = None
    updated: Optional[datetime] = None
    file_metadata: Optional[Dict] = None  

class GCSFileResponse(BaseModel):
    id: int
    uri: str  # Renamed from id
    name: str
    bucket: str
    contenttype: Optional[str] = None
    size: Optional[int] = None
    md5hash: Optional[str] = None
    crc32c: Optional[str] = None
    etag: Optional[str] = None
    timecreated: Optional[datetime] = None
    updated: Optional[str] = None 
    file_metadata: Optional[Dict] = None
    uri_id: int

    class Config:
        orm_mode = True
        from_attributes = True