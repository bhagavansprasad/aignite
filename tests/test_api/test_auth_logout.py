import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from app.api.router import api_router
from app.api.auth import auth_router
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
LOGOUT_URL = "/api/auth/logout"
VALID_USERNAME = "bhagavan"  # Replace with a valid username from your test database
VALID_PASSWORD = "jnjnuh"  # Replace with the corresponding password

def get_access_token():
    """Helper function to login and get an access token."""
    data = {"username": VALID_USERNAME, "password": VALID_PASSWORD}
    response = client.post(LOGIN_URL, data=data)
    assert response.status_code == 200
    return response.json()["access_token"]

def test_valid_logout():
    """Test successful logout with a valid access token."""
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post(LOGOUT_URL, headers=headers)

    assert response.status_code == 200
    assert response.json() == {"message": "Successfully logged out"}

    # Verify that the token is no longer valid (optional)
    # This requires a protected endpoint to test against.
    # Example (assuming you have a /users/me endpoint):
    # response = client.get("/api/users/me", headers=headers)
    # assert response.status_code == 401  # Or 403, depending on your auth setup

def test_logout_without_token():
    """Test logout without providing an access token."""
    response = client.post(LOGOUT_URL)

    # Expecting 401 Unauthorized because the endpoint requires a valid token
    assert response.status_code == 401 # Or 403, depending on your auth setup