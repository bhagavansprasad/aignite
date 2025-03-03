import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from app.api.router import api_router  # Import the combined router
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
VALID_USERNAME = "bhagavan"  # Replace with a valid username from your test database
VALID_PASSWORD = "jnjnuh"  # Replace with the corresponding password
INVALID_USERNAME = "invalid_user"
INVALID_PASSWORD = "invalid_password"

def test_valid_login():
    """Test successful login with valid credentials."""
    data = {"username": VALID_USERNAME, "password": VALID_PASSWORD}
    response = client.post(LOGIN_URL, data=data)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "role" in response.json()
    assert "user_full_name" in response.json()
    assert response.json()["token_type"] == "bearer"
    # You may want to further decode the token and validate its contents

def test_invalid_username_login():
    """Test login with an invalid username."""
    data = {"username": INVALID_USERNAME, "password": VALID_PASSWORD}
    response = client.post(LOGIN_URL, data=data)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_invalid_password_login():
    """Test login with a valid username but an invalid password."""
    data = {"username": VALID_USERNAME, "password": INVALID_PASSWORD}
    response = client.post(LOGIN_URL, data=data)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_missing_username_login():
    """Test login with a missing username."""
    data = {"password": VALID_PASSWORD}
    response = client.post(LOGIN_URL, data=data)

    assert response.status_code == 422  # Unprocessable Entity (validation error)
    # Check for specific error message indicating username is missing
    assert "username" in response.json()["detail"][0]["loc"] # or other relevant validation error

def test_missing_password_login():
    """Test login with a missing password."""
    data = {"username": VALID_USERNAME}
    response = client.post(LOGIN_URL, data=data)

    assert response.status_code == 422  # Unprocessable Entity (validation error)
    # Check for specific error message indicating password is missing
    assert "password" in response.json()["detail"][0]["loc"] # or other relevant validation error
    