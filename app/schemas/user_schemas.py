# app/schemas/user_schemas.py
import logging

from pydantic import BaseModel, EmailStr, constr
from typing import List, Optional

logger = logging.getLogger("app")  # Get logger for this module

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    mobile_no: constr(min_length=10, max_length=20)  # Example mobile number validation
    password: str  
    role_id: Optional[int] = None
    is_active: Optional[bool] = None

class UserUpdate(UserCreate):
    pass

class User(BaseModel):
    id: int
    full_name: Optional[str]
    email: EmailStr
    mobile_no: constr(min_length=10, max_length=20)
    password: str  # Keep this only if you want to return hashed passwords
    role_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True  # Pydantic v2 replacement for orm_mode
        
class UserList(BaseModel):
    users: List[User]

logger.debug("User schemas defined.")
