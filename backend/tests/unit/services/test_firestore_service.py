import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from backend.app.models.firestore_models import (
    UserProfileCreate,
    UserProfile,
    PatientDataLogCreate,
    PatientDataLog,
    DataType,
    UserRole
)
from backend.app.services.firestore_service import (
    create_user_profile,
    get_user_profile,
    list_patient_data_logs_for_user,
    # db # This is what we need to mock effectively
)

# To be able to compare datetime objects, we can set a fixed time for tests
FIXED_NOW = datetime.now(timezone.utc)

@pytest.fixture(autouse=True)
def mock_datetime_now(mocker):
    """Fixture to mock datetime.now() to return a fixed time."""
    mocker.patch('backend.app.services.firestore_service.datetime', autospec=True)
    backend.app.services.firestore_service.datetime.now.return_value = FIXED_NOW


@pytest.fixture
def mock_db_client(mocker):
    """Mocks the global 'db' AsyncClient instance in firestore_service."""
    mock_client = MagicMock() # Using MagicMock for the client itself
    mocker.patch('backend.app.services.firestore_service.db', mock_client)
    return mock_client

# --- UserProfile Tests ---

@pytest.mark.asyncio
async def test_create_user_profile_success(mock_db_client, mocker):
    user_id = "test_user_123"
    profile_data = UserProfileCreate(
        email="test@example.com",
        display_name="Test User",
        photoURL="http://example.com/photo.jpg",
        role=UserRole.PATIENT,
        preferences={"theme": "dark"}
    )

    mock_doc_ref = MagicMock()
    mock_set_method = AsyncMock()
    mock_doc_ref.set = mock_set_method

    mock_db_client.collection.return_value.document.return_value = mock_doc_ref

    created_profile = await create_user_profile(user_id, profile_data)

    mock_db_client.collection.assert_called_once_with("user_profiles")
    mock_db_client.collection.return_value.document.assert_called_once_with(user_id)

    expected_data_to_set = {
        "user_id": user_id,
        "email": profile_data.email,
        "display_name": profile_data.display_name,
        "photoURL": profile_data.photoURL,
        "role": profile_data.role.value,
        "preferences": profile_data.preferences,
        "created_at": FIXED_NOW,
        "updated_at": FIXED_NOW,
    }
    mock_set_method.assert_called_once()
    # Check that the first argument of the call to set matches our expected data
    args, _ = mock_set_method.call_args
    assert args[0] == expected_data_to_set


    assert created_profile is not None
    assert created_profile.user_id == user_id
    assert created_profile.email == profile_data.email
    assert created_profile.display_name == profile_data.display_name
    assert created_profile.role == profile_data.role
    assert created_profile.preferences == profile_data.preferences
    assert created_profile.created_at == FIXED_NOW
    assert created_profile.updated_at == FIXED_NOW

@pytest.mark.asyncio
async def test_get_user_profile_found(mock_db_client):
    user_id = "test_user_123"
    sample_profile_data = {
        "user_id": user_id,
        "email": "test@example.com",
        "display_name": "Test User",
        "role": "patient",
        "preferences": {"theme": "dark"},
        "created_at": FIXED_NOW,
        "updated_at": FIXED_NOW,
    }

    mock_snapshot = MagicMock()
    mock_snapshot.exists = True
    mock_snapshot.to_dict.return_value = sample_profile_data
    mock_snapshot.id = user_id # Though not strictly used by get_user_profile for return, good for completeness

    mock_get_method = AsyncMock(return_value=mock_snapshot)
    mock_db_client.collection.return_value.document.return_value.get = mock_get_method

    profile = await get_user_profile(user_id)

    mock_db_client.collection.assert_called_once_with("user_profiles")
    mock_db_client.collection.return_value.document.assert_called_once_with(user_id)
    mock_get_method.assert_called_once()

    assert profile is not None
    assert profile.user_id == user_id
    assert profile.email == sample_profile_data["email"]
    assert profile.role == UserRole.PATIENT # Test enum conversion
    assert profile.created_at == FIXED_NOW

@pytest.mark.asyncio
async def test_get_user_profile_not_found(mock_db_client):
    user_id = "non_existent_user"

    mock_snapshot = MagicMock()
    mock_snapshot.exists = False

    mock_get_method = AsyncMock(return_value=mock_snapshot)
    mock_db_client.collection.return_value.document.return_value.get = mock_get_method

    profile = await get_user_profile(user_id)

    mock_db_client.collection.assert_called_once_with("user_profiles")
    mock_db_client.collection.return_value.document.assert_called_once_with(user_id)
    mock_get_method.assert_called_once()

    assert profile is None


# --- PatientDataLog List Tests ---

@pytest.mark.asyncio
async def test_list_patient_data_logs_for_user_success(mock_db_client):
    user_id = "patient_with_logs"
    limit = 5
    order_by_field = "timestamp"
    descending = True

    log_data_1 = {
        "id": "log1", "user_id": user_id, "timestamp": FIXED_NOW,
        "data_type": "blood_pressure", "content": {"systolic": 120, "diastolic": 80},
        "source": "test_device", "created_at": FIXED_NOW, "updated_at": FIXED_NOW,
        "created_by_user_id": user_id
    }
    log_data_2 = {
        "id": "log2", "user_id": user_id, "timestamp": FIXED_NOW, # In reality, timestamps would differ
        "data_type": "blood_glucose", "content": {"value": 90, "unit": "mg/dL"},
        "source": "manual", "created_at": FIXED_NOW, "updated_at": FIXED_NOW,
        "created_by_user_id": user_id
    }

    mock_snapshot_1 = MagicMock()
    mock_snapshot_1.exists = True
    mock_snapshot_1.id = log_data_1["id"]
    mock_snapshot_1.to_dict.return_value = {k:v for k,v in log_data_1.items() if k != 'id'}


    mock_snapshot_2 = MagicMock()
    mock_snapshot_2.exists = True
    mock_snapshot_2.id = log_data_2["id"]
    mock_snapshot_2.to_dict.return_value = {k:v for k,v in log_data_2.items() if k != 'id'}


    # Mock the stream to be an async iterable
    async def mock_stream_gen():
        yield mock_snapshot_1
        yield mock_snapshot_2

    mock_query = MagicMock()
    mock_query.stream = mock_stream_gen # Assign the async generator directly

    # Mock the fluent interface
    mock_db_client.collection.return_value.where.return_value.order_by.return_value.limit.return_value = mock_query

    logs = await list_patient_data_logs_for_user(user_id, limit, order_by_field, descending)

    mock_db_client.collection.assert_called_once_with("patient_data_logs")
    mock_db_client.collection.return_value.where.assert_called_once_with("user_id", "==", user_id)
    mock_db_client.collection.return_value.where.return_value.order_by.assert_called_once_with(
        order_by_field, direction='DESCENDING' if descending else 'ASCENDING'
    )
    mock_db_client.collection.return_value.where.return_value.order_by.return_value.limit.assert_called_once_with(limit)


    assert len(logs) == 2
    assert logs[0].id == log_data_1["id"]
    assert logs[0].data_type == DataType.BLOOD_PRESSURE
    assert logs[0].content["systolic"] == 120
    assert logs[1].id == log_data_2["id"]
    assert logs[1].data_type == DataType.BLOOD_GLUCOSE
    assert logs[1].content["value"] == 90


@pytest.mark.asyncio
async def test_list_patient_data_logs_for_user_empty(mock_db_client):
    user_id = "patient_without_logs"
    limit = 5

    async def mock_empty_stream_gen():
        if False: # Never yields
            yield

    mock_query = MagicMock()
    mock_query.stream = mock_empty_stream_gen

    mock_db_client.collection.return_value.where.return_value.order_by.return_value.limit.return_value = mock_query

    logs = await list_patient_data_logs_for_user(user_id, limit)

    assert len(logs) == 0
    mock_db_client.collection.assert_called_once_with("patient_data_logs")
    mock_db_client.collection.return_value.where.assert_called_once_with("user_id", "==", user_id)
    # Further assertions on order_by and limit can be added if needed.
```
