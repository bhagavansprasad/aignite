# app/ai/llm_connectors/vertexai_connector.py

import logging
from typing import Optional

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
except ImportError:
    print("Please install vertexai and google-cloud-aiplatform")

logger = logging.getLogger("app")

class VertexAIConnector:
    def __init__(self, project_id: str, location: str, model_name: str = "gemini-1.5-pro-002"):
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        try:
            vertexai.init(project=self.project_id, location=self.location)
            self.model = GenerativeModel(self.model_name)
            logger.info(f"Initialized VertexAI connector with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error initializing VertexAI: {e}")
            raise

    def generate_text(self, prompt: str, max_output_tokens: int = 1024) -> Optional[str]:
        """
        Sends a prompt to the Gemini model and returns the generated text.
        """
        try:
            response = self.model.generate_content(prompt, generation_config={"max_output_tokens": max_output_tokens})
            # logger.debug(f"Gemini response: {response.text}")
            return response.text
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {e}")
            return None

    def generate_text_from_image(self, prompt: str, image_uri: str, max_output_tokens: int = 1024) -> Optional[str]:
        """
        Sends a prompt and an image URI to the Gemini model and returns the generated text.
        """
        try:
            from google.cloud import storage

            storage_client = storage.Client()
            bucket_name = image_uri.split('/')[2]
            blob_name = '/'.join(image_uri.split('/')[3:])
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            image_bytes = blob.download_as_bytes()

            img = Part.from_data(image_bytes, mime_type="image/jpeg")

            response = self.model.generate_content([prompt, img], generation_config={"max_output_tokens": max_output_tokens})
            logger.debug(f"Gemini response: {response.text}")
            return response.text
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {e}")
            return None
