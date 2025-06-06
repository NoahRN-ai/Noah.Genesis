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
from backend.app.core.exceptions import NotFoundError, OperationFailedError

# --- Firestore Client Initialization ---
db = AsyncClient()

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
    return UserProfile(user_id=user_id, created_at=current_time, updated_at=current_time, **profile_data.model_dump())

async def get_user_profile(user_id: str) -> UserProfile:
    """Retrieves a user profile document from Firestore by user_id."""
    doc_ref = db.collection(USER_PROFILES_COLLECTION).document(user_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        return UserProfile(user_id=snapshot.id, **data)
    raise NotFoundError(detail=f"User profile with ID '{user_id}' not found.")

async def update_user_profile(user_id: str, profile_update_data: UserProfileUpdate) -> UserProfile:
    """Updates an existing user profile document in Firestore."""
    doc_ref = db.collection(USER_PROFILES_COLLECTION).document(user_id)

    existing_doc_snapshot = await doc_ref.get()
    if not existing_doc_snapshot.exists:
        raise NotFoundError(detail=f"User profile with ID '{user_id}' not found for update.")

    update_data = profile_update_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_user_profile(user_id)

    update_data["updated_at"] = utcnow()
    await doc_ref.update(update_data)

    updated_snapshot = await doc_ref.get()
    if updated_snapshot.exists:
        return UserProfile(user_id=updated_snapshot.id, **updated_snapshot.to_dict())
    raise OperationFailedError(detail=f"Failed to re-fetch user profile '{user_id}' after update attempt.")

async def delete_user_profile(user_id: str) -> bool:
    """Deletes a user profile document from Firestore."""
    doc_ref = db.collection(USER_PROFILES_COLLECTION).document(user_id)
    await doc_ref.delete()
    return True


# --- PatientDataLog Service Functions ---

async def create_patient_data_log(log_data: PatientDataLogCreate) -> PatientDataLog:
    """Creates a new patient data log entry in Firestore with an auto-generated ID."""
    collection_ref = db.collection(PATIENT_DATA_LOGS_COLLECTION)
    current_time = utcnow()
    log_doc_data = log_data.model_dump(exclude_unset=True)
    log_doc_data["created_at"] = current_time
    log_doc_data["updated_at"] = current_time

    _update_time, doc_ref = await collection_ref.add(log_doc_data)
    return PatientDataLog(log_id=doc_ref.id, created_at=current_time, updated_at=current_time, **log_data.model_dump())

async def get_patient_data_log(log_id: str) -> PatientDataLog:
    """Retrieves a specific patient data log entry by its ID."""
    doc_ref = db.collection(PATIENT_DATA_LOGS_COLLECTION).document(log_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        return PatientDataLog(log_id=snapshot.id, **data)
    raise NotFoundError(detail=f"Patient data log with ID '{log_id}' not found.")

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
        if snapshot.exists:
            data = snapshot.to_dict()
            logs.append(PatientDataLog(log_id=snapshot.id, **data))
    return logs

async def update_patient_data_log(log_id: str, log_update_data: PatientDataLogUpdate) -> PatientDataLog:
    """Updates an existing patient data log entry."""
    doc_ref = db.collection(PATIENT_DATA_LOGS_COLLECTION).document(log_id)

    existing_doc_snapshot = await doc_ref.get()
    if not existing_doc_snapshot.exists:
        raise NotFoundError(detail=f"Patient data log with ID '{log_id}' not found for update.")

    update_data = log_update_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_patient_data_log(log_id)

    update_data["updated_at"] = utcnow()
    await doc_ref.update(update_data)

    updated_snapshot = await doc_ref.get()
    if updated_snapshot.exists:
        return PatientDataLog(log_id=updated_snapshot.id, **updated_snapshot.to_dict())
    raise OperationFailedError(detail=f"Failed to re-fetch patient data log '{log_id}' after update attempt.")

async def delete_patient_data_log(log_id: str) -> bool:
    """Deletes a patient data log entry."""
    doc_ref = db.collection(PATIENT_DATA_LOGS_COLLECTION).document(log_id)
    await doc_ref.delete()
    return True


# --- InteractionHistory Service Functions ---

async def create_interaction_history_entry(entry_data: InteractionHistoryCreate) -> InteractionHistory:
    """Creates a new interaction history entry in Firestore with an auto-generated ID."""
    collection_ref = db.collection(INTERACTION_HISTORY_COLLECTION)
    current_time = utcnow()
    entry_doc_data = entry_data.model_dump(exclude_unset=True)
    entry_doc_data["timestamp"] = current_time
    _update_time, doc_ref = await collection_ref.add(entry_doc_data)
    return InteractionHistory(interaction_id=doc_ref.id, **entry_doc_data)


async def get_interaction_history_entry(interaction_id: str) -> InteractionHistory:
    """Retrieves a specific interaction history entry by its ID."""
    doc_ref = db.collection(INTERACTION_HISTORY_COLLECTION).document(interaction_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        return InteractionHistory(interaction_id=snapshot.id, **data)
    raise NotFoundError(detail=f"Interaction history entry with ID '{interaction_id}' not found.")

async def list_interaction_history_for_session(
    session_id: str,
    limit: int = 50,
    order_by: str = "timestamp",
    descending: bool = False
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


# --- PatientProfile Service Functions ---

async def create_patient_profile(patient_id: str, profile_data: PatientProfileCreate) -> PatientProfile:
    """Creates a new patient profile document in Firestore."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id)
    current_time = utcnow()
    profile_doc_data = profile_data.model_dump(exclude_unset=True)
    profile_doc_data["created_at"] = current_time
    profile_doc_data["updated_at"] = current_time
    await doc_ref.set(profile_doc_data)
    return PatientProfile(patient_id=patient_id, created_at=current_time, updated_at=current_time, **profile_data.model_dump())

async def get_patient_profile(patient_id: str) -> PatientProfile:
    """Retrieves a patient profile document from Firestore by patient_id."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        return PatientProfile(patient_id=snapshot.id, **data)
    raise NotFoundError(detail=f"Patient profile with ID '{patient_id}' not found.")

async def update_patient_profile(patient_id: str, profile_update_data: PatientProfileUpdate) -> PatientProfile:
    """Updates an existing patient profile document in Firestore."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id)

    existing_doc_snapshot = await doc_ref.get()
    if not existing_doc_snapshot.exists:
        raise NotFoundError(detail=f"Patient profile with ID '{patient_id}' not found for update.")

    update_data = profile_update_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_patient_profile(patient_id)

    update_data["updated_at"] = utcnow()
    await doc_ref.update(update_data)

    updated_snapshot = await doc_ref.get()
    if updated_snapshot.exists:
        return PatientProfile(patient_id=updated_snapshot.id, **updated_snapshot.to_dict())
    raise OperationFailedError(detail=f"Failed to re-fetch patient profile '{patient_id}' after update attempt.")

async def delete_patient_profile(patient_id: str) -> bool:
    """Deletes a patient profile document from Firestore."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id)
    await doc_ref.delete()
    return True

async def list_patient_profiles(
    limit: int = 20,
    order_by: str = "created_at",
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
    if observation_data.subject_patient_id != patient_id:
        observation_data.subject_patient_id = patient_id
    subcollection_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_OBSERVATIONS_SUBCOLLECTION)
    current_time = utcnow()
    doc_data = observation_data.model_dump(exclude_unset=True)
    doc_data["created_at"] = current_time
    doc_data["updated_at"] = current_time
    _timestamp, doc_ref = await subcollection_ref.add(doc_data)
    final_data = observation_data.model_dump()
    final_data["observation_id"] = doc_ref.id
    final_data["created_at"] = current_time
    final_data["updated_at"] = current_time
    return Observation(**final_data)

async def get_observation(patient_id: str, observation_id: str) -> Observation:
    """Retrieves a specific observation for a patient."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_OBSERVATIONS_SUBCOLLECTION).document(observation_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        return Observation(observation_id=snapshot.id, **data)
    raise NotFoundError(detail=f"Observation with ID '{observation_id}' for patient '{patient_id}' not found.")

async def list_observations_for_patient(
    patient_id: str,
    limit: int = 20,
    order_by: str = "effectiveDateTime",
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

async def update_observation(patient_id: str, observation_id: str, observation_update_data: ObservationUpdate) -> Observation:
    """Updates an existing observation for a patient."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_OBSERVATIONS_SUBCOLLECTION).document(observation_id)

    existing_doc_snapshot = await doc_ref.get()
    if not existing_doc_snapshot.exists:
        raise NotFoundError(detail=f"Observation with ID '{observation_id}' for patient '{patient_id}' not found for update.")

    update_data = observation_update_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_observation(patient_id, observation_id)

    update_data["updated_at"] = utcnow()
    await doc_ref.update(update_data)

    updated_snapshot = await doc_ref.get()
    if updated_snapshot.exists:
        return Observation(observation_id=updated_snapshot.id, **updated_snapshot.to_dict())
    raise OperationFailedError(detail=f"Failed to re-fetch observation '{observation_id}' for patient '{patient_id}' after update attempt.")

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
    _timestamp, doc_ref = await subcollection_ref.add(doc_data)
    final_data = statement_data.model_dump()
    final_data["medication_statement_id"] = doc_ref.id
    final_data["created_at"] = current_time
    final_data["updated_at"] = current_time
    return MedicationStatement(**final_data)

async def get_medication_statement(patient_id: str, statement_id: str) -> MedicationStatement:
    """Retrieves a specific medication statement for a patient."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_MEDICATION_STATEMENTS_SUBCOLLECTION).document(statement_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        return MedicationStatement(medication_statement_id=snapshot.id, **data)
    raise NotFoundError(detail=f"Medication statement with ID '{statement_id}' for patient '{patient_id}' not found.")

async def list_medication_statements_for_patient(
    patient_id: str,
    limit: int = 20,
    order_by: str = "effectiveDateTime",
    descending: bool = True
) -> List[MedicationStatement]:
    """Lists medication statements for a specific patient."""
    subcollection_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_MEDICATION_STATEMENTS_SUBCOLLECTION)
    direction = Query.DESCENDING if descending else Query.ASCENDING
    query = subcollection_ref.order_by(order_by, direction=direction).limit(limit)
    statements = []
    async for snapshot in query.stream():
        if snapshot.exists:
            data = snapshot.to_dict()
            statements.append(MedicationStatement(medication_statement_id=snapshot.id, **data))
    return statements

async def update_medication_statement(patient_id: str, statement_id: str, statement_update_data: MedicationStatementUpdate) -> MedicationStatement:
    """Updates an existing medication statement for a patient."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_MEDICATION_STATEMENTS_SUBCOLLECTION).document(statement_id)

    existing_doc_snapshot = await doc_ref.get()
    if not existing_doc_snapshot.exists:
        raise NotFoundError(detail=f"Medication statement with ID '{statement_id}' for patient '{patient_id}' not found for update.")

    update_data = statement_update_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_medication_statement(patient_id, statement_id)

    update_data["updated_at"] = utcnow()
    await doc_ref.update(update_data)

    updated_snapshot = await doc_ref.get()
    if updated_snapshot.exists:
        return MedicationStatement(medication_statement_id=updated_snapshot.id, **updated_snapshot.to_dict())
    raise OperationFailedError(detail=f"Failed to re-fetch medication statement '{statement_id}' for patient '{patient_id}' after update attempt.")

async def delete_medication_statement(patient_id: str, statement_id: str) -> bool:
    """Deletes a medication statement for a patient."""
    doc_ref = db.collection(NOAH_MVP_PATIENTS_COLLECTION).document(patient_id).collection(NOAH_MVP_MEDICATION_STATEMENTS_SUBCOLLECTION).document(statement_id)
    await doc_ref.delete()
    return True


# --- AIContextualStore Service Functions ---

async def get_ai_contextual_store(patient_id: str) -> AIContextualStore:
    """Retrieves the AI contextual store document for a patient."""
    doc_ref = db.collection(AI_CONTEXTUAL_STORES_COLLECTION).document(patient_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        return AIContextualStore(**data)
    raise NotFoundError(detail=f"AI contextual store for patient ID '{patient_id}' not found.")

async def create_or_replace_ai_contextual_store(patient_id: str, store_data: AIContextualStoreCreate) -> AIContextualStore:
    """Creates or replaces an AI contextual store document for a patient."""
    doc_ref = db.collection(AI_CONTEXTUAL_STORES_COLLECTION).document(patient_id)
    existing_snapshot = await doc_ref.get()
    current_time = utcnow()
    doc_data_dict = store_data.model_dump(exclude_unset=True)
    doc_data_dict["patient_id"] = patient_id
    doc_data_dict["updated_at"] = current_time

    if existing_snapshot.exists:
        existing_data = existing_snapshot.to_dict()
        doc_data_dict["created_at"] = existing_data.get("created_at", current_time)
    else:
        doc_data_dict["created_at"] = current_time

    await doc_ref.set(doc_data_dict)
    return AIContextualStore(**doc_data_dict)


async def update_ai_contextual_store(patient_id: str, store_update_data: AIContextualStoreUpdate) -> AIContextualStore:
    """Updates an existing AI contextual store document for a patient."""
    doc_ref = db.collection(AI_CONTEXTUAL_STORES_COLLECTION).document(patient_id)

    existing_doc_snapshot = await doc_ref.get()
    if not existing_doc_snapshot.exists:
        raise NotFoundError(detail=f"AI contextual store for patient ID '{patient_id}' not found for update.")

    update_data_dict = store_update_data.model_dump(exclude_unset=True)
    if not update_data_dict:
        return await get_ai_contextual_store(patient_id)

    update_data_dict["updated_at"] = utcnow()
    await doc_ref.update(update_data_dict)
    updated_snapshot = await doc_ref.get()
    if updated_snapshot.exists:
        return AIContextualStore(**updated_snapshot.to_dict())
    raise OperationFailedError(detail=f"Failed to re-fetch AI contextual store for patient ID '{patient_id}' after update attempt.")

async def delete_ai_contextual_store(patient_id: str) -> bool:
    """Deletes the AI contextual store document for a patient."""
    doc_ref = db.collection(AI_CONTEXTUAL_STORES_COLLECTION).document(patient_id)
    await doc_ref.delete()
    return True
