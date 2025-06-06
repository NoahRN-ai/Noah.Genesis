from fastapi import APIRouter, Depends, HTTPException, Path, status
import logging

from backend.app.models.api_models import UserProfileResponse, UserProfileUpdateInput
from backend.app.core.security import UserInfo, get_current_active_user
from backend.app.services.firestore_service import get_user_profile, update_user_profile
from backend.app.models.firestore_models import UserProfileUpdate

router = APIRouter()
logger = logging.getLogger(__name__)

PROFILE_USER_ID_DESC = "The User ID of the profile to manage. For MVP, should match authenticated user."

@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def read_user_profile(
    user_id: str = Path(..., description=PROFILE_USER_ID_DESC),
    current_user: UserInfo = Depends(get_current_active_user)
):
    """
    Retrieves a user's profile.
    Service layer (get_user_profile) will raise NotFoundError if not found.
    """
    if user_id != current_user.user_id:
        logger.warning(f"User {current_user.user_id} attempt to access profile for different user {user_id}.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this profile.")

    try:
        # get_user_profile now raises NotFoundError if not found, handled by global handler
        profile_doc = await get_user_profile(user_id=user_id)
        return UserProfileResponse.model_validate(profile_doc)
    except HTTPException: # Re-raise auth HTTP exceptions
        raise
    except Exception as e: # Catch any other unexpected errors from service layer not covered by AppException
        logger.error(f"Unexpected error reading user profile for {user_id}: {e}", exc_info=True)
        # This will be caught by the generic Exception handler in main.py if not an AppException
        # If it's a custom AppException (like OperationFailedError if get_user_profile changed), it's handled there.
        # For now, assume other unexpected errors are 500.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving the user profile.")


@router.put("/{user_id}/profile", response_model=UserProfileResponse)
async def update_user_profile_endpoint(
    update_data: UserProfileUpdateInput,
    user_id: str = Path(..., description=PROFILE_USER_ID_DESC),
    current_user: UserInfo = Depends(get_current_active_user)
):
    """
    Updates a user's profile.
    Service layer (update_user_profile) will raise NotFoundError or OperationFailedError.
    """
    if user_id != current_user.user_id:
        logger.warning(f"User {current_user.user_id} attempt to update profile for different user {user_id}.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this profile.")

    firestore_update_model = UserProfileUpdate.model_validate(update_data.model_dump(exclude_unset=True))

    try:
        if not firestore_update_model.model_dump(exclude_unset=True):
            logger.info(f"No update data provided for user profile {user_id}. Returning current profile.")
            # get_user_profile raises NotFoundError if profile doesn't exist.
            profile_doc = await get_user_profile(user_id=user_id)
            return UserProfileResponse.model_validate(profile_doc)

        # update_user_profile now raises NotFoundError or OperationFailedError
        updated_profile_doc = await update_user_profile(user_id=user_id, profile_update_data=firestore_update_model)
        return UserProfileResponse.model_validate(updated_profile_doc)
    except HTTPException: # Re-raise auth HTTP exceptions
        raise
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"Unexpected error updating user profile for {user_id}: {e}", exc_info=True)
        # This will be caught by the generic Exception handler in main.py
        # or specific AppException handlers.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating the user profile.")
