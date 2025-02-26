from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class URICreate(BaseModel):
    uri: str
    created_by_system: Optional[str] = None

class URIResponse(BaseModel):
    id: int
    uri: str 
    user_id: Optional[int] = None
    created_at: datetime
    last_processed_at: Optional[datetime] = None
    status: str
    error_message: Optional[str] = None
    created_by_system: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True 
