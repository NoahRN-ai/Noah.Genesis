import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.models.api_models import ChatRequest, ChatResponse
from backend.app.core.security import UserInfo, get_current_active_user
from backend.app.agent.memory import save_interaction, load_session_history
from backend.app.services.llm_service import get_llm_response
from backend.app.models.firestore_models import InteractionActor
from backend.app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("", response_model=ChatResponse)
async def handle_chat_message(
    request: ChatRequest,
    current_user: UserInfo = Depends(get_current_active_user)
):
    """
    Handles incoming user chat messages, orchestrates interaction with the LLM
    and returns the AI agent's response.
    LLM service errors are now handled by global exception handlers.
    """
    session_id = request.session_id or str(uuid.uuid4())
    user_id = current_user.user_id

    # 1. Save user's message to interaction history
    try:
        await save_interaction(
            session_id=session_id,
            user_id=user_id,
            actor=InteractionActor.USER,
            message_content=request.user_query_text
        )
    except Exception as e:
        logger.error(f"Error saving user message to history for session {session_id}: {e}", exc_info=True)
        # Continue processing, but log the error.

    # 2. Load recent conversation history for context
    try:
        conversation_history_lc_messages = await load_session_history(session_id=session_id, limit=10)
    except Exception as e:
        logger.error(f"Error loading session history for session {session_id}: {e}", exc_info=True)
        conversation_history_lc_messages = [] # Proceed with no history if loading fails

    # 3. Get LLM response
    # Service `get_llm_response` now raises custom exceptions (LLMError, etc.) on failure.
    # These will be caught by global handlers in main.py.
    try:
        ai_text_response = await get_llm_response(
            prompt=request.user_query_text,
            conversation_history=conversation_history_lc_messages,
            llm_model_name=settings.DEFAULT_LLM_MODEL_NAME
        )
    except HTTPException: # Re-raise if get_llm_response or other code raises FastAPI's HTTPException directly
        raise
    except Exception as e: # Catch any other unexpected error from LLM call or this block
        logger.error(f"Critical error during LLM interaction for session {session_id}: {e}", exc_info=True)
        # This will be caught by the generic Exception handler in main.py if it's not an AppException
        # or by the AppException handler if it's a custom one (like LLMError).
        # If we want to ensure a 503 specifically for *any* error in this LLM path not already handled:
        # raise HTTPException(
        #     status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        #     detail="The AI agent is currently unavailable. Please try again later."
        # )
        # For now, let the global handlers manage the response based on the raised exception type.
        # If 'e' is already an AppException (like LLMError), it will be handled correctly.
        # If 'e' is a non-AppException, the generic handler in main.py will give a 500.
        # To force a 503 for *any* error here not already an HTTPException:
        if not isinstance(e, (HTTPException)): # Avoid re-wrapping HTTPExceptions
             raise HTTPException(
                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                 detail=f"The AI agent encountered an issue: {type(e).__name__}. Please try again later."
             ) from e
        raise # Re-raise if it was already an HTTPException or an AppException


    # 4. Save AI's response to interaction history
    try:
        agent_interaction = await save_interaction(
            session_id=session_id,
            user_id=user_id,
            actor=InteractionActor.AGENT,
            message_content=ai_text_response,
            tool_calls=None,
            tool_responses=None
        )
        interaction_id = agent_interaction.interaction_id
    except Exception as e:
        logger.error(f"Error saving agent message to history for session {session_id}: {e}", exc_info=True)
        interaction_id = "error_saving_agent_response"

    return ChatResponse(
        agent_response_text=ai_text_response,
        session_id=session_id,
        interaction_id=interaction_id
    )
