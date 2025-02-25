# get_token.py
from utils import read_config, make_post_request
import logging
import json

# Configure basic logging (adjust level as needed)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)  # Get logger for this module


def get_token_from_login(config_file="config.json"):
    """
    Logs in to the API, retrieves the access token, and returns it.

    Args:
        config_file (str): Path to the config.json file.

    Returns:
        str: The access token, or None if login fails.
    """

    config = read_config(config_file)

    if not config:
        return None

    server_url = config.get("server_url")
    username = config.get("username")
    password = config.get("password")

    if not server_url or not username or not password:
        logger.error("Missing server_url, username, or password in config.json")
        return None

    login_url = f"{server_url}/auth/login"

    data = {
        "username": username,
        "password": password
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = make_post_request(login_url, data, headers)

    if not response:
        return None

    try:
        response_json = response.json()
        access_token = response_json.get("access_token")  # Adjust based on your API's response
        token_type = response_json.get("token_type")      #  Assuming you are sending bearer

        if access_token:
            if token_type == "bearer":
                logger.info(f"{username}, Login Successfull, retrieved bearer token.")
                return f"{token_type} {access_token}"
            else:
                logger.info("Successfully retrieved token (non-bearer).")
                return access_token
        else:
            logger.error("Access token not found in response.")
            logger.debug(f"Response: {response_json}")
            return None

    except json.JSONDecodeError:
        logger.error("Could not decode JSON response.")
        return None


if __name__ == "__main__":
    access_token = get_token_from_login()

    if access_token:
        # print(f"login successful, token...")
        print(access_token.strip().strip('barer').strip())
    else:
        print("Failed to retrieve access token.")
