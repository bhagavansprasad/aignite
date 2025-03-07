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
from app.schemas.gcs_file_schemas import GCSFileResponse
from app.schemas.document_details_schemas import SubjectDetails


logger = logging.getLogger("app")

documents_router = APIRouter()

@documents_router.post("/ingest_uri/", summary="Ingest URIs", status_code=status.HTTP_202_ACCEPTED)
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
            target=extract_document_data,
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

@documents_router.get("/list_uris/", summary="List URIs", response_model=List[URIResponse])
async def list_uris(
    db: Session = Depends(get_db),
    current_user: user_schemas.User = Depends(check_role("list_uris"))
):
    """
    Retrieve a list of all ingested documents (URIs).
    """
    logger.info(f"User {current_user.email} is requesting a list of all ingested documents.")
    document_service = DocumentService(db, None)  # Pass None for ai_service as it's not needed here
    uris = await document_service.get_all_uris()
    return uris

@documents_router.get("/gcs_files/", response_model=List[GCSFileResponse], summary="List GCS Files")
async def list_gcs_files(
    db: Session = Depends(get_db),
    current_user: user_schemas.User = Depends(check_role("list_gcs_files"))  # Optional: Add a permission check
):
    """
    Retrieve a list of all GCS file entries.
    """
    logger.info(f"User {current_user.email} is requesting a list of GCS files.")
    
    try:
        gcs_files = db.query(GCSFile).all()

        gcs_file_responses = []
        for gcs_file in gcs_files:
            # Explicitly format the 'updated' datetime as a string
            updated_str = gcs_file.updated.isoformat() if gcs_file.updated else None

            # Create a dictionary with the data, including the formatted 'updated' field
            gcs_file_data = {
                "id": gcs_file.id,
                "uri": gcs_file.uri,
                "name": gcs_file.name,
                "bucket": gcs_file.bucket,
                "contenttype": gcs_file.contenttype,
                "size": gcs_file.size,
                "md5hash": gcs_file.md5hash,
                "crc32c": gcs_file.crc32c,
                "etag": gcs_file.etag,
                "timecreated": gcs_file.timecreated,
                "updated": updated_str,  # Use the formatted string
                "file_metadata": gcs_file.file_metadata,
                "uri_id": gcs_file.uri_id
            }

            gcs_file_responses.append(GCSFileResponse(**gcs_file_data)) # Use dictionary and pass

        logger.debug(f"Retrieved {len(gcs_file_responses)} GCS files.")
        return gcs_file_responses
    
    except Exception as e:
        logger.exception(f"Error retrieving GCS files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving GCS files"
        )
        
@documents_router.post("/process", summary="Process Document", status_code=status.HTTP_200_OK) # updated path to be without param, you can also keep as is and extract from request
async def process_document(
    gcs_file_id: str = Query(..., title="GCS File ID"),  # Expect as a query parameter
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

@documents_router.get("/{document_id}", summary="Get Document Details", response_model=DocumentDetailsResponse)
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

@documents_router.get("/document_list/", summary="Get Documents List", response_model=List[DocumentDetailsResponse]) #Updated response to DcoumentDetailsResponse
async def get_doc_list(
    db: Session = Depends(get_db),
    current_user: user_schemas.User = Depends(check_role("get_doc_list"))
):
    """
    Retrieve a list of all document details for all GCS files.
    """
    logger.info(f"User {current_user.email} is requesting a list of all document details.")

    try:
        document_details = db.query(DocumentDetails).all()  # Get all DocumentDetails entries
        # updated type to DocumentDetailsResponse and return DocumentDetails entries
        doc_list_response = [DocumentDetailsResponse.model_validate(dd) for dd in document_details]

        logger.debug(f"Retrieved {len(doc_list_response)} document details.")
        return doc_list_response

    except Exception as e:
        logger.exception(f"Error retrieving document details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving document details"
        )


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


def extract_document_data(gcs_ids: List[int]):
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
            api_url = f"{settings.SERVER_URL}/api/documents/process?gcs_file_id={gcs_file_id}"
            post_request_by_doc_id(gcs_file_id, api_url, token)

        db.commit()

    except Exception as e:
        db.rollback()
        process_logger.exception(f"Error in processing loop: {e}")
    finally:
        db.close()
        
        
@documents_router.get("/get_subjects/", summary="Get Subjects with Chapter Details", response_model=List[SubjectDetails])
async def get_subjects(
    db: Session = Depends(get_db),
    current_user: user_schemas.User = Depends(check_role("get_subjects"))  # Optional permission check
):
    """
    Retrieves a list of subjects, chapter details, and file information for all documents.
    """
    logger.info(f"User {current_user.email} is requesting a list of subjects with chapter details.")

    try:
        # Perform a join to retrieve the required information
        results = db.query(
            DocumentDetails.id,
            DocumentDetails.gcs_file_id,
            DocumentDetails.subject,
            DocumentDetails.extracted_data,
            GCSFile.uri_id,
            GCSFile.name
        ).join(GCSFile, GCSFile.id == DocumentDetails.gcs_file_id).all()

        subject_list = []
        for doc_id, gcs_file_id, subject, extracted_data, uri_id, name in results:
            chapters = extracted_data.get("chapters") if extracted_data else None

            subject_details = SubjectDetails(
                id=doc_id,
                gcs_file_id=gcs_file_id,
                subject=subject,
                chapters=chapters,
                uri_id=uri_id,
                name=name
            )
            subject_list.append(subject_details)

        logger.debug(f"Retrieved {len(subject_list)} subjects with chapter details.")
        return subject_list

    except Exception as e:
        logger.exception(f"Error retrieving subjects with chapter details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving subjects with chapter details"
        )