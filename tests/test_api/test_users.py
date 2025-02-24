# tests/test_api/test_users.py

import pytest
import requests
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator

from app.core.config import TEST_DATABASE_URL # test URL is pulled
from app.models.base import Base
from app.models import user as user_model
from app.database_drivers.postgres_driver import PostgresDriver, get_db
from app import schemas
from app.core import security
from app.services import user_service
from app.api import router as api_router
import os

# Define base URL
BASE_URL = "http://localhost:8000"

# Client for making requests to the test app
app = FastAPI()
app.include_router(api_router)

# Create a database engine for testing
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)

# Dependency to get the testing database session
def override_get_db() -> Generator:
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

app.dependency_overrides[get_db] = override_get_db

from fastapi.testclient import TestClient
client = TestClient(app)

# Test data
test_data = {
    "valid": {
        "full_name": "Valid Test",
        "email": "valid@example.com",
        "mobile_no": "5551234567",
        "password": "secure_password"
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
        "password": "secure_password" # Missing full_name
    },
    "sql_injection": {
        "full_name": "'; DROP TABLE users;--", # SQL Injection name, and is usually handled by DB
        "email": "valid_sql@example.com",
        "mobile_no": "5551234567",
        "password": "secure_password"
    }
}

@pytest.fixture() # autouse=True scope="session"
def setup_test_db():
    """Sets up a clean test database before each test function."""
    # engine = create_engine(testURL)
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield

def test_read_users(setup_test_db):
    """Test the GET /users/ endpoint."""
    response = client.get(f"{BASE_URL}/users/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) # checking for JSON list

def test_create_valid_user(setup_test_db):
    """Test the POST /users/ endpoint with valid data."""
    response = client.post(f"{BASE_URL}/users/", json=test_data["valid"])
    assert response.status_code == 200, response.text
    created_user = response.json()
    assert created_user["email"] == test_data["valid"]["email"]
    assert created_user["full_name"] == test_data["valid"]["full_name"]

    # Test with DB credentials and make sure they are valid and safe.

def test_create_invalid_email(setup_test_db):
    """Test the POST /users/ endpoint with invalid email data."""
    response = client.post(f"{BASE_URL}/users/", json=test_data["invalid_email"])
    assert response.status_code == 400 # Checking for a general response code

def test_create_invalid_mobile(setup_test_db):
    """Test the POST /users/ endpoint with invalid mobile data."""
    response = client.post(f"{BASE_URL}/users/", json=test_data["invalid_mobile"])
    assert response.status_code == 400 # Checking for a general response code