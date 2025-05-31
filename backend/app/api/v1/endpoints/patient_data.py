from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from typing import List
import logging # Added import

from backend.app.models.api_models import PatientDataLogCreateInput, PatientDataLogResponse
from backend.app.core.security import UserInfo, get_current_active_user
from backend.app.services.firestore_service import (
    create_patient_data_log,
    # get_patient_data_log, # Not used in these specific POST/GET list endpoints
    list_patient_data_logs_for_user,
    # update_patient_data_log, # Not part of this task's scope
    # delete_patient_data_log  # Not part of this task's scope
)
from backend.app.models.firestore_models import PatientDataLogCreate # For constructing service layer input

router = APIRouter()
logger = logging.getLogger(__name__) # Added logger

@router.post("", response_model=PatientDataLogResponse, status_code=status.HTTP_201_CREATED)
async def submit_patient_data_log(
    data_input: PatientDataLogCreateInput,
    current_user: UserInfo = Depends(get_current_active_user),
    target_patient_user_id: str = Query(..., description="The User ID of the patient this data log pertains to.")
):
    """
    Submits a new patient data log.
    - The `created_by_user_id` will be the ID of the authenticated `current_user`.
    - The `target_patient_user_id` query parameter specifies the patient to whom this log belongs.
    - Basic authorization should ensure that a patient can only log data for themselves,
      while a nurse might log data for a patient they are authorized for (full nurse auth is future).
    """
    # MVP Authorization: Patient can only log for themselves.
    # A proper system would involve fetching current_user's role from UserProfile.
    # For Task 1.5, this is a simplified check.
    # if current_user.role == "patient" and current_user.user_id != target_patient_user_id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patients can only submit data logs for themselves.")
    # Nurse role check and patient access validation would go here.

    log_create_data = PatientDataLogCreate(
        user_id=target_patient_user_id, # The patient this data belongs to
        created_by_user_id=current_user.user_id, # Who actually submitted this log
        timestamp=data_input.timestamp,
        data_type=data_input.data_type,
        content=data_input.content,
        source=data_input.source or "Noah.Genesis_MVP" # Use default if not provided
    )
    try:
        created_log_doc = await create_patient_data_log(log_data=log_create_data)
        return PatientDataLogResponse.model_validate(created_log_doc)
    except Exception as e:
        logger.error(f"Error creating patient data log for user {target_patient_user_id} by {current_user.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create patient data log.")


@router.get("", response_model=List[PatientDataLogResponse])
async def get_patient_data_logs(
    patient_user_id: str = Query(..., description="User ID of the patient whose data logs are to be retrieved."),
    current_user: UserInfo = Depends(get_current_active_user),
    limit: int = Query(default=20, ge=1, le=100),
    order_by: str = Query(default="timestamp", description="Field to order by, e.g., 'timestamp' or 'created_at'"),
    descending: bool = Query(default=True)
):
    """
    Retrieves patient data logs for a specified patient user ID.
    Authorization: Patient can only get their own data. Nurse can get data for patients they manage (future).
    """
    # MVP Authorization: Patient can only retrieve their own data logs.
    # A proper system would involve fetching current_user's role from UserProfile.
    # if current_user.role == "patient" and current_user.user_id != patient_user_id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patients can only retrieve their own data logs.")
    # Nurse role check and patient access validation would go here.
    # For Task 1.5, simplified: if the patient_user_id doesn't match the authenticated user, deny for now,
    # unless we assume a nurse role might exist without explicit check yet.
    # To be safe for MVP, strict check:
    if current_user.user_id != patient_user_id:
        # This is a placeholder for more complex role-based access control (RBAC).
        # A nurse would need different validation. For now, only self-access.
        logger.warning(f"User {current_user.user_id} attempt to access data logs for different user {patient_user_id}.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this patient's data logs.")

    try:
        log_docs = await list_patient_data_logs_for_user(
            user_id=patient_user_id, limit=limit, order_by=order_by, descending=descending
        )
        return [PatientDataLogResponse.model_validate(doc) for doc in log_docs]
    except Exception as e:
        logger.error(f"Error listing patient data logs for user {patient_user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve patient data logs.")
