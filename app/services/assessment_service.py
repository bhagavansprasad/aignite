# app/services/assessment_service.py

import logging
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ai.ai_service import AIService

logger = logging.getLogger("app")

class AssessmentService:
    def __init__(self, ai_service: AIService, db: Session = None):
        """
        Initializes the AssessmentService.

        Args:
            ai_service: An instance of the AIService for interacting with LLMs.
            db: An optional database session.
        """
        self.ai_service = ai_service
        self.db = db
        logger.debug("AssessmentService initialized")

    def generate_mcqs(self, gcs_uris: List[str], sub_chapter_list: List[str], prompt_src: str) -> Dict[str, str]:
        """
        Generates Multiple Choice Questions (MCQs) using the AIService.

        Args:
            gcs_uris: A list of GCS URIs for the documents.
            prompt_src: The path to the prompt file.
            sub_chapter_list: A list of sub-chapters to filter the MCQs on.

        Returns:
            A dictionary containing the query and the generated reply.
        """
        logger.info(f"Generating MCQs using AIService for files: {gcs_uris}, prompt: {prompt_src}, sub-chapters: {sub_chapter_list}")

        sub_chapter_string = ""
        try:
            # Prepare the prompt, injecting subchapter information if available
            if sub_chapter_list:
                sub_chapter_string = ", ".join(sub_chapter_list)

            result = self.ai_service.generate_mcqs(
                file_uris=gcs_uris, 
                sub_chapter_string=sub_chapter_string,
                prompt_src=prompt_src
                )
            logger.info(f"Successfully generated MCQs: {result}")
            return result

        except Exception as e:
            logger.exception(f"Error generating MCQs: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error generating MCQs: {e}")
