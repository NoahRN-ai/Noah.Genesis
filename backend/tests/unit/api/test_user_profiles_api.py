import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from backend.app.main import app # FastAPI app instance
from backend.app.models.api_models import UserInfo, UserProfileUpdateInput, UserProfileResponse
from backend.app.models.firestore_models import UserProfile, UserRole
from backend.app.core.security import get_current_active_user

# Fixed UserInfo for testing
TEST_USER_PROFILE_OWNER = UserInfo(
    user_id="profile_owner_123",
    email="profile_owner@example.com",
    role=UserRole.PATIENT,
    disabled=False
)
TEST_USER_OTHER = UserInfo(
    user_id="other_user_456",
    email="other@example.com",
    role=UserRole.PATIENT,
    disabled=False
)
FIXED_TIMESTAMP = datetime.now(timezone.utc)

@pytest.fixture
def mock_get_user_profile_fixture(mocker):
    return mocker.patch('backend.app.api.v1.endpoints.user_profiles.get_user_profile', new_callable=AsyncMock)

@pytest.fixture
def mock_update_user_profile_fixture(mocker):
    return mocker.patch('backend.app.api.v1.endpoints.user_profiles.update_user_profile', new_callable=AsyncMock)

# --- Tests for GET /{user_id}/profile ---

@pytest.mark.asyncio
async def test_read_user_profile_success(mock_get_user_profile_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_PROFILE_OWNER
    target_user_id = TEST_USER_PROFILE_OWNER.user_id

    mock_profile_data = UserProfile(
        user_id=target_user_id, email="owner@example.com", role=UserRole.PATIENT,
        display_name="Profile Owner", created_at=FIXED_TIMESTAMP, updated_at=FIXED_TIMESTAMP
    )
    mock_get_user_profile_fixture.return_value = mock_profile_data

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/users/{target_user_id}/profile")

    assert response.status_code == 200
    profile_response = UserProfileResponse(**response.json())
    assert profile_response.user_id == target_user_id
    assert profile_response.display_name == "Profile Owner"
    assert profile_response.role == UserRole.PATIENT.value # Ensure enum value

    mock_get_user_profile_fixture.assert_called_once_with(target_user_id)
    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_read_user_profile_unauthorized(mock_get_user_profile_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_OTHER # Logged in as other_user
    target_user_id = TEST_USER_PROFILE_OWNER.user_id # Trying to access profile_owner's profile

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/users/{target_user_id}/profile")

    assert response.status_code == 403
    mock_get_user_profile_fixture.assert_not_called()
    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_read_user_profile_not_found(mock_get_user_profile_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_PROFILE_OWNER
    target_user_id = TEST_USER_PROFILE_OWNER.user_id
    mock_get_user_profile_fixture.return_value = None # Profile not found

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/users/{target_user_id}/profile")

    assert response.status_code == 404
    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_read_user_profile_service_error(mock_get_user_profile_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_PROFILE_OWNER
    target_user_id = TEST_USER_PROFILE_OWNER.user_id
    mock_get_user_profile_fixture.side_effect = Exception("Database connection failed")

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/users/{target_user_id}/profile")

    assert response.status_code == 500
    del app.dependency_overrides[get_current_active_user]


# --- Tests for PUT /{user_id}/profile ---

@pytest.mark.asyncio
async def test_update_user_profile_success(mock_update_user_profile_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_PROFILE_OWNER
    target_user_id = TEST_USER_PROFILE_OWNER.user_id

    update_data = UserProfileUpdateInput(display_name="Updated Name", preferences={"notify": True})

    updated_profile_mock = UserProfile(
        user_id=target_user_id, email=TEST_USER_PROFILE_OWNER.email, role=TEST_USER_PROFILE_OWNER.role,
        display_name="Updated Name", preferences={"notify": True},
        created_at=FIXED_TIMESTAMP, updated_at=datetime.now(timezone.utc) # updated_at would change
    )
    mock_update_user_profile_fixture.return_value = updated_profile_mock

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(f"/api/v1/users/{target_user_id}/profile", json=update_data.model_dump(exclude_unset=True))

    assert response.status_code == 200
    profile_response = UserProfileResponse(**response.json())
    assert profile_response.user_id == target_user_id
    assert profile_response.display_name == "Updated Name"
    assert profile_response.preferences == {"notify": True}

    mock_update_user_profile_fixture.assert_called_once_with(target_user_id, update_data)
    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_update_user_profile_unauthorized(mock_update_user_profile_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_OTHER
    target_user_id = TEST_USER_PROFILE_OWNER.user_id # Trying to update another user's profile
    update_data = UserProfileUpdateInput(display_name="Attempted Update")

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(f"/api/v1/users/{target_user_id}/profile", json=update_data.model_dump(exclude_unset=True))

    assert response.status_code == 403
    mock_update_user_profile_fixture.assert_not_called()
    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_update_user_profile_no_update_data(mock_get_user_profile_fixture, mock_update_user_profile_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_PROFILE_OWNER
    target_user_id = TEST_USER_PROFILE_OWNER.user_id

    empty_update_data = UserProfileUpdateInput() # All fields None

    current_profile_mock = UserProfile(
        user_id=target_user_id, email=TEST_USER_PROFILE_OWNER.email, role=TEST_USER_PROFILE_OWNER.role,
        display_name="Current Name", preferences={"current": "pref"},
        created_at=FIXED_TIMESTAMP, updated_at=FIXED_TIMESTAMP
    )
    mock_get_user_profile_fixture.return_value = current_profile_mock # If update is empty, it fetches current

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(f"/api/v1/users/{target_user_id}/profile", json=empty_update_data.model_dump(exclude_unset=True))

    assert response.status_code == 200
    profile_response = UserProfileResponse(**response.json())
    assert profile_response.display_name == "Current Name" # Should return current profile

    mock_update_user_profile_fixture.assert_not_called() # update_user_profile service should not be called
    mock_get_user_profile_fixture.assert_called_once_with(target_user_id) # get_user_profile should be called
    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_update_user_profile_not_found(mock_update_user_profile_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_PROFILE_OWNER
    target_user_id = TEST_USER_PROFILE_OWNER.user_id
    update_data = UserProfileUpdateInput(display_name="Trying to update non-existent")

    mock_update_user_profile_fixture.return_value = None # Service indicates profile not found to update

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(f"/api/v1/users/{target_user_id}/profile", json=update_data.model_dump(exclude_unset=True))

    assert response.status_code == 404
    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_update_user_profile_service_error(mock_update_user_profile_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_PROFILE_OWNER
    target_user_id = TEST_USER_PROFILE_OWNER.user_id
    update_data = UserProfileUpdateInput(display_name="Update during outage")

    mock_update_user_profile_fixture.side_effect = Exception("Database write error")

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(f"/api/v1/users/{target_user_id}/profile", json=update_data.model_dump(exclude_unset=True))

    assert response.status_code == 500
    del app.dependency_overrides[get_current_active_user]

```
