import os
import time
from typing import Dict, Optional, List
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content, ChatSession
import json
import pprint
# Assuming you have logging setup.  If not, replace with print statements.
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Or whatever level you prefer

# --- Global Variables (for caching) ---
_llm_cache: Dict[str, ChatSession] = {}  # Cache ChatSession instances
_last_access_time: Dict[str, float] = {}  # Track last access time
CACHE_TTL = 60  # Time-to-live for cache entries (seconds)


PROJECT_ID = os.environ['VERTEXAI_PROJECT_ID']
LOCATION = os.environ['VERTEXAI_LOCATION']


def _cleanup_cache():
    """Removes expired entries from the cache."""
    global _llm_cache, _last_access_time
    current_time = time.time()
    expired_keys = [
        key
        for key, last_access in _last_access_time.items()
        if current_time - last_access > CACHE_TTL
    ]
    for key in expired_keys:
        del _llm_cache[key]
        del _last_access_time[key]


def _get_cached_llm(token: str, model_name: str) -> ChatSession:
    """Retrieves or creates a cached ChatSession instance."""
    global _llm_cache, _last_access_time

    _cleanup_cache()

    if token in _llm_cache:
        _last_access_time[token] = time.time()
        print(f"Cached session found token:{token}")
        return _llm_cache[token]
    else:
        model = GenerativeModel(model_name)
        chat = model.start_chat()
        _llm_cache[token] = chat
        _last_access_time[token] = time.time()
        print(f"No Cached session found token:{token}")
        return chat

def load_prompt(prompt_path: str) -> str:
    try:
        #Simple prompt loading from a file 
        with open(prompt_path, 'r') as f:
            prompt = f.read()
        return prompt

    except FileNotFoundError:
        logger.warning(f"Prompt file not found: {prompt_path}")
        return "" 
    except Exception as e:
        logger.error(f"Error loading prompt: {e}")
        return ""

def dump_args(function_name, **kwargs):
    """Dummy dump args function. Replace with actual logging."""
    print(f"Function: {function_name}, Arguments: {kwargs}")


def dump_json_response(response):
    """Dummy dump json response function. Replace with actual logging."""
    print(f"Response: {response}")

class VertexAIConnector:  # Dummy connector for demonstration
    def __init__(self, model_name="gemini-2.0-pro-exp-02-05"):
        self.model_name = model_name

    def start_chat(self):
        model = GenerativeModel(self.model_name)
        return model.start_chat()
        
    def send_message(self, chat, message):
        response = chat.send_message(message)
        return response.text.strip()

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

class AIService: 
    def __init__(self, llm_provider="vertexai", model_name="gemini-2.0-pro-exp-02-05"):
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.llm_connector = VertexAIConnector(model_name=model_name) # Assuming this is how you initialize it.
        self.env = self  # Dummy for template loading

    def get_template(self, template_path):  #Dummy
      return template_path


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

            prompt = load_prompt(prompt_path)
            
            # Initialize the chat session - BYPASSING CACHE - always new session
            chat = vertexai_connector.start_chat()

            # Create the content parts
            contents = [
                Part.from_uri(document_uri, mime_type="application/pdf"),
                Part.from_text(prompt)
            ]

            # Combine system message and content for the LLM

            # Send the message to the chat session
            response = chat.send_message(Content(role="user", parts=contents))

            llm_output = response.text.strip()

            if not llm_output:
                logger.warning(f"Failed to extract details from document: {document_uri}")
                return None

            # Clean the LLM output
            llm_output = self.clean_llm_output(llm_output)

            # Parse the JSON output
            try:
                extracted_details = json.loads(llm_output)
                print(f"extracted_details...")
                print(extracted_details)
                print()
                print(json.dumps(extracted_details, sort_keys=True, indent=4))
                # logger.debug(f"Extracted details: {extracted_details}")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON: {e}\nLLM Output: {llm_output}")
                return None

            logger.info(f"Extracted details from document: {document_uri}")
            return extracted_details

        except Exception as e:
            logger.error(f"Error extracting document details: {e}")
            return None


def main():
    MODEL_NAME = "gemini-2.0-pro-exp-02-05"

    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # document_uri = "gs://bhagavan-pub-bucket/genai-resources/jemh101.pdf"
    document_uri = "gs://bhagavan-pub-bucket/aignite-resources/jemh1a2.pdf"
    prompt_path = "/home/bhagavan/dev/aignite/app/ai/prompts/extract_document_details_prompt.txt"
    prompt_path = "/home/bhagavan/dev/aignite/app/ai/prompts/02-prompt.txt"
    prompt_path = "/home/bhagavan/dev/aignite/app/ai/prompts/03-prompt.txt"

    doc_extractor = AIService()  

    extracted_details = doc_extractor.extract_document_details(document_uri, prompt_path)

    if extracted_details:
        print("Extracted Details:")
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(extracted_details)
        # dump_json_response(extracted_details)
    else:
        print("Failed to extract document details.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) #Configure basic logging
    main()