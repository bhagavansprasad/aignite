# app/ai/llm_connectors/huggingface_connector.py

import logging
from typing import Optional
from transformers import pipeline

logger = logging.getLogger("app")

class HuggingFaceConnector:
    def __init__(self, api_key: str = None, model_name: str = "google/flan-t5-base"): #API key is not used, but kept for consistency
        self.api_key = api_key
        self.model_name = model_name
        try:
            self.generator = pipeline("text-generation", model=self.model_name)
            logger.info(f"Initialized Hugging Face connector with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error initializing Hugging Face pipeline: {e}")
            raise

    def generate_text(self, prompt: str, max_output_tokens: int = 1024) -> Optional[str]:
        """
        Generates text using the Hugging Face pipeline.
        """
        try:
            response = self.generator(prompt, max_length=max_output_tokens)
            logger.debug(f"Hugging Face response: {response[0]['generated_text']}")
            return response[0]["generated_text"]
        except Exception as e:
            logger.error(f"Error generating text with Hugging Face: {e}")
            return None

    def generate_text_from_image(self, prompt: str, image_uri: str, max_output_tokens: int = 1024) -> Optional[str]:
        logger.warning("HuggingFace does not support image input.  Returning None.")
        return None