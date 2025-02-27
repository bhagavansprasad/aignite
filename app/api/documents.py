# app/api/documents.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.document_service import DocumentService
from app.schemas.uris_schemas import URIResponse 
from app.core.security import check_role
from app.schemas import user_schemas
import logging
from fastapi.responses import JSONResponse
from typing import Dict

logger = logging.getLogger("app")

router = APIRouter()

@router.post("/documents/ingest/", status_code=status.HTTP_201_CREATED)
async def ingest_documents(
    *,
    uri: str = Query(..., description="GCS URI of the bucket"),
    db: Session = Depends(get_db),
    current_user: user_schemas.User = Depends(check_role("ingest_documents"))
) -> JSONResponse:
    """
    Ingest documents from a GCS bucket.
    - Adds an entry to the `uris` table.
    - Returns the URI entry and GCS metadata as JSON.
    - Requires 'ingest_documents' permission.
    """
    logger.info(f"User {current_user.email} is ingesting documents from URI: {uri}")

    document_service = DocumentService(db)
    try:
        # Create the URI entry in the database
        # Pass an empty dictionary for metadata since we are not taking metadata from request body
        uri_obj = await document_service.create_uri_entry(
            uri=uri,
            user_id=current_user.id,
            created_by_system=None,  
            metadata={}
        )
        logger.info(f"Created URI entry: {uri_obj.uri}")
    except HTTPException as e:
        logger.error(f"Error during URI creation: {e.detail}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating URI entry."
        )

    try:
        # Get the GCS metadata
        gcs_metadata = await document_service.process_gcs_uri(uri)

        await document_service.create_gcs_file_entries(gcs_metadata["gcs_files"], uri_obj.id)
        logger.info(f"Created GCS file entries for URI ID: {uri_obj.id}")
        
        # Create a dictionary for the URI entry
        uri_entry_data = {
            "id": uri_obj.id,
            "uri": uri_obj.uri,
            "user_id": uri_obj.user_id,
            "created_at": uri_obj.created_at.isoformat() if uri_obj.created_at else None,  # Convert to string
            "last_processed_at": uri_obj.last_processed_at.isoformat() if uri_obj.last_processed_at else None,  # Convert to string
            "status": uri_obj.status,
            "error_message": uri_obj.error_message,
            "created_by_system": uri_obj.created_by_system,
            "metadata": uri_obj.metadata if isinstance(uri_obj.metadata, dict) else {}  # Ensure it's a dictionary
        }

        # Validate the URI entry data using the URIResponse schema
        uri_entry = URIResponse(**uri_entry_data)

        # Combine the URI response and GCS metadata into a single dictionary
        response_data: Dict = {
            "uri_entry": uri_entry.dict(),  # Use the validated URIResponse object
            "gcs_metadata": gcs_metadata
        }

        return JSONResponse(content=response_data, status_code=status.HTTP_201_CREATED)

    except HTTPException as e:
        logger.error(f"Error during GCS metadata processing: {e.detail}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during GCS metadata processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing GCS metadata."
        )
