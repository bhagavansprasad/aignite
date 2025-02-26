# app/models/__init__.py
from app.core.database import Base  # Ensure Base is imported first
from app.models.users import User
from app.models.roles import Role
from app.models.tokens import Token
