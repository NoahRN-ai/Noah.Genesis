import pytest
from unittest.mock import patch, MagicMock, AsyncMock # AsyncMock for async methods
from datetime import datetime, timezone

# Make sure the service module can be imported. Adjust path if necessary.
# This assumes tests are run from a context where 'backend' is a top-level package.
from backend.app.services import firestore_service
from backend.app.models.firestore_models import (
    PatientProfile, PatientProfileCreate, PatientProfileUpdate, Gender, HumanName,
    Observation, ObservationCreate, ObservationUpdate, FHIRStatusObservation, CodeableConcept, Quantity,
    MedicationStatement, MedicationStatementCreate, MedicationStatementUpdate, FHIRStatusMedicationStatement,
    AIContextualStore, AIContextualStoreCreate, AIContextualStoreUpdate,
    utcnow # Assuming this is available from firestore_models or firestore_service
)

# If utcnow is in firestore_service, use that, otherwise import from models.
# For consistency, let's assume firestore_service.utcnow is used by the service.
# We might need to mock firestore_service.utcnow for deterministic timestamp tests.

# --- Test Data Samples (Simplified for brevity, reuse from model tests or define new) ---

def create_sample_patient_profile_create_data() -> PatientProfileCreate:
    return PatientProfileCreate(
        name=[HumanName(family="Test", given=["Patient"], use="official")],
        gender=Gender.FEMALE,
        birthDate=datetime(1990, 5, 15, tzinfo=timezone.utc)
    )

def create_sample_patient_profile_db_data(patient_id: str) -> dict:
    now = utcnow()
    return {
        "patient_id": patient_id,
        "name": [{"family": "Test", "given": ["Patient"], "use": "official", "text":"Patient Test"}], # Pydantic might auto-add text
        "gender": "female",
        "birthDate": datetime(1990, 5, 15, tzinfo=timezone.utc),
        "active": True,
        "telecom": [], "address": [], # Assuming defaults
        "created_at": now,
        "updated_at": now
    }

def create_sample_observation_create_data(patient_id: str) -> ObservationCreate:
    return ObservationCreate(
        subject_patient_id=patient_id,
        status=FHIRStatusObservation.FINAL,
        code=CodeableConcept(text="Heart Rate", coding=[{"system": "loinc", "code": "8867-4", "display": "Heart rate"}]),
        effectiveDateTime=utcnow(),
        valueQuantity=Quantity(value=75, unit="bpm")
    )

def create_sample_observation_db_data(obs_id: str, patient_id: str) -> dict:
    now = utcnow()
    data = create_sample_observation_create_data(patient_id).model_dump(mode='json') # use_enum_values=True if in model_config
    # Manually convert enums if not handled by model_dump with use_enum_values=True
    data["status"] = FHIRStatusObservation.FINAL.value
    data["observation_id"] = obs_id
    data["created_at"] = now
    data["updated_at"] = now
    # Pydantic sub-models are already dicts via model_dump
    return data

def create_sample_med_statement_create_data(patient_id: str) -> MedicationStatementCreate:
    return MedicationStatementCreate(
        subject_patient_id=patient_id,
        status=FHIRStatusMedicationStatement.ACTIVE,
        medicationCodeableConcept=CodeableConcept(text="Amoxicillin 250mg"),
        effectiveDateTime=utcnow()
    )

def create_sample_med_statement_db_data(stmt_id: str, patient_id: str) -> dict:
    now = utcnow()
    data = create_sample_med_statement_create_data(patient_id).model_dump(mode='json')
    data["status"] = FHIRStatusMedicationStatement.ACTIVE.value
    data["medication_statement_id"] = stmt_id
    data["created_at"] = now
    data["updated_at"] = now
    return data

def create_sample_ai_store_create_data(patient_id: str) -> AIContextualStoreCreate:
    return AIContextualStoreCreate(
        patient_id=patient_id,
        last_summary="Initial summary.",
        key_insights=["Insight 1"]
    )

def create_sample_ai_store_db_data(patient_id: str) -> dict:
    now = utcnow()
    return {
        "patient_id": patient_id,
        "last_summary": "Initial summary.",
        "key_insights": ["Insight 1"],
        "interaction_highlights": [], "preferences": {}, "custom_alerts": [], # Defaults
        "created_at": now,
        "updated_at": now
    }

# --- Pytest Fixture for Mocking Firestore Client ---

@pytest.fixture
def mock_firestore_db():
    # This patches 'db' instance in the firestore_service module
    with patch('backend.app.services.firestore_service.db', new_callable=AsyncMock) as mock_db:
        yield mock_db

@pytest.fixture
def mock_utcnow():
    fixed_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    with patch('backend.app.services.firestore_service.utcnow', return_value=fixed_now) as mock_time:
        yield mock_time


# --- PatientProfile Service Tests ---

@pytest.mark.asyncio
async def test_create_patient_profile(mock_firestore_db: AsyncMock, mock_utcnow: MagicMock):
    patient_id = "patient_test_001"
    profile_create_data = create_sample_patient_profile_create_data()

    mock_doc_ref = AsyncMock()
    mock_firestore_db.collection().document.return_value = mock_doc_ref

    result = await firestore_service.create_patient_profile(patient_id, profile_create_data)

    mock_firestore_db.collection.assert_called_with(firestore_service.NOAH_MVP_PATIENTS_COLLECTION)
    mock_firestore_db.collection().document.assert_called_with(patient_id)

    # Check the data passed to set()
    args, _ = mock_doc_ref.set.call_args
    set_data = args[0]
    assert set_data["gender"] == profile_create_data.gender.value
    assert set_data["birthDate"] == profile_create_data.birthDate
    assert set_data["created_at"] == mock_utcnow.return_value
    assert set_data["updated_at"] == mock_utcnow.return_value

    assert isinstance(result, PatientProfile)
    assert result.patient_id == patient_id
    assert result.gender == profile_create_data.gender

@pytest.mark.asyncio
async def test_get_patient_profile_found(mock_firestore_db: AsyncMock):
    patient_id = "patient_test_002"
    db_data = create_sample_patient_profile_db_data(patient_id)

    mock_snapshot = AsyncMock()
    mock_snapshot.exists = True
    mock_snapshot.id = patient_id
    mock_snapshot.to_dict.return_value = db_data

    mock_doc_ref = AsyncMock()
    mock_doc_ref.get.return_value = mock_snapshot
    mock_firestore_db.collection().document.return_value = mock_doc_ref

    result = await firestore_service.get_patient_profile(patient_id)

    assert isinstance(result, PatientProfile)
    assert result.patient_id == patient_id
    assert result.created_at == db_data["created_at"]

@pytest.mark.asyncio
async def test_get_patient_profile_not_found(mock_firestore_db: AsyncMock):
    patient_id = "patient_test_003"
    mock_snapshot = AsyncMock()
    mock_snapshot.exists = False
    mock_doc_ref = AsyncMock()
    mock_doc_ref.get.return_value = mock_snapshot
    mock_firestore_db.collection().document.return_value = mock_doc_ref

    result = await firestore_service.get_patient_profile(patient_id)
    assert result is None

# --- Observation Service Tests ---

@pytest.mark.asyncio
async def test_create_observation(mock_firestore_db: AsyncMock, mock_utcnow: MagicMock):
    patient_id = "patient_obs_001"
    observation_id = "new_obs_123"
    obs_create_data = create_sample_observation_create_data(patient_id)

    mock_doc_ref = AsyncMock()
    mock_doc_ref.id = observation_id
    mock_subcollection_ref = AsyncMock()
    mock_subcollection_ref.add.return_value = (mock_utcnow.return_value, mock_doc_ref) # add returns (timestamp, DocumentReference)

    mock_patient_doc_ref = AsyncMock()
    mock_patient_doc_ref.collection.return_value = mock_subcollection_ref
    mock_firestore_db.collection().document.return_value = mock_patient_doc_ref

    result = await firestore_service.create_observation(patient_id, obs_create_data)

    mock_firestore_db.collection.assert_called_with(firestore_service.NOAH_MVP_PATIENTS_COLLECTION)
    mock_firestore_db.collection().document.assert_called_with(patient_id)
    mock_patient_doc_ref.collection.assert_called_with(firestore_service.NOAH_MVP_OBSERVATIONS_SUBCOLLECTION)

    args, _ = mock_subcollection_ref.add.call_args
    add_data = args[0]
    assert add_data["subject_patient_id"] == patient_id
    assert add_data["status"] == obs_create_data.status.value
    assert add_data["created_at"] == mock_utcnow.return_value

    assert isinstance(result, Observation)
    assert result.observation_id == observation_id
    assert result.subject_patient_id == patient_id

@pytest.mark.asyncio
async def test_list_observations_for_patient(mock_firestore_db: AsyncMock):
    patient_id = "patient_obs_002"
    obs_data1 = create_sample_observation_db_data("obs1", patient_id)
    obs_data2 = create_sample_observation_db_data("obs2", patient_id)

    mock_snapshot1 = AsyncMock()
    mock_snapshot1.exists = True
    mock_snapshot1.id = "obs1"
    mock_snapshot1.to_dict.return_value = obs_data1

    mock_snapshot2 = AsyncMock()
    mock_snapshot2.exists = True
    mock_snapshot2.id = "obs2"
    mock_snapshot2.to_dict.return_value = obs_data2

    mock_query = AsyncMock()
    # Mock the async iterator part of query.stream()
    async def mock_stream_results():
        yield mock_snapshot1
        yield mock_snapshot2
    mock_query.stream.return_value = mock_stream_results() # assign the async generator

    mock_subcollection_ref = AsyncMock()
    mock_subcollection_ref.order_by().limit.return_value = mock_query # Chain calls
    mock_patient_doc_ref = AsyncMock()
    mock_patient_doc_ref.collection.return_value = mock_subcollection_ref
    mock_firestore_db.collection().document.return_value = mock_patient_doc_ref

    results = await firestore_service.list_observations_for_patient(patient_id, limit=10)

    assert len(results) == 2
    assert isinstance(results[0], Observation)
    assert results[0].observation_id == "obs1"
    mock_subcollection_ref.order_by.assert_called_with("effectiveDateTime", direction=firestore_service.Query.DESCENDING) # Assuming Query is accessible
    mock_subcollection_ref.order_by().limit.assert_called_with(10)


# --- MedicationStatement Service Tests ---
# (Similar structure to Observation tests: create_medication_statement, list_medication_statements_for_patient)
# For brevity, I'll skip writing them all out here but they would follow the same pattern.

# --- AIContextualStore Service Tests ---

@pytest.mark.asyncio
async def test_create_or_replace_ai_contextual_store_new(mock_firestore_db: AsyncMock, mock_utcnow: MagicMock):
    patient_id = "patient_ai_001"
    store_create_data = create_sample_ai_store_create_data(patient_id)

    mock_existing_snapshot = AsyncMock()
    mock_existing_snapshot.exists = False # Simulate document does not exist

    mock_doc_ref = AsyncMock()
    mock_doc_ref.get.return_value = mock_existing_snapshot # For the initial check
    mock_firestore_db.collection().document.return_value = mock_doc_ref

    result = await firestore_service.create_or_replace_ai_contextual_store(patient_id, store_create_data)

    mock_firestore_db.collection.assert_called_with(firestore_service.AI_CONTEXTUAL_STORES_COLLECTION)
    mock_firestore_db.collection().document.assert_called_with(patient_id)

    args, _ = mock_doc_ref.set.call_args
    set_data = args[0]
    assert set_data["patient_id"] == patient_id
    assert set_data["last_summary"] == store_create_data.last_summary
    assert set_data["created_at"] == mock_utcnow.return_value # New document gets current time as created_at
    assert set_data["updated_at"] == mock_utcnow.return_value

    assert isinstance(result, AIContextualStore)
    assert result.patient_id == patient_id
    assert result.created_at == mock_utcnow.return_value

@pytest.mark.asyncio
async def test_create_or_replace_ai_contextual_store_existing(mock_firestore_db: AsyncMock, mock_utcnow: MagicMock):
    patient_id = "patient_ai_002"
    store_create_data = create_sample_ai_store_create_data(patient_id)

    original_created_at = datetime(2022, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    mock_existing_db_data = {
        "patient_id": patient_id, "created_at": original_created_at, "updated_at": original_created_at,
        "last_summary": "Old summary"
    }

    mock_existing_snapshot = AsyncMock()
    mock_existing_snapshot.exists = True
    mock_existing_snapshot.to_dict.return_value = mock_existing_db_data

    mock_doc_ref = AsyncMock()
    mock_doc_ref.get.return_value = mock_existing_snapshot
    mock_firestore_db.collection().document.return_value = mock_doc_ref

    result = await firestore_service.create_or_replace_ai_contextual_store(patient_id, store_create_data)

    args, _ = mock_doc_ref.set.call_args
    set_data = args[0]
    assert set_data["created_at"] == original_created_at # Should preserve original created_at
    assert set_data["updated_at"] == mock_utcnow.return_value # updated_at should be new
    assert set_data["last_summary"] == store_create_data.last_summary # Content updated

    assert result.created_at == original_created_at

@pytest.mark.asyncio
async def test_update_ai_contextual_store(mock_firestore_db: AsyncMock, mock_utcnow: MagicMock):
    patient_id = "patient_ai_003"
    store_update_data = AIContextualStoreUpdate(last_summary="Updated summary")

    # Mock for the get() call made after update
    updated_db_data = create_sample_ai_store_db_data(patient_id)
    updated_db_data["last_summary"] = "Updated summary"
    updated_db_data["updated_at"] = mock_utcnow.return_value

    mock_updated_snapshot = AsyncMock()
    mock_updated_snapshot.exists = True
    mock_updated_snapshot.to_dict.return_value = updated_db_data

    # Mock for the initial check get() if strict update behavior is tested
    mock_check_snapshot = AsyncMock()
    mock_check_snapshot.exists = True

    mock_doc_ref = AsyncMock()
    # Sequence of get calls: first for check (if any), then for returning updated data
    mock_doc_ref.get.side_effect = [mock_check_snapshot, mock_updated_snapshot]
    mock_firestore_db.collection().document.return_value = mock_doc_ref

    result = await firestore_service.update_ai_contextual_store(patient_id, store_update_data)

    mock_doc_ref.update.assert_called_once()
    args, _ = mock_doc_ref.update.call_args
    update_arg_data = args[0]
    assert update_arg_data["last_summary"] == "Updated summary"
    assert update_arg_data["updated_at"] == mock_utcnow.return_value

    assert isinstance(result, AIContextualStore)
    assert result.last_summary == "Updated summary"
    assert result.updated_at == mock_utcnow.return_value

# --- General Notes for Service Tests ---
# - Test delete_* functions: ensure doc_ref.delete() is called.
# - Test update_* functions:
#   - Case: document does not exist (should return None or raise error depending on implementation).
#   - Case: update_data is empty (should ideally skip DB call and return current data).
# - Test list_* functions:
#   - Case: no documents found (should return empty list).
#   - Verify ordering and limiting parameters are correctly applied to the Firestore query.
# - Mock `firestore_service.Query.DESCENDING` and `ASCENDING` if Query is imported from google.cloud.firestore
#   The current code uses `firestore_service.Query.DESCENDING` which means Query is available in that module's scope.
#   If `Query` is directly from `google.cloud.firestore`, the mock setup might need adjustment or direct import.
#   In these tests, `firestore_service.Query.DESCENDING` is used, assuming it's accessible.
# - Ensure that `model_dump(exclude_unset=True)` is used in service functions for updates,
#   and test that partial updates don't overwrite unspecified fields with nulls.
# - For `create_observation` and `create_medication_statement`, the `add()` method returns a tuple:
#   `_timestamp, doc_ref = await subcollection_ref.add(doc_data)`
#   The mock needs to reflect this: `mock_subcollection_ref.add.return_value = (mock_timestamp, mock_doc_ref)`
#   The `mock_timestamp` can be `mock_utcnow.return_value`.

pytest # Ensure this file is treated as a test file
