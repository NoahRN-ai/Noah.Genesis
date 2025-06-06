import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from backend.app.main import app # FastAPI app instance
from backend.app.models.api_models import (
    PatientDataLogCreateRequest,
    PatientDataLogResponse,
    UserInfo
)
from backend.app.models.firestore_models import PatientDataLog, DataType, UserRole
from backend.app.core.security import get_current_active_user

# Fixed UserInfo for testing
TEST_USER_PATIENT = UserInfo(
    user_id="patient_user_123",
    email="patient@example.com",
    role=UserRole.PATIENT,
    disabled=False
)
TEST_USER_OTHER = UserInfo( # For unauthorized tests
    user_id="other_user_456",
    email="other@example.com",
    role=UserRole.PATIENT, # Role might not matter as much as ID for self-access
    disabled=False
)
FIXED_TIMESTAMP = datetime.now(timezone.utc)

@pytest.fixture
def mock_create_patient_data_log_fixture(mocker):
    return mocker.patch('backend.app.api.v1.endpoints.patient_data.create_patient_data_log', new_callable=AsyncMock)

@pytest.fixture
def mock_list_patient_data_logs_fixture(mocker):
    return mocker.patch('backend.app.api.v1.endpoints.patient_data.list_patient_data_logs_for_user', new_callable=AsyncMock)

# --- Tests for POST / (submit_patient_data_log) ---

@pytest.mark.asyncio
async def test_submit_patient_data_log_success(mock_create_patient_data_log_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_PATIENT

    request_payload = PatientDataLogCreateRequest(
        target_patient_user_id=TEST_USER_PATIENT.user_id,
        timestamp=FIXED_TIMESTAMP,
        data_type=DataType.BLOOD_GLUCOSE,
        content={"value": 100, "unit": "mg/dL"},
        source="TestDevice"
    )

    mock_created_log = PatientDataLog(
        id="log_id_xyz",
        user_id=TEST_USER_PATIENT.user_id,
        created_by_user_id=TEST_USER_PATIENT.user_id,
        timestamp=request_payload.timestamp,
        data_type=request_payload.data_type,
        content=request_payload.content,
        source=request_payload.source,
        created_at=FIXED_TIMESTAMP,
        updated_at=FIXED_TIMESTAMP
    )
    mock_create_patient_data_log_fixture.return_value = mock_created_log

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/patient_data/", json=request_payload.model_dump(mode="json"))

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["id"] == "log_id_xyz"
    assert response_data["user_id"] == TEST_USER_PATIENT.user_id
    assert response_data["created_by_user_id"] == TEST_USER_PATIENT.user_id
    assert response_data["data_type"] == DataType.BLOOD_GLUCOSE.value # Ensure enum value is returned
    assert response_data["content"] == {"value": 100, "unit": "mg/dL"}

    mock_create_patient_data_log_fixture.assert_called_once()
    call_args = mock_create_patient_data_log_fixture.call_args[0][0] # The PatientDataLogCreate object
    assert call_args.user_id == TEST_USER_PATIENT.user_id
    assert call_args.created_by_user_id == TEST_USER_PATIENT.user_id
    assert call_args.data_type == request_payload.data_type
    assert call_args.content == request_payload.content

    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_submit_patient_data_log_service_error(mock_create_patient_data_log_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_PATIENT
    request_payload = PatientDataLogCreateRequest(
        target_patient_user_id=TEST_USER_PATIENT.user_id, timestamp=FIXED_TIMESTAMP,
        data_type=DataType.NOTES, content={"note": "test"}, source="manual"
    )
    mock_create_patient_data_log_fixture.side_effect = Exception("Firestore is down")

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/patient_data/", json=request_payload.model_dump(mode="json"))

    assert response.status_code == 500
    # Optionally check error message if a standard format is used

    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_submit_patient_data_log_unauthorized_attempt_as_per_current_code(mock_create_patient_data_log_fixture):
    # This test reflects that the POST endpoint's specific authorization check
    # for current_user.user_id == target_patient_user_id is currently commented out.
    # If it were active, we'd expect a 403.
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_OTHER # Logged in as other_user

    target_patient_id_for_log = "patient_user_123" # Attempting to log for patient_user_123

    request_payload = PatientDataLogCreateRequest(
        target_patient_user_id=target_patient_id_for_log, # Different from TEST_USER_OTHER.user_id
        timestamp=FIXED_TIMESTAMP,
        data_type=DataType.ACTIVITY,
        content={"steps": 5000},
        source="FitnessApp"
    )

    mock_created_log = PatientDataLog(
        id="log_id_diff_user",
        user_id=target_patient_id_for_log, # Log is for the target patient
        created_by_user_id=TEST_USER_OTHER.user_id, # But created by the logged-in user
        timestamp=request_payload.timestamp, data_type=request_payload.data_type,
        content=request_payload.content, source=request_payload.source,
        created_at=FIXED_TIMESTAMP, updated_at=FIXED_TIMESTAMP
    )
    mock_create_patient_data_log_fixture.return_value = mock_created_log

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/patient_data/", json=request_payload.model_dump(mode="json"))

    assert response.status_code == 201 # Expect 201 as auth is currently not blocking this

    mock_create_patient_data_log_fixture.assert_called_once()
    call_args = mock_create_patient_data_log_fixture.call_args[0][0]
    assert call_args.user_id == target_patient_id_for_log
    assert call_args.created_by_user_id == TEST_USER_OTHER.user_id # Verifies who created it

    del app.dependency_overrides[get_current_active_user]


# --- Tests for GET / (get_patient_data_logs) ---

@pytest.mark.asyncio
async def test_get_patient_data_logs_success(mock_list_patient_data_logs_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_PATIENT

    mock_log_1 = PatientDataLog(
        id="log1", user_id=TEST_USER_PATIENT.user_id, created_by_user_id=TEST_USER_PATIENT.user_id,
        timestamp=FIXED_TIMESTAMP, data_type=DataType.BLOOD_GLUCOSE, content={}, source="test",
        created_at=FIXED_TIMESTAMP, updated_at=FIXED_TIMESTAMP
    )
    mock_log_2 = PatientDataLog(
        id="log2", user_id=TEST_USER_PATIENT.user_id, created_by_user_id=TEST_USER_PATIENT.user_id,
        timestamp=FIXED_TIMESTAMP, data_type=DataType.BLOOD_PRESSURE, content={}, source="test",
        created_at=FIXED_TIMESTAMP, updated_at=FIXED_TIMESTAMP
    )
    mock_list_patient_data_logs_fixture.return_value = [mock_log_1, mock_log_2]

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/patient_data/?patient_user_id={TEST_USER_PATIENT.user_id}&limit=10")

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["id"] == "log1"
    assert response_data[1]["id"] == "log2"
    assert response_data[0]["data_type"] == DataType.BLOOD_GLUCOSE.value

    mock_list_patient_data_logs_fixture.assert_called_once_with(
        user_id=TEST_USER_PATIENT.user_id, limit=10, order_by="timestamp", descending=True
    )
    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_get_patient_data_logs_unauthorized(mock_list_patient_data_logs_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_OTHER # Logged in as other_user

    target_patient_id_for_logs = "patient_user_123" # Requesting logs for patient_user_123

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/patient_data/?patient_user_id={target_patient_id_for_logs}")

    assert response.status_code == 403 # This authorization IS active in GET
    mock_list_patient_data_logs_fixture.assert_not_called() # Service should not be called

    del app.dependency_overrides[get_current_active_user]

@pytest.mark.asyncio
async def test_get_patient_data_logs_service_error(mock_list_patient_data_logs_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_PATIENT # Authorized user

    mock_list_patient_data_logs_fixture.side_effect = Exception("Firestore is down")

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/patient_data/?patient_user_id={TEST_USER_PATIENT.user_id}")

    assert response.status_code == 500
    del app.dependency_overrides[get_current_active_user]

```
