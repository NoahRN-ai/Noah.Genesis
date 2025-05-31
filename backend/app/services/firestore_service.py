from google.cloud.firestore_async import AsyncClient
from google.cloud.firestore import Query, AsyncWriteBatch # For typed queries if needed later
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from backend.app.models.firestore_models import (
    UserProfileCreate, UserProfileUpdate, UserProfile,
    PatientDataLogCreate, PatientDataLogUpdate, PatientDataLog,
    InteractionHistoryCreate, InteractionHistoryUpdate, InteractionHistory # InteractionHistoryUpdate might not be used if immutable
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
