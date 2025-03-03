import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from app.api.router import api_router
from app.core.config import settings
import os

# Create a FastAPI app instance for testing
app = FastAPI()
# Include the routers
app.include_router(api_router, prefix="/api")

# Create a TestClient for making requests
client = TestClient(app)

# Test data
LOGIN_URL = "/api/auth/login"
# (username, password, expected_role)
TEST_USERS = [
    ("user1", "jnjnuh", "ADMIN"),
    ("user2", "jnjnuh", "TEACHER"),
    ("user3", "jnjnuh", "STUDENT"),
]
INVALID_USERNAME = "invalid_user"
INVALID_PASSWORD = "invalid_password"

@pytest.mark.parametrize("username, password, expected_role", TEST_USERS)
def test_valid_login(username: str, password: str, expected_role: str):
    """Test successful login with valid credentials for different users."""
    data = {"username": username, "password": password}
    response = client.post(LOGIN_URL, data=data)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "role" in response.json()
    assert "user_full_name" in response.json()
    assert response.json()["token_type"] == "bearer"
    assert response.json()["role"] == expected_role

def test_invalid_username_login():
    """Test login with an invalid username."""
    data = {"username": INVALID_USERNAME, "password": "jnjnuh"}
    response = client.post(LOGIN_URL, data=data)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_invalid_password_login():
    """Test login with a valid username but an invalid password."""
    data = {"username": "user1@example.com", "password": INVALID_PASSWORD}
    response = client.post(LOGIN_URL, data=data)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_missing_username_login():
    """Test login with a missing username."""
    data = {"password": "jnjnuh"}
    response = client.post(LOGIN_URL, data=data)

    assert response.status_code == 422  # Unprocessable Entity (validation error)
    # Check for specific error message indicating username is missing
    assert "username" in response.json()["detail"][0]["loc"] # or other relevant validation error

def test_missing_password_login():
    """Test login with a missing password."""
    data = {"username": "user1@example.com"}
    response = client.post(LOGIN_URL, data=data)

    assert response.status_code == 422  # Unprocessable Entity (validation error)
    # Check for specific error message indicating password is missing
    assert "password" in response.json()["detail"][0]["loc"] # or other relevant validation error