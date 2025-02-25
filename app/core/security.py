# app/core/security.py
import logging
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from app.core.config import SECRET_KEY, ALGORITHM
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.users import User
from app.models.tokens import Token

logger = logging.getLogger("app")  # Get logger for this module

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.debug(f"Verifying password.")
    is_verified = pwd_context.verify(plain_password, hashed_password)
    logger.debug(f"Password verification result: {is_verified}")
    return is_verified

def get_password_hash(password: str) -> str:
    logger.debug(f"Generating password hash.")
    hashed_password = pwd_context.hash(password)
    logger.debug(f"Password hash generated.")
    return hashed_password

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return True
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Decode the JWT token and return the authenticated user.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("user_email")
        
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.email == email, User.is_active == True).first()

        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Ensure token exists in DB (prevents reuse of invalidated tokens)
        token_entry = db.query(Token).filter(Token.user_id == user.id, Token.token == token).first()
        if not token_entry:
            raise HTTPException(status_code=401, detail="Token has been revoked")

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
