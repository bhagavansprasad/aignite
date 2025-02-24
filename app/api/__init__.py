# app/api/__init__.py

import logging
from fastapi import APIRouter
from . import users

logger = logging.getLogger("app")  # Get logger for this module

router = APIRouter()
router.include_router(users.router, prefix="/users", tags=["users"])
logger.info("Starting API Routes")
