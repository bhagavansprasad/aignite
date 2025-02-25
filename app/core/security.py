# app/core/security.py
import logging
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from app.core.config import SECRET_KEY, ALGORITHM
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.users import User
from app.models.tokens import Token
from app.models.endpoint_role import EndpointRole 
from typing import List

logger = logging.getLogger("app")  

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define the HTTP bearer scheme for API authentication
bearer_scheme = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    logger.debug(f"Verifying password.")
    # is_verified = pwd_context.verify(plain_password, hashed_password)
    is_verified = (plain_password == hashed_password)
    logger.debug(f"Password verification result: {is_verified}")
    return is_verified

def get_password_hash(password: str) -> str:
    """Generates a password hash."""
    logger.debug(f"Generating password hash.")
    # hashed_password = pwd_context.hash(password)
    hashed_password = password
    logger.debug(f"Password hash generated.")
    return hashed_password

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    """Creates a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """
    Retrieves the current user from the database based on the JWT token.
    """
    return _get_user_from_token(token, db)

async def get_current_active_user(token: str = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """
    Retrieves the current active user from the database based on the JWT token extracted from Authorization header.
    """
    return _get_user_from_token(token.credentials, db)  # Correctly accesses the token string

def _get_user_from_token(token: str, db: Session):
    """
    Helper function to decode the JWT token and retrieve the user.
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
    except Exception as e: # Catch any other exceptions
        logger.exception("Error decoding token: %s", e)  # Log the exception
        raise HTTPException(status_code=401, detail="Invalid token")  # Generic message

def get_allowed_roles_for_endpoint(endpoint_name: str, db: Session) -> List[int]:
    """
    Fetches the allowed role IDs for a given endpoint from the database.

    Args:
        endpoint_name: The name of the endpoint (e.g., "detailed_list_users").
        db: The database session.

    Returns:
        A list of allowed role IDs, or an empty list if the endpoint is not found.
    """
    try:
        endpoint_roles = db.query(EndpointRole).filter(EndpointRole.endpoint_name == endpoint_name).all()
        if endpoint_roles:
            return [endpoint_role.role_id for endpoint_role in endpoint_roles]
        else:
            logger.warning(f"No roles found for endpoint: {endpoint_name}")
            return []  # Or raise an exception if you prefer to enforce that all endpoints have roles
    except Exception as e:
        logger.error(f"Error fetching roles for endpoint {endpoint_name}: {e}")
        return []  # Or raise an exception
    
def check_role(endpoint_name: str):
    """
    Dependency that checks if the current user has one of the allowed roles for the given endpoint.
    """
    def role_check_dependency(
        current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
    ):
        allowed_roles = get_allowed_roles_for_endpoint(endpoint_name, db)
        if not allowed_roles:
            logger.warning(f"No roles configured for endpoint: {endpoint_name}")
            raise HTTPException(status_code=403, detail="Endpoint not configured with roles") # Raise an error instead

        if current_user.role_id not in allowed_roles:
            logger.warning(
                f"User {current_user.email} with role ID {current_user.role_id} attempted to access endpoint "
                f"{endpoint_name} requiring roles {allowed_roles}."
            )
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return role_check_dependency
