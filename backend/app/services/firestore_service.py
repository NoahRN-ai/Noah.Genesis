from google.cloud.firestore_async import AsyncClient
from google.cloud.firestore import Query, AsyncWriteBatch # For typed queries if needed later
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from backend.app.models.firestore_models import (
    UserProfileCreate, UserProfileUpdate, UserProfile,
    PatientDataLogCreate, PatientDataLogUpdate, PatientDataLog,
    InteractionHistoryCreate, InteractionHistoryUpdate, InteractionHistory, # InteractionHistoryUpdate might not be used if immutable
    PatientProfileBase, PatientProfileCreate, PatientProfileUpdate, PatientProfile,
    ObservationBase, ObservationCreate, ObservationUpdate, Observation,
    MedicationStatementBase, MedicationStatementCreate, MedicationStatementUpdate, MedicationStatement,
    AIContextualStoreBase, AIContextualStoreCreate, AIContextualStoreUpdate, AIContextualStore
)

# --- Firestore Client Initialization ---
# For a FastAPI app, this client would typically be initialized during app startup
# and managed via dependency injection or lifespan events.
# For simplicity in this service module, we'll instantiate it directly.
# In a real application, ensure proper async context management for the client if shared globally.
db = AsyncClient() # Assumes Application Default Credentials are set

# --- Collection Names ---
USER_PROFILES_COLLECTION = "user_profiles"
PATIENT_DATA_LOGS_COLLECTION = "patient_data_logs"
INTERACTION_HISTORY_COLLECTION = "interaction_history"
NOAH_MVP_PATIENTS_COLLECTION = "noah_mvp_patients"
NOAH_MVP_OBSERVATIONS_SUBCOLLECTION = "noah_mvp_observations"
NOAH_MVP_MEDICATION_STATEMENTS_SUBCOLLECTION = "noah_mvp_medication_statements"
AI_CONTEXTUAL_STORES_COLLECTION = "ai_contextual_stores"

def utcnow():
    return datetime.now(timezone.utc)

# --- UserProfile Service Functions ---

async def create_user_profile(user_id: str, profile_data: UserProfileCreate) -> UserProfile:
    """Creates a new user profile document in Firestore."""
    doc_ref = db.collection(USER_PROFILES_COLLECTION).document(user_id)
    current_time = utcnow()
    profile_doc_data = profile_data.model_dump(exclude_unset=True)
    profile_doc_data["created_at"] = current_time
    profile_doc_data["updated_at"] = current_time

    await doc_ref.set(profile_doc_data)
    # Construct the UserProfile object for return, ensuring all fields including server-set ones are present
    # This assumes profile_data.model_dump() contains all fields from UserProfileBase
    return UserProfile(user_id=user_id, created_at=current_time, updated_at=current_time, **profile_data.model_dump())

async def get_user_profile(user_id: str) -> Optional[UserProfile]:
    """Retrieves a user profile document from Firestore by user_id."""
    doc_ref = db.collection(USER_PROFILES_COLLECTION).document(user_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        return UserProfile(user_id=snapshot.id, **data)
    return None

async def update_user_profile(user_id: str, profile_update_data: UserProfileUpdate) -> Optional[UserProfile]:
    """Updates an existing user profile document in Firestore."""
    doc_ref = db.collection(USER_PROFILES_COLLECTION).document(user_id)

    # Ensure the document exists before attempting to update
    # This check can be omitted if "upsert" behavior is acceptable or handled differently,
    # but for a strict update, it's good practice.
    # existing_doc = await doc_ref.get()
    # if not existing_doc.exists:
    #     return None # Or raise a custom exception/HTTPException in an API context

    update_data = profile_update_data.model_dump(exclude_unset=True)
    if not update_data: # No fields to update
        # If no data to update, just return the current state of the profile
        return await get_user_profile(user_id)

    update_data["updated_at"] = utcnow()
    await doc_ref.update(update_data)

    updated_snapshot = await doc_ref.get() # Fetch the updated document
    if updated_snapshot.exists:
        return UserProfile(user_id=updated_snapshot.id, **updated_snapshot.to_dict())
    return None # Should ideally not be reached if update was on an existing doc and successful

async def delete_user_profile(user_id: str) -> bool:
    """Deletes a user profile document from Firestore."""
    doc_ref = db.collection(USER_PROFILES_COLLECTION).document(user_id)
    await doc_ref.delete()
    # Deletion is typically fire-and-forget in Firestore.
    # To confirm deletion, you could try to get() the doc afterwards and check existence.
    # For MVP, returning True assumes the command was accepted by Firestore.
    return True


# --- PatientDataLog Service Functions ---

async def create_patient_data_log(log_data: PatientDataLogCreate) -> PatientDataLog:
    """Creates a new patient data log entry in Firestore with an auto-generated ID."""
    collection_ref = db.collection(PATIENT_DATA_LOGS_COLLECTION)
    current_time = utcnow()
    log_doc_data = log_data.model_dump(exclude_unset=True)
    log_doc_data["created_at"] = current_time
    log_doc_data["updated_at"] = current_time

    # Add document with auto-generated ID
    update_time, doc_ref = await collection_ref.add(log_doc_data) # add() returns (timestamp, DocumentReference)
    # Construct the PatientDataLog object for return
    return PatientDataLog(log_id=doc_ref.id, created_at=current_time, updated_at=current_time, **log_data.model_dump())

async def get_patient_data_log(log_id: str) -> Optional[PatientDataLog]:
    """Retrieves a specific patient data log entry by its ID."""
    doc_ref = db.collection(PATIENT_DATA_LOGS_COLLECTION).document(log_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        return PatientDataLog(log_id=snapshot.id, **data)
    return None

async def list_patient_data_logs_for_user(
    user_id: str,
    limit: int = 20,
    order_by: str = "timestamp",
    descending: bool = True
) -> List[PatientDataLog]:
    """Lists patient data logs for a specific user, with pagination and ordering."""
    query = db.collection(PATIENT_DATA_LOGS_COLLECTION).where("user_id", "==", user_id)

    direction = Query.DESCENDING if descending else Query.ASCENDING
    query = query.order_by(order_by, direction=direction).limit(limit)

    logs = []
    async for snapshot in query.stream():
        if snapshot.exists: # Should always be true for query results unless collection is empty
            data = snapshot.to_dict()
            logs.append(PatientDataLog(log_id=snapshot.id, **data))
    return logs

async def update_patient_data_log(log_id: str, log_update_data: PatientDataLogUpdate) -> Optional[PatientDataLog]:
    """Updates an existing patient data log entry."""
    doc_ref = db.collection(PATIENT_DATA_LOGS_COLLECTION).document(log_id)
    update_data = log_update_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_patient_data_log(log_id) # Return current state if no updates

    update_data["updated_at"] = utcnow()
    await doc_ref.update(update_data)

    updated_snapshot = await doc_ref.get()
    if updated_snapshot.exists:
        return PatientDataLog(log_id=updated_snapshot.id, **updated_snapshot.to_dict())
    return None

async def delete_patient_data_log(log_id: str) -> bool:
    """Deletes a patient data log entry."""
    doc_ref = db.collection(PATIENT_DATA_LOGS_COLLECTION).document(log_id)
    await doc_ref.delete()
    return True


# --- InteractionHistory Service Functions ---

async def create_interaction_history_entry(entry_data: InteractionHistoryCreate) -> InteractionHistory:
    """Creates a new interaction history entry in Firestore with an auto-generated ID."""
    collection_ref = db.collection(INTERACTION_HISTORY_COLLECTION)
    current_time = utcnow() # Timestamp for when the interaction is logged

    entry_doc_data = entry_data.model_dump(exclude_unset=True)
    # The `timestamp` field in InteractionHistory is meant to be the time of the interaction event.
    # If it's not provided by the caller (e.g. LangGraph), we set it now.
    # If it IS provided (e.g. from a client event), use that.
    # For this service, we'll assume it's the logging time.
    entry_doc_data["timestamp"] = current_time

    update_time, doc_ref = await collection_ref.add(entry_doc_data)
    # Construct the InteractionHistory object for return
    # The model_dump might include tool_calls/responses as dicts, Pydantic handles sub-model validation
    return InteractionHistory(interaction_id=doc_ref.id, **entry_doc_data)


async def get_interaction_history_entry(interaction_id: str) -> Optional[InteractionHistory]:
    """Retrieves a specific interaction history entry by its ID."""
    doc_ref = db.collection(INTERACTION_HISTORY_COLLECTION).document(interaction_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        return InteractionHistory(interaction_id=snapshot.id, **data)
    return None

async def list_interaction_history_for_session(
    session_id: str,
    limit: int = 50,
    order_by: str = "timestamp", # This is the timestamp of interaction logging
    descending: bool = False # Chat history typically ascending
) -> List[InteractionHistory]:
    """Lists interaction history entries for a specific session, with pagination and ordering."""
    query = db.collection(INTERACTION_HISTORY_COLLECTION).where("session_id", "==", session_id)

    direction = Query.DESCENDING if descending else Query.ASCENDING
    query = query.order_by(order_by, direction=direction).limit(limit)

    history_entries = []
    async for snapshot in query.stream():
        if snapshot.exists:
            data = snapshot.to_dict()
            history_entries.append(InteractionHistory(interaction_id=snapshot.id, **data))
    return history_entries

# Update/Delete for InteractionHistory are generally not recommended as history should be immutable.
# If needed, they can be added similar to other services, but consider implications.


# --- PatientProfile Service Functions ---

async def create_patient_profile(patient_id: str, profile_data: PatientProfileCreate) -> PatientProfile:
    """Creates a new patient profile document in Firestore."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id)
    current_time = utcnow()
    # Use model_dump() to convert Pydantic model to dict, ensuring enum values are used if model_config.use_enum_values = True
    profile_doc_data = profile_data.model_dump(exclude_unset=True)
    profile_doc_data["created_at"] = current_time
    profile_doc_data["updated_at"] = current_time

    await doc_ref.set(profile_doc_data)
    # Construct the PatientProfile object for return
    return PatientProfile(patient_id=patient_id, created_at=current_time, updated_at=current_time, **profile_data.model_dump())

async def get_patient_profile(patient_id: str) -> Optional[PatientProfile]:
    """Retrieves a patient profile document from Firestore by patient_id."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        # Ensure datetime fields are converted if stored as Firestore Timestamps
        # Pydantic V2 usually handles this automatically if types are `datetime`
        return PatientProfile(patient_id=snapshot.id, **data)
    return None

async def update_patient_profile(patient_id: str, profile_update_data: PatientProfileUpdate) -> Optional[PatientProfile]:
    """Updates an existing patient profile document in Firestore."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id)

    # Check if document exists (optional, Firestore update won't fail if doc doesn't exist but won't create either)
    # existing_doc = await doc_ref.get()
    # if not existing_doc.exists:
    #     return None # Or raise error

    update_data = profile_update_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_patient_profile(patient_id) # No changes, return current

    update_data["updated_at"] = utcnow()
    await doc_ref.update(update_data)

    updated_snapshot = await doc_ref.get()
    if updated_snapshot.exists:
        return PatientProfile(patient_id=updated_snapshot.id, **updated_snapshot.to_dict())
    return None # Should not happen if update was successful on existing doc

async def delete_patient_profile(patient_id: str) -> bool:
    """Deletes a patient profile document from Firestore."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id)
    await doc_ref.delete()
    # To confirm deletion, one might try to get the doc again. For now, assume success.
    return True

async def list_patient_profiles(
    limit: int = 20,
    order_by: str = "created_at", # Default order: newest first
    descending: bool = True
) -> List[PatientProfile]:
    """Lists patient profiles with pagination and ordering."""
    query = db.collection(NOAH_MVP_PATIENTS_COLLECTION)
    direction = Query.DESCENDING if descending else Query.ASCENDING
    query = query.order_by(order_by, direction=direction).limit(limit)

    profiles = []
    async for snapshot in query.stream():
        if snapshot.exists:
            data = snapshot.to_dict()
            profiles.append(PatientProfile(patient_id=snapshot.id, **data))
    return profiles


# --- Observation Service Functions (Subcollection of PatientProfile) ---

async def create_observation(patient_id: str, observation_data: ObservationCreate) -> Observation:
    """Creates a new observation for a patient in a subcollection."""
    # Ensure subject_patient_id in data matches patient_id in path for consistency
    if observation_data.subject_patient_id != patient_id:
        # Or handle as an error, e.g., raise ValueError
        observation_data.subject_patient_id = patient_id

    subcollection_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_OBSERVATIONS_SUBCOLLECTION)
    current_time = utcnow()

    # Use model_dump() for converting Pydantic model to dict
    doc_data = observation_data.model_dump(exclude_unset=True)
    doc_data["created_at"] = current_time
    doc_data["updated_at"] = current_time

    _timestamp, doc_ref = await subcollection_ref.add(doc_data) # Firestore auto-generates observation_id

    # Construct the Observation object for return
    # Merge initial data with server-set fields
    final_data = observation_data.model_dump()
    final_data["observation_id"] = doc_ref.id
    final_data["created_at"] = current_time
    final_data["updated_at"] = current_time
    return Observation(**final_data)

async def get_observation(patient_id: str, observation_id: str) -> Optional[Observation]:
    """Retrieves a specific observation for a patient."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_OBSERVATIONS_SUBCOLLECTION).document(observation_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        return Observation(observation_id=snapshot.id, **data)
    return None

async def list_observations_for_patient(
    patient_id: str,
    limit: int = 20,
    order_by: str = "effectiveDateTime", # Common default for observations
    descending: bool = True
) -> List[Observation]:
    """Lists observations for a specific patient."""
    subcollection_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_OBSERVATIONS_SUBCOLLECTION)
    direction = Query.DESCENDING if descending else Query.ASCENDING
    query = subcollection_ref.order_by(order_by, direction=direction).limit(limit)

    observations = []
    async for snapshot in query.stream():
        if snapshot.exists:
            data = snapshot.to_dict()
            observations.append(Observation(observation_id=snapshot.id, **data))
    return observations

async def update_observation(patient_id: str, observation_id: str, observation_update_data: ObservationUpdate) -> Optional[Observation]:
    """Updates an existing observation for a patient."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_OBSERVATIONS_SUBCOLLECTION).document(observation_id)

    update_data = observation_update_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_observation(patient_id, observation_id)

    update_data["updated_at"] = utcnow()
    await doc_ref.update(update_data)

    updated_snapshot = await doc_ref.get()
    if updated_snapshot.exists:
        return Observation(observation_id=updated_snapshot.id, **updated_snapshot.to_dict())
    return None

async def delete_observation(patient_id: str, observation_id: str) -> bool:
    """Deletes an observation for a patient."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_OBSERVATIONS_SUBCOLLECTION).document(observation_id)
    await doc_ref.delete()
    return True


# --- MedicationStatement Service Functions (Subcollection of PatientProfile) ---

async def create_medication_statement(patient_id: str, statement_data: MedicationStatementCreate) -> MedicationStatement:
    """Creates a new medication statement for a patient in a subcollection."""
    if statement_data.subject_patient_id != patient_id:
        statement_data.subject_patient_id = patient_id

    subcollection_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_MEDICATION_STATEMENTS_SUBCOLLECTION)
    current_time = utcnow()

    doc_data = statement_data.model_dump(exclude_unset=True)
    doc_data["created_at"] = current_time
    doc_data["updated_at"] = current_time

    _timestamp, doc_ref = await subcollection_ref.add(doc_data) # Firestore auto-generates medication_statement_id

    final_data = statement_data.model_dump()
    final_data["medication_statement_id"] = doc_ref.id
    final_data["created_at"] = current_time
    final_data["updated_at"] = current_time
    return MedicationStatement(**final_data)

async def get_medication_statement(patient_id: str, statement_id: str) -> Optional[MedicationStatement]:
    """Retrieves a specific medication statement for a patient."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_MEDICATION_STATEMENTS_SUBCOLLECTION).document(statement_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        return MedicationStatement(medication_statement_id=snapshot.id, **data)
    return None

async def list_medication_statements_for_patient(
    patient_id: str,
    limit: int = 20,
    order_by: str = "effectiveDateTime", # Common default
    descending: bool = True
) -> List[MedicationStatement]:
    """Lists medication statements for a specific patient."""
    subcollection_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_MEDICATION_STATEMENTS_SUBCOLLECTION)
    direction = Query.DESCENDING if descending else Query.ASCENDING
    # Note: effectiveDateTime might be null. Firestore order_by on nullable fields needs care.
    # If ordering by a field that might be null, ensure Firestore indexes handle this or choose a non-null field.
    # For now, assume effectiveDateTime is mostly populated or nulls sort predictably if allowed by index.
    query = subcollection_ref.order_by(order_by, direction=direction).limit(limit)

    statements = []
    async for snapshot in query.stream():
        if snapshot.exists:
            data = snapshot.to_dict()
            statements.append(MedicationStatement(medication_statement_id=snapshot.id, **data))
    return statements

async def update_medication_statement(patient_id: str, statement_id: str, statement_update_data: MedicationStatementUpdate) -> Optional[MedicationStatement]:
    """Updates an existing medication statement for a patient."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_MEDICATION_STATEMENTS_SUBCOLLECTION).document(statement_id)

    update_data = statement_update_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_medication_statement(patient_id, statement_id)

    update_data["updated_at"] = utcnow()
    await doc_ref.update(update_data)

    updated_snapshot = await doc_ref.get()
    if updated_snapshot.exists:
        return MedicationStatement(medication_statement_id=updated_snapshot.id, **updated_snapshot.to_dict())
    return None

async def delete_medication_statement(patient_id: str, statement_id: str) -> bool:
    """Deletes a medication statement for a patient."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_MEDICATION_STATEMENTS_SUBCOLLECTION).document(statement_id)
    await doc_ref.delete()
    return True


# --- AIContextualStore Service Functions ---

async def get_ai_contextual_store(patient_id: str) -> Optional[AIContextualStore]:
    """Retrieves the AI contextual store document for a patient."""
    doc_ref = db.collection(AI_CONTEXTUAL_STORES_COLLECTION).document(patient_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        # patient_id from the document ID is implicitly handled by AIContextualStore model if it expects patient_id.
        # Ensure the model correctly maps snapshot.id to its patient_id field if not automatically done.
        # AIContextualStore model has patient_id as a field, which should match snapshot.id.
        return AIContextualStore(**data) # Assumes 'patient_id' is in data and matches snapshot.id
    return None

async def create_or_replace_ai_contextual_store(patient_id: str, store_data: AIContextualStoreCreate) -> AIContextualStore:
    """Creates or replaces an AI contextual store document for a patient.
    This acts as an "upsert" operation, preserving created_at if the document already exists."""
    doc_ref = db.collection(AI_CONTEXTUAL_STORES_COLLECTION).document(patient_id)
    existing_snapshot = await doc_ref.get()
    current_time = utcnow()

    # Ensure patient_id from path is used, store_data.patient_id should match.
    # If store_data.patient_id can be different, validation or error handling might be needed.
    # For this implementation, we assume store_data.patient_id is correctly set to the path patient_id.
    doc_data_dict = store_data.model_dump(exclude_unset=True)
    doc_data_dict["patient_id"] = patient_id # Explicitly set patient_id from the path parameter
    doc_data_dict["updated_at"] = current_time

    if existing_snapshot.exists:
        existing_data = existing_snapshot.to_dict()
        doc_data_dict["created_at"] = existing_data.get("created_at", current_time)
    else:
        doc_data_dict["created_at"] = current_time

    await doc_ref.set(doc_data_dict) # .set() overwrites the document or creates it if it doesn't exist.

    # Construct the AIContextualStore object for return using the final document data
    # This includes patient_id, created_at, updated_at, and all fields from store_data
    return AIContextualStore(**doc_data_dict)


async def update_ai_contextual_store(patient_id: str, store_update_data: AIContextualStoreUpdate) -> Optional[AIContextualStore]:
    """Updates an existing AI contextual store document for a patient.
    If the document does not exist, returns None."""
    doc_ref = db.collection(AI_CONTEXTUAL_STORES_COLLECTION).document(patient_id)

    # Check for document existence first for a strict update
    # existing_doc = await doc_ref.get()
    # if not existing_doc.exists:
    #    return None # Or raise an error, depending on desired behavior

    update_data_dict = store_update_data.model_dump(exclude_unset=True)

    if not update_data_dict: # No fields to update
        return await get_ai_contextual_store(patient_id) # Return current state

    update_data_dict["updated_at"] = utcnow()

    try:
        await doc_ref.update(update_data_dict)
    except Exception as e: # google.cloud.exceptions.NotFound if doc doesn't exist with .update()
        # Depending on desired behavior, could log error, return None, or let exception propagate
        # For now, let's assume a failed update (e.g. doc not found) means None should be returned
        # This requires checking existence first or handling the specific exception from doc_ref.update
        # A simple way: check existence before update.
        check_doc = await doc_ref.get()
        if not check_doc.exists:
            return None # Document does not exist, cannot update
        await doc_ref.update(update_data_dict) # Try update again if it was a race, or handle error

    updated_snapshot = await doc_ref.get()
    if updated_snapshot.exists:
        return AIContextualStore(**updated_snapshot.to_dict())
    return None # Should ideally be caught by pre-check or specific exception handling

async def delete_ai_contextual_store(patient_id: str) -> bool:
    """Deletes the AI contextual store document for a patient."""
    doc_ref = db.collection(AI_CONTEXTUAL_STORES_COLLECTION).document(patient_id)
    await doc_ref.delete()
    # Deletion in Firestore is typically fire-and-forget.
    # To confirm, one could try to get() the doc afterwards.
    return True
