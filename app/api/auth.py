from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.users import User
from app.models.roles import Role
from app.models.tokens import Token
from app.core.security import create_access_token, verify_password
from app.core.security import get_current_user
import jwt
import logging
from app.core.security import SECRET_KEY, ALGORITHM
from pdbwhereami import whereami


router = APIRouter()

@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handles user login and JWT authentication"""
    user = db.query(User).filter(User.full_name == username, User.is_active == True).first()

    # print(f'username :{username}')
    # print(f'fullname :{user}')
    # print(f'password :{password}')
    # print(f'password :{user.password}')
    
    if not user or not verify_password(password, user.password):
        whereami()
        raise HTTPException(status_code=401, detail="Invalid username or password")

    role = db.query(Role.name).filter(Role.id == user.role_id).scalar()

    if not role:
        raise HTTPException(status_code=403, detail="User role not found.")

    existing_token_entry = db.query(Token).filter(Token.user_id == user.id).first()

    if existing_token_entry:
        try:
            # Decode and validate the existing token
            jwt.decode(existing_token_entry.token, SECRET_KEY, algorithms=[ALGORITHM])
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


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Handles user logout by removing the active JWT token from the database.
    """
    # ✅ Delete user's token from the database
    deleted = db.query(Token).filter(Token.user_id == current_user.id).delete()

    if not deleted:
        raise HTTPException(status_code=404, detail="Token not found or already logged out.")

    db.commit()
    
    return {"message": "Successfully logged out"}
