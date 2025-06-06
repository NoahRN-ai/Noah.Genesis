import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials

# Module to test
from backend.app.core import security
from backend.app.core.security import get_current_user, initialize_firebase_admin, UserInfo, UserRole
from backend.app.core.config import Settings # To mock settings if needed

# --- Fixtures ---

@pytest.fixture(autouse=True)
def reset_firebase_app_state(mocker):
    """Ensures _firebase_app_initialized is reset for relevant tests,
       and Firebase app is cleared if it was initialized by a previous test run in the same session."""
    mocker.patch.object(security, '_firebase_app_initialized', False)
    # If firebase_admin.get_app() doesn't raise, it means an app exists. Delete it.
    try:
        default_app = firebase_admin.get_app()
        firebase_admin.delete_app(default_app)
    except ValueError: # No app exists, which is fine.
        pass


@pytest.fixture
def mock_verify_id_token(mocker):
    return mocker.patch('firebase_admin.auth.verify_id_token')

@pytest.fixture
def mock_firebase_creds_cert(mocker):
    return mocker.patch('firebase_admin.credentials.Certificate')

@pytest.fixture
def mock_firebase_initialize_app(mocker):
    # This mock will allow us to see if initialize_app was called,
    # and also to simulate it raising an error.
    return mocker.patch('firebase_admin.initialize_app')

@pytest.fixture
def mock_security_settings(mocker):
    mock_settings = Settings(FIREBASE_SERVICE_ACCOUNT_JSON_PATH=None) # Default to no path
    return mocker.patch('backend.app.core.security.settings', mock_settings)

# --- Tests for initialize_firebase_admin ---

def test_initialize_firebase_admin_with_service_account_path_success(
    mock_security_settings, mock_firebase_creds_cert, mock_firebase_initialize_app, reset_firebase_app_state
):
    dummy_path = "/path/to/serviceAccount.json"
    mock_security_settings.FIREBASE_SERVICE_ACCOUNT_JSON_PATH = dummy_path

    initialize_firebase_admin()

    mock_firebase_creds_cert.assert_called_once_with(dummy_path)
    mock_firebase_initialize_app.assert_called_once_with(mock_firebase_creds_cert.return_value)
    assert security._firebase_app_initialized is True

def test_initialize_firebase_admin_default_credentials_success(
    mock_security_settings, mock_firebase_initialize_app, reset_firebase_app_state
):
    mock_security_settings.FIREBASE_SERVICE_ACCOUNT_JSON_PATH = None # Ensure it's None

    initialize_firebase_admin()

    # initialize_app called without specific credentials argument
    mock_firebase_initialize_app.assert_called_once_with(None)
    assert security._firebase_app_initialized is True

def test_initialize_firebase_admin_initialization_fails(
    mock_security_settings, mock_firebase_initialize_app, reset_firebase_app_state, caplog
):
    mock_firebase_initialize_app.side_effect = Exception("Firebase init failed")

    initialize_firebase_admin()

    assert security._firebase_app_initialized is False
    assert "Failed to initialize Firebase Admin SDK: Firebase init failed" in caplog.text

def test_initialize_firebase_admin_already_initialized(
    mock_security_settings, mock_firebase_initialize_app, reset_firebase_app_state
):
    # First initialization
    initialize_firebase_admin()
    assert security._firebase_app_initialized is True
    mock_firebase_initialize_app.assert_called_once() # Called once

    # Reset call count for the next check
    mock_firebase_initialize_app.reset_mock()

    # Attempt to initialize again
    initialize_firebase_admin()
    assert security._firebase_app_initialized is True # Still true
    mock_firebase_initialize_app.assert_not_called() # Not called again


# --- Tests for get_current_user ---

@pytest.fixture
def ensure_firebase_is_initialized_for_get_user(mocker):
    """Fixture to ensure _firebase_app_initialized is True for get_current_user tests."""
    mocker.patch.object(security, '_firebase_app_initialized', True)


@pytest.mark.asyncio
async def test_get_current_user_success(mock_verify_id_token, ensure_firebase_is_initialized_for_get_user):
    decoded_token = {
        "uid": "test_uid_123",
        "email": "user@example.com",
        "role": "patient" # Custom claim
    }
    mock_verify_id_token.return_value = decoded_token
    mock_auth_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dummy_token")

    user_info = await get_current_user(mock_auth_creds)

    assert isinstance(user_info, UserInfo)
    assert user_info.user_id == "test_uid_123"
    assert user_info.email == "user@example.com"
    assert user_info.role == UserRole.PATIENT
    assert user_info.disabled is False # Default

@pytest.mark.asyncio
async def test_get_current_user_success_no_role_claim(mock_verify_id_token, ensure_firebase_is_initialized_for_get_user):
    decoded_token = {"uid": "test_uid_no_role", "email": "norole@example.com"} # No 'role' claim
    mock_verify_id_token.return_value = decoded_token
    mock_auth_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dummy_token")

    user_info = await get_current_user(mock_auth_creds)
    assert user_info.role == UserRole.PATIENT # Should default to PATIENT

@pytest.mark.asyncio
async def test_get_current_user_expired_token(mock_verify_id_token, ensure_firebase_is_initialized_for_get_user):
    mock_verify_id_token.side_effect = auth.ExpiredIdTokenError("Token expired")
    mock_auth_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="expired_token")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(mock_auth_creds)

    assert exc_info.value.status_code == 401
    assert "Token has expired" in exc_info.value.detail

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(mock_verify_id_token, ensure_firebase_is_initialized_for_get_user):
    mock_verify_id_token.side_effect = auth.InvalidIdTokenError("Token invalid")
    mock_auth_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(mock_auth_creds)

    assert exc_info.value.status_code == 401
    assert "Invalid authentication credentials" in exc_info.value.detail

@pytest.mark.asyncio
async def test_get_current_user_no_uid_in_token(mock_verify_id_token, ensure_firebase_is_initialized_for_get_user):
    decoded_token_no_uid = {"email": "no_uid@example.com"} # Missing 'uid'
    mock_verify_id_token.return_value = decoded_token_no_uid
    mock_auth_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="no_uid_token")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(mock_auth_creds)

    assert exc_info.value.status_code == 401
    assert "User ID (uid) not found in token" in exc_info.value.detail

@pytest.mark.asyncio
async def test_get_current_user_firebase_not_initialized(reset_firebase_app_state): # Uses reset, not ensure_initialized
    # _firebase_app_initialized is False due to reset_firebase_app_state
    mock_auth_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="any_token")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(mock_auth_creds)

    assert exc_info.value.status_code == 503 # Service Unavailable
    assert "Firebase Admin SDK not initialized" in exc_info.value.detail

@pytest.mark.asyncio
async def test_get_current_user_other_firebase_auth_error(mock_verify_id_token, ensure_firebase_is_initialized_for_get_user):
    mock_verify_id_token.side_effect = auth.FirebaseAuthError(code="unknown-error", message="Some Firebase Auth error")
    mock_auth_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token_causing_other_error")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(mock_auth_creds)

    assert exc_info.value.status_code == 500 # Internal Server Error
    assert "Error verifying Firebase ID token: Some Firebase Auth error" in exc_info.value.detail

@pytest.mark.asyncio
async def test_get_current_user_no_auth_credentials():
    # Test case where HTTPAuthorizationCredentials might be None (e.g., if optional in some routes)
    # Although get_current_user itself has `token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)`
    # which makes it required by FastAPI's DI. This test is more for direct calls if they were possible.
    # For Depends, FastAPI would return a 401 if no token is provided by the client.
    # This test thus checks the behavior if `None` is somehow passed.
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(None) # Pass None directly

    assert exc_info.value.status_code == 401
    assert "Not authenticated" in exc_info.value.detail

```
