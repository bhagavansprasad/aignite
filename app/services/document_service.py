import logging
from sqlalchemy.orm import Session
from app.models.uris import URI
from fastapi import HTTPException, status
from google.cloud import storage
import json
from datetime import datetime
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger("app")

class DocumentService:
    def __init__(self, db: Session):
        self.db = db
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

                    file_metadata = {
                        "id": blob.id,
                        "selfLink": blob.self_link,
                        "name": blob.name,
                        "bucket": blob.bucket.name,  
                        "contentType": blob.content_type,
                        "size": blob.size,
                        "md5Hash": blob.md5_hash,
                        "crc32c": blob.crc32c,
                        "etag": blob.etag,
                        "timeCreated": created_str,  
                        "updated": updated_str,  
                        "metadata": blob.metadata, 
                    }
                    file_metadata_list.append(file_metadata)
                    logger.debug(f"Extracted metadata for file: {blob.name}") 

            metadata = {"gcs_files": file_metadata_list}  
            logger.debug(f"GCS metadata: {metadata}") 

            logger.info(f"Successfully processed GCS URI: {uri}") 
            return metadata

        except Exception as e:
            logger.exception(f"Error accessing GCS bucket: {e}") 
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error accessing GCS bucket: {str(e)}"
            )
