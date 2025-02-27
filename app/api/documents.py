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
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger("app")

router = APIRouter()

@router.post("/documents/ingest/", status_code=status.HTTP_202_ACCEPTED)
async def ingest_documents(
    *,
    uri: str = Query(..., description="GCS URI of the bucket"),
    db: Session = Depends(get_db),
    current_user: user_schemas.User = Depends(check_role("ingest_documents"))
) -> JSONResponse:
    """
    Ingest documents from a GCS bucket.
    - Adds an entry to the `uris` table.
    - Returns a comprehensive message about the ingestion process.
    - Requires 'ingest_documents' permission.
    """
    logger.info(f"User {current_user.email} is ingesting documents from URI: {uri}")

    document_service = DocumentService(db)
    try:
        # Create the URI entry in the database
        uri_obj = await document_service.create_uri_entry(
            uri=uri,
            user_id=current_user.id,
            created_by_system=None,
            metadata={}
        )
        logger.info(f"Created URI entry: {uri_obj.uri}")

        # Update the URI status to "processing"
        uri_obj.status = "processing"
        db.commit()

    except HTTPException as e:
        logger.error(f"Error during URI creation: {e.detail}")
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating URI entry."
        )

    try:
        # Get the GCS metadata
        gcs_metadata = await document_service.process_gcs_uri(uri)

        # Create GCS file entries in the database
        await document_service.create_gcs_file_entries(gcs_metadata["gcs_files"], uri_obj.id)
        logger.info(f"Created GCS file entries for URI ID: {uri_obj.id}")

        # Construct the simplified GCS metadata
        simplified_gcs_files: List[Dict] = []
        for file in gcs_metadata["gcs_files"]:
            simplified_gcs_files.append({
                "name": file["name"],
                "bucket": file["bucket"],
                "content_type": file["contenttype"],
                "size": file["size"],
                "created_at": file["timecreated"]
            })

        # Construct a dictionary for the URI entry
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

        # Construct the response data
        response_data: Dict = {
            "message": f"Document ingestion started for URI: {uri}. {len(gcs_metadata['gcs_files'])} documents found. Understanding of documents is in progress. Check the status endpoint for updates.",
            "uri_entry": uri_entry.dict(),
            "document_summary": {
                "total_documents_found": len(gcs_metadata["gcs_files"]),
                "processing_status": "In Progress",
                "understanding_status": "In Progress",
                "expected_completion": "A few minutes"
            },
            "gcs_metadata": {
                "gcs_files": simplified_gcs_files
            }
        }

        return JSONResponse(content=response_data, status_code=status.HTTP_202_ACCEPTED)

    except HTTPException as e:
        logger.error(f"Error during GCS metadata processing: {e.detail}")
        db.rollback()
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during GCS metadata processing: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing GCS metadata."
        )
