import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from typing import Dict
from app.api.router import api_router  # Corrected import
from app.core.config import settings  # Import settings
import os
import json


# Create a FastAPI app instance for testing
app = FastAPI()
app.include_router(api_router, prefix="/api")  # Add prefix
client = TestClient(app)

# Test data
BASE_URL = settings.SERVER_URL + "/api/users"  # Use settings.SERVER_URL
LOGIN_URL = "/api/auth/login"

# Define users and their roles
USERS = {
    "user1": {"username": "user1", "password": "jnjnuh", "role": "1"},
    "user2": {"username": "user2", "password": "jnjnuh", "role": "2"},
    "user3": {"username": "user3", "password": "jnjnuh", "role": "3"},
}

# Helper function to get a token for a given user
def get_token(username, password):
    """Logs in a user and returns the access token."""
    data = {"username": username, "password": password}
    response = client.post(LOGIN_URL, data=data)
    assert response.status_code == 200
    return response.json()["access_token"]

#  Test cases for detailed_list_users endpoint
def test_detailed_list_users_admin_success():
    """Test successful access to detailed_list_users with ADMIN role."""
    access_token = get_token(USERS["user1"]["username"], USERS["user1"]["password"])
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"{BASE_URL}/detailed?skip=0&limit=100", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_detailed_list_users_non_admin_failure():
    """Test access to detailed_list_users with non-ADMIN roles (expecting failure)."""
    access_token = get_token(USERS["user2"]["username"], USERS["user2"]["password"]) # Using TEACHER role
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"{BASE_URL}/detailed?skip=0&limit=100", headers=headers)

    # Expecting 403 Forbidden as only ADMIN role is allowed
    assert response.status_code == 403

# Test cases for list_user_roles endpoint
def test_list_user_roles_admin_success():
    """Test successful access to list_user_roles with ADMIN role."""
    access_token = get_token(USERS["user1"]["username"], USERS["user1"]["password"])
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"{BASE_URL}/user_roles?skip=0&limit=100", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_user_roles_teacher_success():
    """Test successful access to list_user_roles with TEACHER role."""
    access_token = get_token(USERS["user2"]["username"], USERS["user2"]["password"])
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"{BASE_URL}/user_roles?skip=0&limit=100", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_user_roles_student_failure():
    """Test access to list_user_roles with STUDENT role (expecting failure)."""
    access_token = get_token(USERS["user3"]["username"], USERS["user3"]["password"])
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"{BASE_URL}/user_roles?skip=0&limit=100", headers=headers)

    # Expecting 403 Forbidden as STUDENT role is not allowed
    assert response.status_code == 403


def test_list_users_admin_success():
    """Test successful access to list_users with ADMIN role."""
    access_token = get_token(USERS["user1"]["username"], USERS["user1"]["password"])
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"{BASE_URL}/?skip=0&limit=100", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_users_teacher_success():
    """Test successful access to list_users with TEACHER role."""
    access_token = get_token(USERS["user2"]["username"], USERS["user2"]["password"])
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"{BASE_URL}/?skip=0&limit=100", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_users_student_success():
    """Test successful access to list_users with STUDENT role."""
    access_token = get_token(USERS["user3"]["username"], USERS["user3"]["password"])
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"{BASE_URL}/?skip=0&limit=100", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)
@pytest.mark.skip
def test_create_user_admin_success():
    """Test successful user creation with ADMIN role."""
    access_token = get_token(USERS["user1"]["username"], USERS["user1"]["password"])
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}  # Set content type

    user_data = {
        "full_name": "New User",
        "email": "newuser@example.com",
        "mobile_no": "1234567890",
        "password": "securepassword"
    }
    response = client.post(f"{BASE_URL}/", headers=headers, data=json.dumps(user_data))

    assert response.status_code == 200
    assert response.json()["email"] == "newuser@example.com"  # Verify user was created

@pytest.mark.skip
def test_create_user_non_admin_failure():
    """Test user creation with non-ADMIN roles (expecting failure)."""
    access_token = get_token(USERS["user2"]["username"], USERS["user2"]["password"])  # TEACHER role
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}  # Set content type

    user_data = {
        "full_name": "Attempted User",
        "email": "attempt@example.com",
        "mobile_no": "0987654321",
        "password": "somepassword"
    }
    response = client.post(f"{BASE_URL}/", headers=headers, data=json.dumps(user_data))

    # Expecting 403 Forbidden as only ADMIN role is allowed
    assert response.status_code == 403
