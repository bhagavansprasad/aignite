from fastapi import APIRouter
from app.api.users import users_router
from app.api.auth import auth_router 
from app.api.documents import documents_router

api_router = APIRouter()
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
