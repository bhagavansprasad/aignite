import logging
from typing import Optional
import openai

logger = logging.getLogger("app")

class OpenAIConnector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        openai.api_key = self.api_key
        logger.info("Initialized OpenAI connector")

    def generate_text(self, prompt: str, max_output_tokens: int = 1024) -> Optional[str]:
        """
        Generates text using the OpenAI API.
        """
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",  # Or another suitable engine
                prompt=prompt,
                max_tokens=max_output_tokens,
                temperature=0.7,
                n=1,
                stop=None,
            )
            logger.debug(f"OpenAI response: {response.choices[0].text.strip()}")
            return response.choices[0].text.strip()
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {e}")
            return None

    def generate_text_from_image(self, prompt: str, image_uri: str, max_output_tokens: int = 1024) -> Optional[str]:
        logger.warning("OpenAI text-davinci-003 does not support image input.  Returning None.")
        return None