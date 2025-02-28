import logging
from typing import Optional

logger = logging.getLogger("app")

class CohereConnector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        logger.info("Initialized Cohere connector")

    def generate_text(self, prompt: str, max_output_tokens: int = 1024) -> Optional[str]:
        """
        Generates text using the Cohere API.
        """
        try:
            import cohere
            co = cohere.Client(self.api_key)
            response = co.generate(
                prompt=prompt,
                max_tokens=max_output_tokens,
                model="command", # Specify the model
            )
            logger.debug(f"Cohere response: {response.generations[0].text}")
            return response.generations[0].text
        except Exception as e:
            logger.error(f"Error generating text with Cohere: {e}")
            return None

    def generate_text_from_image(self, prompt: str, image_uri: str, max_output_tokens: int = 1024) -> Optional[str]:
        logger.warning("Cohere does not support image input.  Returning None.")
        return None
    