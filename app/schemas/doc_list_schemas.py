# app/schemas/doc_list_schemas.py

from pydantic import BaseModel
from typing import Optional, Dict

class DocListResponse(BaseModel):
    name: str
    subject: Optional[str] = None
    extracted_data: Optional[Dict] = None

    class Config:
        orm_mode = True
        from_attributes = True
