# app/schemas/user_schemas.py
import logging

from pydantic import BaseModel, EmailStr, constr, UUID4
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger("app")  # Get logger for this module

class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    mobile_no: constr(min_length=10, max_length=20)  # Example mobile number validation
    # Added non-required for update and other purposes - and is optional for the user data to come back
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    full_name: Optional[str] = None # removed it in user data base
    email: Optional[EmailStr] = None #removed ""
    mobile_no: Optional[constr(min_length=10, max_length=20)] = None #Removed
    password: Optional[str] = None  # Include password for updates if needed
    role_id: Optional[int] = None
    is_active: Optional[bool] = None #Added a non breaking change, so we use optional

class User(UserBase):  # all the DB params are there
    id: int
    full_name: str
    email: str
    mobile_no: str
    is_active: bool

    class Config:
        from_attributes = True 

class Token(BaseModel):
    id: UUID4 #uuid.UUID #check the formatting if correct or not
    user_id: int
    token: str
    expires_at: Optional[datetime] = None

class UserList(BaseModel):
    users: List[User]

logger.debug("User schemas defined.")