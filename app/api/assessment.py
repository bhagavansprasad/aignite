# app/api/assessment.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.schemas import user_schemas
from app.core.database import get_db
from app.core.security import check_role
from app.services.assessment_service import AssessmentService
from app.core.config import settings
import logging
from app.ai.ai_service import AIService
from app.models.document_details import DocumentDetails
from app.models.gcs_file import GCSFile

assessment_router = APIRouter()

logger = logging.getLogger("app")


@assessment_router.get("/generate_mcqs", summary="Generate MCQs", tags=["Assessment"])
async def generate_mcqs(
    gcs_file_ids: List[int] = Query(..., description="List of document_details.gcs_file_id"),
    sub_chapters: Optional[str] = Query(None, description="Comma-separated list of sub-chapters"),
    db: Session = Depends(get_db),
    current_user: user_schemas.User = Depends(check_role("generate_mcqs")),
    ai_service: AIService = Depends(lambda: AIService(settings.ai)),
):
    """
    Generates Multiple Choice Questions (MCQs) based on the provided documents and sub-chapters.

    - **gcs_file_ids**: A list of document_details.gcs_file_id associated with the selected subject(s).
    - **sub_chapters**: An optional comma-separated list of sub-chapters to focus the MCQ generation on.
    """

    logger.info(f"User {current_user.email} is generating MCQs for gcs_file_ids: {gcs_file_ids} and sub-chapters: {sub_chapters}")
    try:
        # Build the list of GCS URIs
        gcs_uris = []
        for gcs_file_id in gcs_file_ids:
            # Query for the GCS file
            document_detail = db.query(DocumentDetails).filter(DocumentDetails.gcs_file_id == gcs_file_id).first()
            if not document_detail:
                raise HTTPException(status_code=404, detail=f"DocumentDetails with gcs_file_id {gcs_file_id} not found")

            gcs_file = db.query(GCSFile).filter(GCSFile.id == document_detail.gcs_file_id).first() #gcs_file_id from document details
            if not gcs_file:
                raise HTTPException(status_code=404, detail=f"GCS file with ID {gcs_file_id} not found")

            # Construct the GCS URI
            gcs_uri = f"gs://{gcs_file.bucket}/{gcs_file.name}"
            gcs_uris.append(gcs_uri)
            logger.debug(f"GCS URI added: {gcs_uri}")

        # Extract list of sub-chapters
        sub_chapter_list = [s.strip() for s in sub_chapters.split(",")] if sub_chapters else []
        logger.debug(f"Sub-chapter list: {sub_chapter_list}")
        

        # Prepare parameters for the AssessmentService
        # prompt_path = "app/ai/prompts/extract_document_details_prompt.txt"
        prompt_path = "assessment.prompt"

        # Initialize the AssessmentService
        assessment_service = AssessmentService(ai_service=ai_service, db=db)

        # Generate MCQs using the service
        result = assessment_service.generate_mcqs(gcs_uris, sub_chapter_list, prompt_path)  # Passing all required information
        logger.info(f"Successfully generated MCQs: {result}")
        return result

    except HTTPException as e:
        raise e # Re-raise HTTPExceptions directly
    except Exception as e:
        logger.exception(f"Error generating MCQs: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating MCQs: {e}")
    