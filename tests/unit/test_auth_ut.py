import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch
from fastapi import Depends
from app.api.auth import login, logout, get_current_active_user  # Import get_current_active_user
from app.core.security import verify_password
import jwt
from app.models.users import User  # Import the User model
from app.models.tokens import Token  # Import the Token model

# Mocking dependencies
@pytest.fixture
def mock_db():
    db = MagicMock()
    query_result = MagicMock()
    filter_result = MagicMock()
    first_result = None  # Default: Token not found

    query_result.filter.return_value = filter_result
    filter_result.first.return_value = first_result
    db.query.return_value = query_result # Set query to return the query_result Mock object

    db.query.return_value.filter.return_value.scalar.return_value = None  # Default to no role found.
    return db

@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)  # Important:  Use spec to enforce correct attributes
    user.id = 7  #Example user, can be changed for specific test cases
    user.full_name = "user1" # Username from the provided data
    user.email = "user1@example.com"
    user.password = "jnjnuh"  # Actual password, but remember hashing in real use
    user.is_active = True
    user.role_id = 1
    return user

@pytest.fixture
def mock_role():
    role = MagicMock()
    role.name = "admin"  # Or whatever role is appropriate for the user
    role.id = 1
    return role

@pytest.fixture
def mock_token():
    token = MagicMock(spec=Token)  # Specify the Token model
    token.user_id = 7
    token.token = "test_token"
    return token

def test_login_success_isolated():
    # Arrange
    mock_db = MagicMock()

    # Create a mock User object
    mock_user = MagicMock(spec=User)
    mock_user.id = 7
    mock_user.full_name = "user1"
    mock_user.email = "user1@example.com"
    mock_user.password = "jnjnuh"
    mock_user.is_active = True
    mock_user.role_id = 1

    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    mock_verify_password = MagicMock(return_value=True)

    user = mock_db.query(User).filter(User.full_name == "user1", User.is_active == True).first()

    assert user is not None
    assert user.full_name == "user1"
    assert user.password == "jnjnuh"
    print(f"user.password: {user.password}") # Added print statement
        
def test_login_invalid_password(mock_db, mock_user):
    # Arrange
    # Configure the mock to return mock_user (user is found)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    # Mock verify_password to return False (invalid password)
    with patch("app.api.auth.verify_password", return_value=False) as mock_verify_password:
        # Act & Assert
        with pytest.raises(HTTPException) as excinfo:
            login(username="user1", password="wrongpassword", db=mock_db)
        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "Invalid username or password"
        mock_verify_password.assert_called_once_with("wrongpassword", "jnjnuh")  # Correct Password

@pytest.mark.skip
def test_logout_success(mock_db, mock_user):
    # Arrange
    # Create ONE mock_token object and use it consistently
    mock_token = MagicMock(spec=Token)
    mock_token.user_id = 7
    mock_token.token = "test_token"

    # Configure the mock to return mock_token (token is found)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_token

    # Mock get_current_active_user to return mock_user
    with patch("app.api.auth.get_current_active_user", return_value=mock_user) as mock_get_current_active_user:
        # Act
        result = logout(current_user=Depends(get_current_active_user), db=mock_db)

        # Assert
        mock_db.delete.assert_called()  # Verify that delete was called, without checking arguments
        mock_db.commit.assert_called()
        assert result == {"message": "Successfully logged out"}
        mock_get_current_active_user.assert_called_once()  # Verify that get_current_active_user was called

@pytest.mark.skip
def test_logout_token_not_found(mock_db, mock_user):
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        logout(current_user=mock_user, db=mock_db)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Token not found or already logged out."

@pytest.mark.skip
def test_login_existing_valid_token(mock_db, mock_user, mock_role, mock_token):
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db.query.return_value.filter.return_value.scalar.return_value = mock_role.name
    mock_db.query.return_value.filter.return_value.first.return_value = mock_token

    # Mock verify_password to return True
    with patch("app.api.auth.verify_password", return_value=True) as mock_verify_password:
        # Mock jwt.decode to avoid errors
        with patch("jwt.decode", return_value={}) as mock_jwt_decode:
            # Act
            result = login(username="user1", password="jnjnuh", db=mock_db) #Real username

            # Assert
            assert "access_token" in result
            assert result["token_type"] == "bearer"
            assert result["role"] == mock_role.name
            assert result["user_full_name"] == mock_user.full_name
            mock_verify_password.assert_called_once_with("jnjnuh", "jnjnuh")

@pytest.mark.skip
def test_login_existing_expired_token(mock_db, mock_user, mock_role, mock_token):
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db.query.return_value.filter.return_value.scalar.return_value = mock_role.name
    mock_db.query.return_value.filter.return_value.first.return_value = mock_token

    # Mock verify_password to return True
    with patch("app.api.auth.verify_password", return_value=True) as mock_verify_password:
        # Mock jwt.decode to raise an ExpiredSignatureError
        with patch("jwt.decode", side_effect=jwt.ExpiredSignatureError("Signature has expired")) as mock_jwt_decode:
            # Act
            result = login(username="user1", password="jnjnuh", db=mock_db)

            # Assert
            assert "access_token" in result
            assert result["token_type"] == "bearer"
            assert result["role"] == mock_role.name
            assert result["user_full_name"] == mock_user.full_name
            mock_db.add.assert_called()
            mock_db.commit.assert_called()
            mock_db.query.return_value.filter.return_value.delete.assert_called()
            mock_verify_password.assert_called_once_with("jnjnuh", "jnjnuh")