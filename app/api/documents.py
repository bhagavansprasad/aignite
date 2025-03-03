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
from app.models.gcs_file import GCSFile
from datetime import datetime, timedelta
from app.ai.ai_service import AIService  
from app.core.config import settings  
from app.models.document_details import DocumentDetails
from app.schemas.document_details_schemas import DocumentDetailsResponse
from app.schemas.doc_list_schemas import DocListResponse 

logger = logging.getLogger("app")

documents_router = APIRouter()

@documents_router.post("/documents/ingest/", status_code=status.HTTP_202_ACCEPTED)
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

    document_service = DocumentService(db, "vertexai")
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

@documents_router.get("/documents/", response_model=List[URIResponse])
async def list_documents(
    db: Session = Depends(get_db),
    current_user: user_schemas.User = Depends(check_role("list_documents"))  # Optional: Add a permission check
):
    """
    Retrieve a list of all ingested documents (URIs).
    """
    logger.info(f"User {current_user.email} is requesting a list of all ingested documents.")
    document_service = DocumentService(db, None)  # Pass None for ai_service as it's not needed here
    uris = await document_service.get_all_uris()
    return uris

@documents_router.post("/documents/{gcs_file_id}/process", status_code=status.HTTP_200_OK)
async def process_document(
    gcs_file_id: str,  # gcs_files.id is a string
    db: Session = Depends(get_db),
    current_user: user_schemas.User = Depends(check_role("process_document")),  # Adjust permission as needed
    ai_service: AIService = Depends(lambda: AIService(settings.ai)) # Inject AIService
):
    """
    Processes a specific document if it hasn't been updated in the last day.
    """
    logger.info(f"User {current_user.email} is attempting to process document with ID: {gcs_file_id}")

    document_service = DocumentService(db, ai_service) # Pass ai_service to DocumentService

    try:
        # Get the GCSFile object from the database
        gcs_file: GCSFile = db.query(GCSFile).filter(GCSFile.id == gcs_file_id).first()

        if not gcs_file:
            logger.warning(f"GCS file with ID {gcs_file_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GCS file not found")

        # Check if the document has been updated in the last day
        if gcs_file.updated and gcs_file.updated > datetime.utcnow() - timedelta(days=1):
            logger.info(f"GCS file with ID {gcs_file_id} was updated less than a day ago. Skipping processing.")
            return {"message": "Document already processed recently"}

        # Process the document
        prompt_path = "app/ai/prompts/extract_document_details_prompt.txt"
        result = await document_service.process_document(gcs_file, prompt_path)

        # Update the 'updated' timestamp
        gcs_file.updated = datetime.utcnow()
        db.commit()
        logger.info(f"Successfully processed document with ID: {gcs_file_id}")

        return {"message": "Document processed successfully", "result": result}

    except HTTPException as e:
        logger.error(f"Error processing document: {e.detail}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing document: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing document"
        )

@documents_router.get("/document_details/{document_details_id}", response_model=DocumentDetailsResponse)
def get_document_details(
    document_details_id: int, 
    db: Session = Depends(get_db),
    current_user: user_schemas.User = Depends(check_role("get_document_details")),
):
    """
    Retrieves document details by ID.
    """
    
    logger.info(f"In get_document_details document_details_id :{document_details_id}")
    document_details = db.query(DocumentDetails).filter(DocumentDetails.gcs_file_id == document_details_id).first()
    if not document_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document details not found")
    return document_details

@documents_router.get("/doc_list/", response_model=List[DocListResponse])
async def get_doc_list(
    db: Session = Depends(get_db),
    current_user: user_schemas.User = Depends(check_role("get_doc_list"))
):
    """
    Retrieve a list of documents with their names, subjects, and extracted data.
    """
    logger.info(f"User {current_user.email} is requesting a list of documents with details.")
    document_service = DocumentService(db, None) 
    doc_list = await document_service.get_doc_list()
    return doc_list
