from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List
import logging # Added import

from backend.app.models.api_models import SessionHistoryResponse, InteractionOutput
from backend.app.core.security import UserInfo, get_current_active_user
from backend.app.services.firestore_service import list_interaction_history_for_session
from backend.app.models.firestore_models import InteractionHistory as FirestoreInteractionHistoryModel

router = APIRouter()
logger = logging.getLogger(__name__) # Added logger

@router.get("/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    current_user: UserInfo = Depends(get_current_active_user),
    limit: int = Query(default=20, ge=1, le=100),
    # Add page_token: Optional[str] = Query(None) for cursor-based pagination later
):
    """
    Retrieves the interaction history for a given session ID.
    Ensures the authenticated user is associated with the session (or has rights to view it).
    """
    # Authorization check: Ensure current_user.user_id is allowed to view this session_id's history.
    # For MVP, we might assume user can only fetch their own sessions.
    # This would mean list_interaction_history_for_session might also need a user_id filter
    # or session_ids are globally unique and their ownership is checked.
    # Let's assume session_id is sufficient for now and firestore_service can filter by user_id internally if needed.
    # OR: A session document could exist linking session_id to user_id.
    # For now, `list_interaction_history_for_session` primarily filters by session_id.
    # An additional check to ensure `current_user.user_id` matches the `user_id` on the interactions
    # might be needed here or in the service layer for strictness, if history items are not already user-scoped by the query.

    try:
        # The service function already filters by session_id
        # We should ensure that user can only access *their* sessions.
        # One way is to ensure user_id is on all interaction_history docs and filter there,
        # or ensure session_id itself is user-scoped or checked for user ownership.
        # For now, list_interaction_history_for_session takes session_id.
        # We must make sure the user_id matches.

        history_docs: List[FirestoreInteractionHistoryModel] = await list_interaction_history_for_session(
            session_id=session_id, limit=limit, order_by="timestamp", descending=False # typically history is viewed oldest to newest
        )

        api_interactions: List[InteractionOutput] = []

        if not history_docs and session_id:
            # If no docs, we can't confirm user_id for auth, but if session_id is intended to be unique to user
            # we could raise a 404 if not owned, or return empty if owned.
            # To avoid complex lookup for just session existence vs auth, return empty for now.
            # Or, if the session is expected to exist, this might be a 404.
            # For MVP, returning empty list is acceptable if session has no history or doesn't exist.
            pass

        for doc in history_docs:
            # Perform authorization check: user can only access their own session history.
            if doc.user_id != current_user.user_id:
                # This indicates an attempt to access unauthorized data.
                # Log the attempt and raise a 403/404.
                logger.warning(f"User {current_user.user_id} attempted to access session {session_id} belonging to user {doc.user_id}.")
                # Depending on policy, either filter out these specific messages or deny access to the whole session history.
                # For strictness, if any part of the session doesn't match, deny all.
                # However, if `list_interaction_history_for_session` could also filter by user_id, that would be cleaner.
                # For now, let's assume a session is tied to one user. If the first record doesn't match, it's an issue.
                # This check should ideally be done on the query if possible.
                # If session_id is globally unique and not user-specific, this check becomes more important.
                # For now, let's assume sessions are user-specific and the first record check is okay for MVP.
                # A better approach would be to include user_id in the query to firestore_service if possible.
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, # Or 404 if we want to obscure session existence
                    detail="Not authorized to view this session history or session not found for this user."
                )
            api_interactions.append(InteractionOutput.model_validate(doc)) # Convert from Firestore model

        return SessionHistoryResponse(session_id=session_id, interactions=api_interactions)

    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        logger.error(f"Error retrieving history for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve session history.")
