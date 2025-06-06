import logging  # Added import

from fastapi import APIRouter, Depends, HTTPException, Path, status

from backend.app.core.security import UserInfo, get_current_active_user
from backend.app.models.api_models import UserProfileResponse, UserProfileUpdateInput
from backend.app.models.firestore_models import (
    UserProfileUpdate,  # For constructing service layer input
)
from backend.app.services.firestore_service import get_user_profile, update_user_profile

router = APIRouter()
logger = logging.getLogger(__name__)  # Added logger

PROFILE_USER_ID_DESC = (
    "The User ID of the profile to manage. For MVP, should match authenticated user."
)


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def read_user_profile(
    user_id: str = Path(..., description=PROFILE_USER_ID_DESC),
    current_user: UserInfo = Depends(get_current_active_user),
):
    """Retrieves a user's profile.
    For MVP, users can only retrieve their own profile.
    Future: Admins/nurses might retrieve other profiles based on roles/permissions.
    """
    # MVP Authorization: User can only access their own profile.
    if user_id != current_user.user_id:
        logger.warning(
            f"User {current_user.user_id} attempt to access profile for different user {user_id}."
        )
        # TODO: Add role-based check here if nurses/admins can fetch other profiles in future.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this profile.",
        )

    try:
        profile_doc = await get_user_profile(user_id=user_id)
        if not profile_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found."
            )
        return UserProfileResponse.model_validate(profile_doc)
    except HTTPException:  # Re-raise known HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error reading user profile for {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve user profile.",
        )


@router.put("/{user_id}/profile", response_model=UserProfileResponse)
async def update_user_profile_endpoint(  # Renamed to avoid conflict with service
    update_data: UserProfileUpdateInput,
    user_id: str = Path(..., description=PROFILE_USER_ID_DESC),
    current_user: UserInfo = Depends(get_current_active_user),
):
    """Updates a user's profile.
    For MVP, users can only update their own profile.
    Future: Admins/nurses might update parts of other profiles based on roles/permissions.
    """
    # MVP Authorization: User can only update their own profile.
    if user_id != current_user.user_id:
        logger.warning(
            f"User {current_user.user_id} attempt to update profile for different user {user_id}."
        )
        # TODO: Add role-based check here if nurses/admins can update other profiles in future.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this profile.",
        )

    # Convert API model to Firestore service layer model if they differ significantly,
    # or if service expects specific Pydantic model type.
    # Here, UserProfileUpdateInput is designed to be compatible with UserProfileUpdate (Firestore model).
    firestore_update_model = UserProfileUpdate.model_validate(
        update_data.model_dump(exclude_unset=True)
    )

    if not firestore_update_model.model_dump(
        exclude_unset=True
    ):  # Check if there's anything to update
        logger.info(f"No update data provided for user profile {user_id}.")
        # Return current profile if no changes sent
        profile_doc = await get_user_profile(user_id=user_id)
        if not profile_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found."
            )
        return UserProfileResponse.model_validate(profile_doc)

    try:
        updated_profile_doc = await update_user_profile(
            user_id=user_id, profile_update_data=firestore_update_model
        )
        if not updated_profile_doc:
            # This case might occur if update_user_profile checks for existence and returns None
            # or if the document was deleted between a potential check and the update.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found for update, or update failed.",
            )
        return UserProfileResponse.model_validate(updated_profile_doc)
    except HTTPException:  # Re-raise known HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error updating user profile for {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update user profile.",
        )
