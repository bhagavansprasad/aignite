from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.document_service import DocumentService
from app.schemas.uris_schemas import URIResponse
from app.core.security import check_role
from app.schemas import user_schemas
import logging

logger = logging.getLogger("app")

router = APIRouter()

@router.post("/documents/ingest/", response_model=URIResponse, status_code=status.HTTP_201_CREATED)
async def ingest_documents(
    *,
    uri: str = Query(..., description="GCS URI of the bucket"),
    db: Session = Depends(get_db),
    current_user: user_schemas.User = Depends(check_role("ingest_documents")),
    created_by_system: str = Query(None, description="System that created the URI entry (optional)")
):
    """
    Ingest documents from a GCS bucket.
    - Adds an entry to the `uris` table.
    - Requires 'ingest_documents' permission.
    """
    logger.info(f"User {current_user.email} is ingesting documents from URI: {uri}")

    try:
        document_service = DocumentService(db)
        uri_obj = await document_service.create_uri_entry(
            uri=uri,
            user_id=current_user.id,
            created_by_system=created_by_system
        )
        logger.info(f"Created URI entry: {uri_obj.uri}")
        return uri_obj
    except HTTPException as e:
        logger.error(f"Error during URI creation: {e.detail}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating URI entry."
        )
