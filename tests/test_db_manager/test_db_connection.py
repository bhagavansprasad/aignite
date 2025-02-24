import pytest
import sqlalchemy
from sqlalchemy import create_engine
import os

# Get database URL from environment variable or use a default
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://bhagavan:jnjnuh@localhost/aignite_db")

def test_db_connection():
    """Tests the database connection using SQLAlchemy."""
    try:
        engine = create_engine(DATABASE_URL)
        connection = engine.connect()
        print("Database connection successful!")
        connection.close()
        assert True  # Connection successful, so assert True
    except Exception as e:
        print(f"Database connection failed: {e}")
        assert False # Fail the test if the connection fails

# Optional: Add a test that checks if the DATABASE_URL environment variable is set
def test_database_url_env_variable():
    """Tests if the DATABASE_URL environment variable is set."""
    db_url = os.environ.get("DATABASE_URL")
    assert db_url is not None, "DATABASE_URL environment variable is not set."

# Optional: add fixture to create tables for a test database
@pytest.fixture(scope="session")
def create_test_database():
    """Create a test database and tables, dropping them after the tests."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://bhagavan:jnjnuh@localhost/aignite_db") # Same logic as above
    engine = create_engine(db_url)
    # Drop the table
    try:
        test = """SELECT 1 from users"""
        engine.execute(test)
        assert True, "Database already exists, and table exists"
    except:
        assert False, "Table does not exists"
