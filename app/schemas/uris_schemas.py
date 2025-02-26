# app/schemas/uris_schemas.py

from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class URICreate(BaseModel):
    uri: str
    created_by_system: Optional[str] = None
    metadata: Optional[Dict] = None 

class URIResponse(BaseModel):
    id: int
    uri: str
    user_id: Optional[int] = None
    created_at: str
    last_processed_at: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_by_system: Optional[str] = None
    metadata: Optional[Dict] = None

    class Config:
        orm_mode = True
        from_attributes = True