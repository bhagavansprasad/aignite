# app/services/document_service.py

import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.uris import URI
from app.schemas.uris_schemas import URIResponse, URICreate
from app.models.gcs_file import GCSFile
from app.schemas.gcs_file_schemas import GCSFileCreate
from typing import List
from typing import List, Dict, Any 
from sqlalchemy.exc import IntegrityError
from google.cloud import storage
from app.ai.ai_service import AIService
from app.models.document_details import DocumentDetails
from app.schemas.doc_list_schemas import DocListResponse

logger = logging.getLogger("app")

class DocumentService:
    def __init__(self, db: Session, ai_service: AIService):
        self.db = db
        self.ai_service = ai_service
        logger.debug("DocumentService initialized")
        
    async def create_uri_entry(self, uri: str, user_id: int, created_by_system: str = None, metadata: dict = None):  # Add metadata parameter
        """Creates a URI entry in the database."""
        logger.info(f"Creating URI entry for uri: {uri}, user_id: {user_id}, created_by_system: {created_by_system}, metadata: {metadata}") # Log input parameters
        db_uri = URI(
            uri=uri,
            user_id=user_id,
            created_by_system=created_by_system,
            metadata=metadata
        )
        self.db.add(db_uri)
        try:
            logger.debug("Committing URI entry to database")
            self.db.commit()
            self.db.refresh(db_uri)
            logger.info(f"Successfully created URI entry with id: {db_uri.id}")
            return db_uri
        except IntegrityError as e:
            self.db.rollback()
            logger.warning(f"URI entry already exists: {str(e)}")
            existing_uri = self.db.query(URI).filter(URI.uri == uri).first()
            if existing_uri:
                logger.info(f"Returning existing URI entry with id: {existing_uri.id}")
                return existing_uri
            else:
                logger.error("IntegrityError occurred, but could not retrieve existing URI.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error creating URI entry: {str(e)}"
                )
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error creating URI entry: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating URI entry: {str(e)}"
            )

    async def process_gcs_uri(self, uri: str) -> dict:
        """Connects to GCS, lists files, and prepares metadata."""
        logger.info(f"Processing GCS URI: {uri}")

        if not uri.startswith("gs://"):
            logger.warning(f"Invalid URI format: {uri}. URI must start with gs://")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URI must start with gs://")

        try:
            bucket_name = uri.split('/')[2]
            prefix = '/'.join(uri.split('/')[3:])
            logger.debug(f"Extracted bucket_name: {bucket_name}, prefix: {prefix}")
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)

            file_metadata_list = []
            for blob in blobs:
                if not blob.name.endswith('/'):
                    # Convert datetime to ISO format string
                    updated_str = blob.updated.isoformat() if blob.updated else None
                    created_str = blob.time_created.isoformat() if blob.time_created else None
                    metadata = blob.metadata if blob.metadata is not None else {}
                    md5hash = blob.md5_hash if blob.md5_hash is not None else "" 

                    file_metadata = {
                        "uri": blob.id,
                        "selfLink": blob.self_link,
                        "name": blob.name,
                        "bucket": blob.bucket.name,
                        "contenttype": blob.content_type,
                        "size": blob.size,
                        "md5hash": md5hash,
                        "crc32c": blob.crc32c,
                        "etag": blob.etag,
                        "timecreated": created_str,
                        "updated": updated_str,
                        "file_metadata": metadata,
                    }
                    file_metadata_list.append(file_metadata)
                    logger.debug(f"Extracted metadata for file: {blob.name}")

            metadata = {"gcs_files": file_metadata_list}
            logger.info(f"Successfully processed GCS URI: {uri}")
            return metadata

        except Exception as e:
            logger.exception(f"Error accessing GCS bucket: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error accessing GCS bucket: {str(e)}"
            )

    async def create_gcs_file_entries(self, gcs_files: List[dict], uri_id: int):
        """Creates GCS file entries in the database."""
        logger.info(f"Creating GCS file entries for URI ID: {uri_id}")

        try:
            for file_data in gcs_files:
                gcs_file_create = GCSFileCreate(**file_data)

                # Check if the entry already exists
                existing_gcs_file = self.db.query(GCSFile).filter(
                    GCSFile.uri == gcs_file_create.uri,
                    GCSFile.uri_id == uri_id,
                    GCSFile.md5hash == gcs_file_create.md5hash
                ).first()

                if existing_gcs_file:
                    logger.warning(f"GCS file entry already exists (uri: {gcs_file_create.uri}, uri_id: {uri_id}, md5hash: {gcs_file_create.md5hash}). Skipping insertion.")
                    continue  # Skip to the next file
                                   
                # Create a new GCSFile object
                db_gcs_file = GCSFile(
                    uri=gcs_file_create.uri,
                    uri_id=uri_id,
                    name=gcs_file_create.name,
                    bucket=gcs_file_create.bucket,
                    contenttype=gcs_file_create.contenttype,
                    size=gcs_file_create.size,
                    md5hash=gcs_file_create.md5hash,
                    crc32c=gcs_file_create.crc32c,
                    etag=gcs_file_create.etag,
                    timecreated=gcs_file_create.timecreated,
                    updated=gcs_file_create.updated,
                    file_metadata=gcs_file_create.file_metadata,
                )

                self.db.add(db_gcs_file)
                logger.debug(f"Added GCS file entry: {db_gcs_file.name}")

            self.db.commit()
            logger.info(f"Successfully created GCS file entries for URI ID: {uri_id}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating GCS file entries: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating GCS file entry."
            )

            
    def _extract_document_details(self, result: dict) -> dict:
        """Extracts specific document details from the AI result."""
        logger.info("Extracting specific document details from AI result")
        try:
            subject = result.get("metadata", {}).get("subject")
            chapters = result.get("chapters", [])
            chapter_details = []

            for chapter in chapters:
                chapter_name = chapter.get("name")
                subchapter_names = [subchapter.get("name") for subchapter in chapter.get("subchapters", [])]
                chapter_details.append({"name": chapter_name, "subchapters": subchapter_names})

            extracted_data = {"subject": subject, "chapters": chapter_details}
            logger.debug(f"Extracted data: {extracted_data}")
            return extracted_data
        except Exception as e:
            logger.error(f"Error extracting document details: {e}")
            return {}

    async def process_document(self, gcs_file: GCSFile, prompt_path: str):
        """
        Processes a GCS file, extracts metadata, and stores it in the database.
        """
        logger.info(f"Processing GCS file: {gcs_file}")

        try:
            gcs_uri = f"gs://{gcs_file.bucket}/{gcs_file.name}"
            logger.debug(f"Constructed GCS URI: {gcs_uri}")

            # Extract document details using the AIService
            extracted_details = self.ai_service.extract_document_details(gcs_uri, prompt_path)

            if not extracted_details:
                logger.warning(f"Failed to extract details from document: {gcs_uri}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to extract document details"
                )

            # Extract specific document details
            extracted_data = self._extract_document_details(extracted_details)

            # Create a DocumentDetails object
            db_document_details = DocumentDetails(
                gcs_file_id=gcs_file.id,
                subject=extracted_data.get("subject"),
                extracted_data=extracted_data,
                full_metadata=extracted_details,
            )
            self.db.add(db_document_details)
            self.db.commit()
            self.db.refresh(db_document_details)

            logger.info(f"Successfully processed GCS file and stored details in the database. Document Details ID: {db_document_details.id}")
            return extracted_details  # Or return db_document_details if you want the database object

        except Exception as e:
            self.db.rollback()
            logger.exception(f"Error processing GCS file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing document: {e}"
            )

    async def get_all_uris(self) -> List[URIResponse]:
        """
        Retrieves a list of all URIs from the database.
        """
        logger.info("Retrieving a list of all URIs from the database.")
        try:
            uris = self.db.query(URI).all()
            # Convert the SQLAlchemy objects to URIResponse objects, formatting datetime and ensuring metadata is a dict
            uri_responses = []
            for uri in uris:
                uri_data: Dict[str, Any] = {  # Specify types for uri_data
                    "id": uri.id,
                    "uri": uri.uri,
                    "user_id": uri.user_id,
                    "created_at": uri.created_at.isoformat() if uri.created_at else None,
                    "last_processed_at": uri.last_processed_at.isoformat() if uri.last_processed_at else None,
                    "status": uri.status,
                    "error_message": uri.error_message,
                    "created_by_system": uri.created_by_system,
                    "metadata": uri.metadata if isinstance(uri.metadata, dict) else {},  # Ensure metadata is a dict
                }
                uri_responses.append(URIResponse(**uri_data))

            logger.debug(f"Retrieved {len(uris)} URIs.")
            return uri_responses
        except Exception as e:
            logger.exception(f"Error retrieving URIs: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving URIs"
            )

    async def get_doc_list(self) -> List[DocListResponse]:
        """
        Retrieves a list of documents with their names, subjects, and extracted data.
        """
        logger.info("Retrieving a list of documents with their names, subjects, and extracted data.")
        try:
            # Join the gcs_files and document_details tables
            doc_list = self.db.query(GCSFile.name, DocumentDetails.subject, DocumentDetails.extracted_data).join(
                DocumentDetails, GCSFile.id == DocumentDetails.gcs_file_id
            ).all()

            # Convert the results to a list of DocListResponse objects
            doc_list_response = [DocListResponse(name=name, subject=subject, extracted_data=extracted_data) for name, subject, extracted_data in doc_list]

            logger.debug(f"Retrieved {len(doc_list_response)} documents with details.")
            return doc_list_response
        except Exception as e:
            logger.exception(f"Error retrieving document list: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving document list"
            )
