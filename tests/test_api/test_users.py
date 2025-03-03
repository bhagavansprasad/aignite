import pytest
import requests
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from typing import Dict
from app.api.users import router as api_router  # Corrected import
import os

from app.core.config import settings 
TEST_DATABASE_URL = settings.TEST_DATABASE_URL
SERVER_URL = settings.SERVER_URL

# Client for making requests to the test app
app = FastAPI()
app.include_router(api_router, prefix="/users")  # Add prefix
client = TestClient(app)

# Test data
BASE_URL = SERVER_URL + "/users"  # Ensure the base URL includes the prefix
test_data = {
    "valid": {
        "full_name": "Valid Test",
        "email": "bhagavan",
        "mobile_no": "5551234567",
        "password": "jnjnuh"
    },
    "invalid_email": {
        "full_name": "Invalid Email",
        "email": "invalid_email",
        "mobile_no": "5551234567",
        "password": "secure_password"
    },
    "invalid_mobile": {
        "full_name": "Invalid Mobile",
        "email": "valid2@example.com",
        "mobile_no": "short",
        "password": "secure_password"
    },
    "missing_field": {
        "email": "valid3@example.com",
        "mobile_no": "5551234567",
        "password": "secure_password"  # Missing full_name
    },
    "sql_injection": {
        "full_name": "'; DROP TABLE users;--",  # SQL Injection name, and is usually handled by DB
        "email": "valid_sql@example.com",
        "mobile_no": "5551234567",
        "password": "secure_password"
    }
}

# Helper function to get a token (replace with your actual token retrieval mechanism)
def get_token(role: str) -> str:
    """
    Replace this with your actual token retrieval logic.  This is a placeholder.
    In a real application, you'd likely call an authentication endpoint
    to get a JWT token for a specific user/role.
    """
    # This is a dummy implementation - NEVER hardcode tokens in real code!
    if role == "detailed_list_users":
        return "detailed_list_users_token"
    elif role == "list_user_roles":
        return "list_user_roles_token"
    elif role == "list_users":
        return "list_users_token"
    elif role == "create_user":
        return "create_user_token"
    else:
        return "invalid_token"  # Or handle the case where the role is unknown

# Fixture to create a test database - this is only used for the API itself
@pytest.fixture()
def setup_test_db():
    """Sets up a clean test database before each test function."""
    yield  # The API needs the test database to exist, but the tests don't use it directly

# Test to create a valid user
def test_create_valid_user(setup_test_db):
    """Test the POST /users/ endpoint with valid data."""
    headers = {"Authorization": f"Bearer {get_token('create_user')}"}  # Add token
    response = client.post(f"{BASE_URL}/", json=test_data["valid"], headers=headers)
    assert response.status_code == 200, response.text
    created_user = response.json()
    assert created_user["email"] == test_data["valid"]["email"]
    assert created_user["full_name"] == test_data["valid"]["full_name"]
    global created_user_email
    created_user_email = created_user["email"] # Store the user email for listing user tests

# Test to handle creation of user with an invalid email
def test_create_invalid_email(setup_test_db):
    """Test the POST /users/ endpoint with invalid email data."""
    headers = {"Authorization": f"Bearer {get_token('create_user')}"}  # Add token
    response = client.post(f"{BASE_URL}/", json=test_data["invalid_email"], headers=headers)
    assert response.status_code == 400  # Expecting error response for invalid data

# Test to handle creation of user with an invalid mobile number
def test_create_invalid_mobile(setup_test_db):
    """Test the POST /users/ endpoint with invalid mobile data."""
    headers = {"Authorization": f"Bearer {get_token('create_user')}"}  # Add token
    response = client.post(f"{BASE_URL}/", json=test_data["invalid_mobile"], headers=headers)
    assert response.status_code == 400  # Expecting error response for invalid data

# Test to get a detailed list of users
def test_read_users_detailed(setup_test_db):
    """Test the GET /users/detailed endpoint."""
    headers = {"Authorization": f"Bearer {get_token('detailed_list_users')}"}  # Add token
    response = client.get(f"{BASE_URL}/detailed", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    #Add check to make sure email that was created is present
    user_emails = [user["email"] for user in data]
    assert created_user_email in user_emails

# Test to get a list of users with roles
def test_read_user_roles(setup_test_db):
    """Test the GET /users/user_roles endpoint."""
    headers = {"Authorization": f"Bearer {get_token('list_user_roles')}"}  # Add token
    response = client.get(f"{BASE_URL}/user_roles", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

# Test to get a basic list of users
def test_read_users_basic(setup_test_db):
    """Test the GET /users/ endpoint to list users (basic info)."""
    headers = {"Authorization": f"Bearer {get_token('list_users')}"}  # Add token
    response = client.get(f"{BASE_URL}/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

# Test to create a user without proper roles
def test_create_user_no_roles(setup_test_db):
    """Test the POST /users/ endpoint to list users (basic info)."""
    headers = {"Authorization": f"Bearer {get_token('invalid')}"}  # Add token
    response = client.post(f"{BASE_URL}/", json=test_data["valid"], headers=headers)
    assert response.status_code == 403