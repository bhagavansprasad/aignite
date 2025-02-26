# app/ai/ai_service.py
import logging
from typing import Dict, Optional

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

from app.core.config import settings  # Get Vertex AI initialization from config
from app.ai.schemas.qa_response_schema import QAResponseSchema
from app.ai.schemas.prompt_schema import PromptSchema
from app.ai.schemas.llm_response_schema import LLMResponseSchema  # Assuming you have this
from pydantic import ValidationError
from app.core.config import settings 
import json
import re

logger = logging.getLogger("app")


class AIService:
    def __init__(self, model_name: str = settings.GEMINI_MODEL_NAME):
        """
        Initializes the AIService with a Gemini model from Vertex AI.
        Ensure Vertex AI is initialized in app/core/config.py (or similar).
        """
        self.model_name = model_name
        self.model = GenerativeModel(model_name)
        logger.info(f"AIService initialized with Gemini model: {model_name}")

    async def generate_text(self, prompt: str, generation_config: dict = None) -> str:
        """
        Generates text using the Gemini model.

        Args:
            prompt (str): The prompt for the LLM.
            generation_config (dict, optional): Generation configuration parameters (e.g., temperature, max_output_tokens). Defaults to None.

        Returns:
            str: The generated text.
        """
        try:
            # Set generation configuration
            if generation_config is None:
                generation_config = {
                    "max_output_tokens": 2048,
                    "temperature": 0.9,
                    "top_p": 1
                }

            config = GenerationConfig(**generation_config)

            response = self.model.generate_content(prompt, generation_config=config)
            return response.text  # Access the text result

        except Exception as e:
            logger.exception(f"Error generating text with Gemini model: {e}")
            raise  # Re-raise the exception


    async def get_document_metadata(self, document_uri: str) -> Dict:
        """
        Gets metadata from the Gemini model based on document content.

        Args:
            document_uri (str): The URI of the document to analyze.

        Returns:
            Dict: A dictionary containing the extracted metadata. Returns an empty dictionary on error.
        """
        prompt = f"""
        Extract the following information from the document at this URI: {document_uri}
        If any information is not found, return null for that value.

        Return a valid JSON object:
        {{
            "subject": "...",
            "author": "...",
            "class": "...",
            "sections": ...,
            "chapters": ...
        }}
        """
        try:
            response = await self.generate_text(prompt)

            # Strip the ```json and ``` from the response, use re
            json_string = re.search(r"\{[\s\S]*\}", response)

            #Extract json content or response as is
            if json_string:
                json_string = json_string.group(0)
            else:
                logger.error(f"String Not Json")
                return {}

            try:
                metadata = json.loads(json_string)
                return metadata

            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from Gemini response: {e}")
                return {}  # Handle the error

        except Exception as e:
            logger.exception(f"Error getting document metadata: {e}")
            return {}
    

    async def generate_qa(self, qa_prompt: PromptSchema) -> Optional[QAResponseSchema]:
        """
        Generates a question and answer pair using the Gemini model based on the provided prompt.

        Args:
            qa_prompt (PromptSchema): A PromptSchema object containing the prompt information.

        Returns:
            Optional[QAResponseSchema]: A QAResponseSchema object containing the question and answer, or None if an error occurs.
        """
        try:
            # Construct the full prompt from PromptSchema object
            full_prompt = qa_prompt.prompt

            # Generate text using the Gemini model
            llm_response = await self.generate_text(full_prompt)

            # Create a LLMResponseSchema object
            llm_response_schema = LLMResponseSchema(response=llm_response)

            # Parse the llm_response and create QAResponseSchema object
            qa_response = self.parse_qa_response(llm_response_schema)

            return qa_response

        except Exception as e:
            logger.exception(f"Error generating Q&A: {e}")
            return None


    def parse_qa_response(self, llm_response: LLMResponseSchema) -> Optional[QAResponseSchema]:
        """
        Parses the Gemini model response and extracts question and answer.

        Args:
            llm_response (LLMResponseSchema): An LLMResponseSchema object containing the LLM response.

        Returns:
            Optional[QAResponseSchema]: A QAResponseSchema object containing the parsed question and answer, or None if an error occurs.
        """
        try:
            # Basic parsing logic (improve as needed)
            response_text = llm_response.response
            parts = response_text.split("\n", 1)  # Split into question and answer

            if len(parts) == 2:
                question = parts[0].split(":", 1)[1].strip() if ":" in parts[0] else parts[0].strip()
                answer = parts[1].split(":", 1)[1].strip() if ":" in parts[1] else parts[1].strip()

                # Create a QAResponseSchema object
                qa_response = QAResponseSchema(question=question, answer=answer)
                return qa_response
            else:
                logger.warning(f"Could not parse Q&A from Gemini response: {response_text}")
                return None

        except ValidationError as e:
            logger.error(f"Pydantic validation error: {e}")
            return None
        except Exception as e:
            logger.exception(f"Error parsing Q&A: {e}")
            return None
