# app/api/__init__.py

import logging
from fastapi import APIRouter
from . import users, auth

logger = logging.getLogger("app")  # Get logger for this module

router = APIRouter()
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
logger.info("Starting API Routes")
