# This file makes 'services' a Python package.
from .firestore_service import (
    create_user_profile, get_user_profile, update_user_profile, delete_user_profile,
    create_patient_data_log, get_patient_data_log, list_patient_data_logs_for_user, update_patient_data_log, delete_patient_data_log,
    create_interaction_history_entry, get_interaction_history_entry, list_interaction_history_for_session
)
from .llm_service import get_llm_response
from .rag_service import retrieve_relevant_chunks # New import

__all__ = [
    "create_user_profile", "get_user_profile", "update_user_profile", "delete_user_profile",
    "create_patient_data_log", "get_patient_data_log", "list_patient_data_logs_for_user", "update_patient_data_log", "delete_patient_data_log",
    "create_interaction_history_entry", "get_interaction_history_entry", "list_interaction_history_for_session",
    "get_llm_response",
    "retrieve_relevant_chunks", # New export
]
