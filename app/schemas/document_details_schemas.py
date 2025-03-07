# app/schemas/document_details_schemas.py

from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class DocumentDetailsCreate(BaseModel):
    gcs_file_id: int
    subject: Optional[str] = None
    extracted_data: Optional[Dict] = None
    full_metadata: Optional[Dict] = None

class DocumentDetailsResponse(BaseModel):
    id: int
    gcs_file_id: int
    subject: Optional[str] = None
    extracted_data: Optional[Dict] = None
    full_metadata: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class SubjectDetails(BaseModel):
    id: int
    gcs_file_id: int
    subject: Optional[str]
    chapters: Optional[List[Dict]]
    uri_id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True