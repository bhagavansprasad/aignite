# app/ai/ai_service.py

import logging
from app.ai.llm_connectors.openai_connector import OpenAIConnector
from app.ai.llm_connectors.cohere_connector import CohereConnector
from app.ai.llm_connectors.huggingface_connector import HuggingFaceConnector
from app.ai.llm_connectors.vertexai_connector import VertexAIConnector
from jinja2 import Environment, FileSystemLoader
from typing import Optional, Dict, List
import json
from vertexai.generative_models import Part
from vertexai.generative_models import Content

logger = logging.getLogger("app")

class AIService:
    def __init__(self, config: dict):
        self.config = config
        self.llm_provider = config.get("llm_provider", "openai")
        self.openai_config = config.get("openai", {})
        self.cohere_config = config.get("cohere", {})
        self.huggingface_config = config.get("huggingface", {})
        self.vertexai_config = config.get("vertexai", {})  # Get Vertex AI config

        self.llm_connector = self._create_llm_connector()

        # Initialize Jinja2 environment for prompt templating
        self.env = Environment(loader=FileSystemLoader("app/ai/prompts"))

    def _create_llm_connector(self):
        if self.llm_provider == "openai":
            return OpenAIConnector(**self.openai_config)
        elif self.llm_provider == "cohere":
            return CohereConnector(**self.cohere_config)
        elif self.llm_provider == "huggingface":
            return HuggingFaceConnector(**self.huggingface_config)
        elif self.llm_provider == "vertexai":
            return VertexAIConnector(**self.vertexai_config)  # Create Vertex AI connector
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    def generate_text(self, prompt: str, max_output_tokens: int = 1024) -> Optional[str]:
        """
        Generates text using the configured LLM connector.
        """
        return self.llm_connector.generate_text(prompt, max_output_tokens)

    def extract_document_details(self, document_uri: str, prompt_path: str = None) -> Optional[dict]:
        """
        Extracts document details using the Gemini model, a base prompt template, and an optional supplemental prompt template in a chat session.
        """
        try:
            # Get the VertexAI Connector
            if self.llm_provider != "vertexai":
                logger.error("extract_document_details with chat requires vertexai llm provider")
                return None

            vertexai_connector = self.llm_connector
            if not isinstance(vertexai_connector, VertexAIConnector):
                logger.error("Invalid llm connector type, VertexAIConnector required")
                return None

            # Load the base prompt template
            template = self.env.get_template("extract_document_details_prompt.txt")
            base_prompt = template.render(document_uri=document_uri)

            # Initialize the chat session
            chat = vertexai_connector.model.start_chat()

            contents = [
                Part.from_uri(document_uri, mime_type="application/pdf"),
                Part.from_text(base_prompt)
            ]

            # Send the message to the chat session
            response = chat.send_message(Content(role="user", parts=contents))

            llm_output = response.text.strip()

            if not llm_output:
                logger.warning(f"Failed to extract details from document: {document_uri}")
                return None

            llm_output = self.clean_llm_output(llm_output)

            try:
                extracted_details = json.loads(llm_output)
                # logger.debug(json.dumps(extracted_details, sort_keys=True, indent=4))
                logger.debug(f"Extracted details: {llm_output}")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON: {e}\nLLM Output: {llm_output}")
                return None

            logger.info(f"Extracted details from document: {document_uri}")
            return extracted_details

        except Exception as e:
            logger.error(f"Error extracting document details: {e}")
            return None

    def generate_text_from_image(self, prompt: str, image_uri: str, max_output_tokens: int = 1024) -> Optional[str]:
        """
        Generates text using the configured LLM connector.
        """
        return self.llm_connector.generate_text_from_image(prompt, image_uri, max_output_tokens)

    def clean_llm_output(self, llm_output: str) -> str:
        """
        Cleans the LLM output by removing any leading/trailing whitespace and ```json blocks.
        """
        llm_output = llm_output.strip()
        # Remove ```json and ``` if present
        if llm_output.startswith("```json"):
            llm_output = llm_output[len("```json"):].strip()
        if llm_output.endswith("```"):
            llm_output = llm_output[:-len("```")].strip()
        return llm_output
    