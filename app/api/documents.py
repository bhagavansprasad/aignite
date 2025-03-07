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
import multiprocessing
import httpx
from app.models.tokens import Token
from app.models.uris import URI
from app.models.tokens import Token  
from app.models.uris import URI  
from app.models.gcs_file import GCSFile 


logger = logging.getLogger("app")

documents_router = APIRouter()

@documents_router.post("/documents/ingest/", status_code=status.HTTP_202_ACCEPTED)
async def ingest_uris(
    *,
    uri: str = Query(..., description="GCS URI of the bucket"),
    db: Session = Depends(get_db),
    current_user: user_schemas.User = Depends(check_role("ingest_uris"))
) -> JSONResponse:
    """
    Ingest documents from a GCS bucket.
    - Adds an entry to the `uris` table.
    - Returns a comprehensive message about the ingestion process.
    - Requires 'ingest_uris' permission.
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
        gcs_ids = await document_service.create_gcs_file_entries(gcs_metadata["gcs_files"], uri_obj.id)
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

        logger.info(f"gcs_ids : {gcs_ids}")
        
        # --- Start the background process here ---
        process = multiprocessing.Process(
            target=process_documents,
            args=(gcs_ids,),  # Pass only gcs_file_ids
        )        
        process.start()
        logger.info(f"Started background process (PID: {process.pid}) for URI ID: {uri_obj.id}")
                
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


def post_request_by_doc_id(gcs_file_id: int, api_url: str, token: str):
    """
    Sends a POST request to the /process endpoint for a given GCS file ID.
    """
    logging.basicConfig(level=logging.INFO)
    process_logger = logging.getLogger(f"process_api_{gcs_file_id}")
    process_logger.info(f"Sending POST request to {api_url} for GCS file ID: {gcs_file_id}")

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}",
    }

    try:
        response = httpx.post(api_url, headers=headers, timeout=60)  # Adjust timeout as needed

        if response.status_code == 200:
            process_logger.info(f"Successfully processed GCS file ID {gcs_file_id}: {response.text}")
        elif response.status_code == 404:
            process_logger.warning(f"GCS file ID {gcs_file_id} not found: {response.text}")
        else:
            process_logger.error(
                f"Error processing GCS file ID {gcs_file_id}: Status {response.status_code}, {response.text}"
            )

    except httpx.RequestError as e:
        process_logger.error(f"Request error processing GCS file ID {gcs_file_id}: {e}")
    except Exception as e:
        process_logger.exception(f"Unexpected error processing GCS file ID {gcs_file_id}: {e}")


def process_documents(gcs_ids: List[int]):
    """
    Sends POST requests to the /process endpoint for each GCS file ID,
    extracting the token based on the specified relationships.
    """
    logging.basicConfig(level=logging.INFO)
    process_logger = logging.getLogger(f"loop_process_{gcs_ids}")
    process_logger.info(f"Starting document processing loop for GCS file IDs: {gcs_ids}")

    # Setup database connection (create a new engine and session)
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings  # Import settings

    engine = create_engine(settings.DATABASE_URL) # Get DB URL from settings
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Process each document by sending a POST request to the API
        for gcs_file_id in gcs_ids:
            # Query to get the token
            token_entry = (
                db.query(Token)
                .join(URI, URI.user_id == Token.user_id)
                .join(GCSFile, GCSFile.uri_id == URI.id)
                .filter(GCSFile.id == gcs_file_id)
                .first()
            )

            if not token_entry:
                process_logger.error(f"No token found for GCS file ID {gcs_file_id}.")
                continue  

            token = token_entry.token
            api_url = f"{settings.SERVER_URL}/api/documents/documents/{gcs_file_id}/process" #get url from settings
            post_request_by_doc_id(gcs_file_id, api_url, token)

        db.commit()

    except Exception as e:
        db.rollback()
        process_logger.exception(f"Error in processing loop: {e}")
    finally:
        db.close()
        