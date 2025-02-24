# app/core/security.py
import logging

from passlib.context import CryptContext

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
