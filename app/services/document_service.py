import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.uris import URI
from app.schemas.uris_schemas import URIResponse, URICreate

logger = logging.getLogger("app")

class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    async def create_uri_entry(self, uri: str, user_id: int, created_by_system: str = None) -> URIResponse:
        """Creates a URI entry in the database."""
        logger.info(f"Creating URI entry for: {uri}")

        # Validate the URI format (Ensure it starts with gs://)
        if not uri.startswith("gs://"):
            raise HTTPException(status_code=400, detail="Invalid URI. Must start with 'gs://'")

        # Check if the URI already exists
        existing_uri = self.db.query(URI).filter(URI.uri == uri).first()
        if existing_uri:
            raise HTTPException(status_code=409, detail="URI already exists in the database.")

        try:
            db_uri = URI(
                uri=uri,  # Store in "uri" column
                user_id=user_id,
                created_by_system=created_by_system
            )
            self.db.add(db_uri)
            self.db.commit()
            self.db.refresh(db_uri)

            logger.info(f"Successfully created URI entry: {db_uri.uri}")
            return URIResponse.from_orm(db_uri)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating URI entry: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating URI entry."
            )
