# app/api/__init__.py

import logging
from fastapi import APIRouter
from . import users, auth

logger = logging.getLogger("app")  # Get logger for this module

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(users.router, prefix="/users", tags=["Users"])
logger.info("Starting API Routes")
