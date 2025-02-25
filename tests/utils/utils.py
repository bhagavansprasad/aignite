# utils.py
import json
import requests
import logging

# Configure basic logging (adjust level as needed)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)  # Get logger for this module


def read_config(config_file="config.json"):
    """
    Reads configuration from a JSON file.

    Args:
        config_file (str): Path to the config.json file.

    Returns:
        dict: The configuration dictionary, or None if there's an error.
    """
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        logger.debug(f"Successfully read config from {config_file}")
        return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_file}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {config_file}")
        return None


def make_post_request(url, data, headers):
    """
    Makes a POST request to the specified URL.

    Args:
        url (str): The URL to make the request to.
        data (dict): The data to send in the request body.
        headers (dict): The headers to send with the request.

    Returns:
        requests.Response: The response object, or None if there's an error.
    """
    try:
        logger.debug(f"Making POST request to {url} with data: {data} and headers: {headers}")
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses
        logger.debug(f"POST request successful. Status code: {response.status_code}")
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Error: {e}")
        return None
