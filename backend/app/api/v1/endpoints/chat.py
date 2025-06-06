import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.models.api_models import ChatRequest, ChatResponse # LLMOutput is not directly returned by this endpoint
from backend.app.core.security import UserInfo, get_current_active_user
from backend.app.agent.memory import save_interaction, load_session_history
from backend.app.services.llm_service import get_llm_response # Returns LLMOutput
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
    The llm_service.get_llm_response now returns an LLMOutput object.
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
            # tool_calls and tool_responses are None for user messages
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
    # Service `get_llm_response` now returns an LLMOutput object and
    # raises custom exceptions (LLMError, etc.) on failure.
    # These will be caught by global handlers in main.py.
    try:
        llm_output = await get_llm_response( # Renamed variable
            prompt=request.user_query_text,
            conversation_history=conversation_history_lc_messages,
            llm_model_name=settings.DEFAULT_LLM_MODEL_NAME
            # tools_schema can be added here later when LangGraph orchestrates tool definitions
        )
    except HTTPException: # Re-raise if get_llm_response or other code raises FastAPI's HTTPException directly
        raise
    except Exception as e: # Catch any other unexpected error from LLM call or this block
        logger.error(f"Critical error during LLM interaction for session {session_id}: {e}", exc_info=True)
        if not isinstance(e, (HTTPException)):
             raise HTTPException(
                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                 detail=f"The AI agent encountered an issue: {type(e).__name__}. Please try again later."
             ) from e
        raise


    # 4. Save AI's response to interaction history
    try:
        agent_interaction = await save_interaction(
            session_id=session_id,
            user_id=user_id,
            actor=InteractionActor.AGENT,
            message_content=llm_output.text, # Use text part from LLMOutput
            tool_calls=llm_output.tool_calls, # Pass along tool_calls from LLMOutput
            tool_responses=None # Placeholder for Phase 3
        )
        interaction_id = agent_interaction.interaction_id
    except Exception as e:
        logger.error(f"Error saving agent message to history for session {session_id}: {e}", exc_info=True)
        interaction_id = "error_saving_agent_response" # Fallback ID

    # Determine the text to return in the API response
    # If LLM returned only tool_calls, text might be None.
    response_text = llm_output.text if llm_output.text is not None else ""

    return ChatResponse(
        agent_response_text=response_text, # Use potentially modified text
        session_id=session_id,
        interaction_id=interaction_id
    )
