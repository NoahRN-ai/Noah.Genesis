import pytest
import httpx
import os
from datetime import datetime, timezone
from google.cloud import firestore_v1 as系数_firestore # For the verification client
from typing import List

from backend.app.main import app # FastAPI app instance
from backend.app.models.api_models import (
    PatientDataLogCreateRequest,
    PatientDataLogResponse,
    UserInfo
)
from backend.app.models.firestore_models import DataType, UserRole
from backend.app.core.security import get_current_active_user

# Assumed to be set in the test environment
FIRESTORE_EMULATOR_HOST = os.environ.get("FIRESTORE_EMULATOR_HOST")
FIRESTORE_PROJECT_ID = os.environ.get("FIRESTORE_PROJECT_ID", "test-project-id")

if not FIRESTORE_EMULATOR_HOST:
    pytest.skip("FIRESTORE_EMULATOR_HOST not set, skipping patient data integration tests", allow_module_level=True)

# Fixed UserInfo for testing
TEST_USER_A = UserInfo(
    user_id="int_patient_A_789",
    email="patientA@example.com",
    role=UserRole.PATIENT,
    disabled=False
)
TEST_USER_B = UserInfo(
    user_id="int_patient_B_012",
    email="patientB@example.com",
    role=UserRole.PATIENT,
    disabled=False
)
FIXED_TIMESTAMP_NOW = datetime.now(timezone.utc)

@pytest.fixture(scope="module")
def firestore_emulator_verification_client():
    cred_mock = MagicMock() # Mock credentials for local emulator client
    client =系数_firestore.AsyncClient(project=FIRESTORE_PROJECT_ID, credentials=cred_mock)
    return client

@pytest.fixture(autouse=True)
async def clear_emulator_firestore():
    if not FIRESTORE_EMULATOR_HOST: return
    clear_url = f"http://{FIRESTORE_EMULATOR_HOST}/emulator/v1/projects/{FIRESTORE_PROJECT_ID}/databases/(default)/documents"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(clear_url)
            response.raise_for_status()
    except httpx.RequestError as e:
        pytest.fail(f"Failed to connect to Firestore emulator to clear data: {e}.")
    except httpx.HTTPStatusError as e:
        if e.response.status_code not in [200, 404]:
            pytest.fail(f"Failed to clear Firestore emulator data, status {e.response.status_code}: {e.response.text}")


@pytest.mark.asyncio
async def test_create_and_get_patient_data_log(firestore_emulator_verification_client):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_A

    # --- POST Request (Create) ---
    create_request_payload = PatientDataLogCreateRequest(
        target_patient_user_id=TEST_USER_A.user_id,
        timestamp=FIXED_TIMESTAMP_NOW,
        data_type=DataType.HEART_RATE,
        content={"value": 75, "unit": "bpm"},
        source="WearableDevice"
    )

    created_log_id = None
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response_post = await client.post("/api/v1/patient_data/", json=create_request_payload.model_dump(mode="json"))

    assert response_post.status_code == 201
    created_log_response_data = PatientDataLogResponse(**response_post.json())
    assert created_log_response_data.id is not None
    created_log_id = created_log_response_data.id
    assert created_log_response_data.user_id == TEST_USER_A.user_id
    assert created_log_response_data.created_by_user_id == TEST_USER_A.user_id # Set by endpoint
    assert created_log_response_data.data_type == DataType.HEART_RATE.value
    assert created_log_response_data.content == {"value": 75, "unit": "bpm"}
    assert created_log_response_data.source == "WearableDevice"
    # Timestamps are tricky to match exactly due to server processing time. Check for presence or approximate.
    assert datetime.fromisoformat(created_log_response_data.timestamp).replace(tzinfo=timezone.utc) == FIXED_TIMESTAMP_NOW
    assert created_log_response_data.created_at is not None
    assert created_log_response_data.updated_at is not None

    # --- Direct Verification (Recommended) ---
    doc_ref = firestore_emulator_verification_client.collection("patient_data_logs").document(created_log_id)
    doc_snapshot = await doc_ref.get()
    assert doc_snapshot.exists
    db_data = doc_snapshot.to_dict()
    assert db_data["user_id"] == TEST_USER_A.user_id
    assert db_data["created_by_user_id"] == TEST_USER_A.user_id
    assert db_data["data_type"] == DataType.HEART_RATE.value
    assert db_data["content"] == {"value": 75, "unit": "bpm"}
    # Timestamps from Firestore are datetime objects
    assert db_data["timestamp"].replace(tzinfo=timezone.utc) == FIXED_TIMESTAMP_NOW

    # --- GET Request (Read List) ---
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response_get = await client.get(f"/api/v1/patient_data/?patient_user_id={TEST_USER_A.user_id}&limit=5")

    assert response_get.status_code == 200
    list_response_data = [PatientDataLogResponse(**item) for item in response_get.json()]

    assert len(list_response_data) >= 1
    found_log_in_list = None
    for log_in_list in list_response_data:
        if log_in_list.id == created_log_id:
            found_log_in_list = log_in_list
            break

    assert found_log_in_list is not None
    assert found_log_in_list.user_id == TEST_USER_A.user_id
    assert found_log_in_list.data_type == DataType.HEART_RATE.value
    assert found_log_in_list.content == {"value": 75, "unit": "bpm"}

    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_get_patient_data_logs_unauthorized_integration():
    # --- Setup User A's Log ---
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_A
    create_payload_user_a = PatientDataLogCreateRequest(
        target_patient_user_id=TEST_USER_A.user_id,
        timestamp=FIXED_TIMESTAMP_NOW,
        data_type=DataType.STEPS,
        content={"count": 5000},
        source="Pedometer"
    )
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response_post_a = await client.post("/api/v1/patient_data/", json=create_payload_user_a.model_dump(mode="json"))
    assert response_post_a.status_code == 201

    # --- Attempt Access as User B ---
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_B # Switch to User B

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response_get_b_for_a = await client.get(f"/api/v1/patient_data/?patient_user_id={TEST_USER_A.user_id}") # User B trying to get User A's logs

    assert response_get_b_for_a.status_code == 403

    del app.dependency_overrides[get_current_active_user] # Clean up both overrides

```
