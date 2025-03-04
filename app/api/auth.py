# app/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.users import User
from app.models.roles import Role
from app.models.tokens import Token
from app.core.security import create_access_token, verify_password
from app.core.security import get_current_user, get_current_active_user
import jwt
import logging
from app.core.config import settings 

auth_router = APIRouter()

@auth_router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handles user login and JWT authentication"""
    user = db.query(User).filter(User.full_name == username, User.is_active == True).first()

    print(f'username :{username}')
    print(f'fullname :{user}')
    print(f'password :{password}')
    print(f'password :{user.password}')
    
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    role = db.query(Role.name).filter(Role.id == user.role_id).scalar()

    if not role:
        raise HTTPException(status_code=403, detail="User role not found.")

    existing_token_entry = db.query(Token).filter(Token.user_id == user.id).first()

    if existing_token_entry:
        try:
            # Decode and validate the existing token
            jwt.decode(existing_token_entry.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return {
                "access_token": existing_token_entry.token,
                "token_type": "bearer",
                "role": role,
                "user_full_name": user.full_name,
            }
        except jwt.ExpiredSignatureError:
            logging.debug(f"Existing token for user {user.email} is expired, generating new token.")
            db.query(Token).filter(Token.user_id == user.id).delete()
            db.commit()

    access_token = create_access_token(data={"user_email": user.email, "role": role})

    new_token_entry = Token(user_id=user.id, token=access_token)
    db.add(new_token_entry)
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role,
        "user_full_name": user.full_name,
    }


@auth_router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logs out the current user by deleting their token from the database.
    """
    try:
        # Retrieve the token to be deleted from the database
        token_to_delete = db.query(Token).filter(Token.user_id == current_user.id).first()

        if not token_to_delete:
            logging.warning(f"Token not found for user ID {current_user.id} or already logged out.")
            raise HTTPException(status_code=404, detail="Token not found or already logged out.")

        # Delete the token from the database
        db.delete(token_to_delete)
        db.commit()
        logging.info(f"User {current_user.email} logged out successfully.")
        return {"message": "Successfully logged out"}

    except Exception as e:
        logging.error(f"Error during logout: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")