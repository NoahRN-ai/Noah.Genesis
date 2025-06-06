import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.models.api_models import ChatRequest, ChatResponse
from backend.app.core.security import UserInfo, get_current_active_user
from backend.app.agent.memory import save_interaction, load_session_history
from backend.app.services.llm_service import get_llm_response
from backend.app.agents.hippocrates_agent import invoke_hippocrates_agent # New import
from backend.app.models.firestore_models import InteractionActor
# ToolCall and ToolResponse from firestore_models are named PydanticToolCall and PydanticToolResponse in the prompt output for chat.py
# but firestore_models.py itself defines them as ToolCall and ToolResponse.
# For consistency with firestore_models.py actual definitions, I'll use ToolCall and ToolResponse here.
# If they were meant to be aliased, that should happen in firestore_models or api_models.
# from backend.app.models.firestore_models import ToolCall as PydanticToolCall, ToolResponse as PydanticToolResponse
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
    (and eventually tools via LangGraph), and returns the AI agent's response.

    For Task 1.5 (MVP prior to full LangGraph integration in Phase 3):
    - It loads recent history.
    - Makes a direct call to the llm_service.
    - Saves the user message and AI response to history.
    - Full tool use and complex LangGraph orchestration will be added in Phase 3.
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
        # Continue processing, but log the error. History saving is important but shouldn't block response.

    # 2. Load recent conversation history for context
    try:
        conversation_history_lc_messages = await load_session_history(session_id=session_id, limit=10) # Limit context window
    except Exception as e:
        logger.error(f"Error loading session history for session {session_id}: {e}", exc_info=True)
        conversation_history_lc_messages = [] # Proceed with no history if loading fails

    # 3. Get LLM response (Simplified for Task 1.5 - direct call)
    #    Phase 3 will replace this with LangGraph invocation.
    #    For now, no complex tool schema passed, LLM responds based on text.

    ai_text_response = ""
    if request.mode == "hippocrates":
        logger.info(f"Using Hippocrates agent for session {session_id} with user query: '{request.user_query_text}'")
        try:
            # Ensure conversation_history_lc_messages is in the format List[dict] as expected by the agent
            # The load_session_history function should already return List[BaseMessage],
            # which might need conversion if HippocratesAgentState.conversation_history expects dicts.
            # For now, assuming it's compatible or Hippocrates agent handles it.
            # Example conversion if needed:
            # history_for_agent = [{"role": msg.type, "content": msg.content} for msg in conversation_history_lc_messages]

            ai_text_response = await invoke_hippocrates_agent(
                user_query=request.user_query_text,
                # TODO: Confirm format of conversation_history_lc_messages is List[Dict] or adapt.
                # Assuming load_session_history provides a list of BaseMessage-like objects that need conversion
                # to the List[Dict] format shown in hippocrates_agent.py's main_test.
                # If conversation_history_lc_messages is already List[Dict], no conversion is needed.
                # For this MVP, we'll pass it as is and adjust the agent or here later if format mismatch.
                conversation_history=[{"role": msg.type if hasattr(msg, 'type') else "unknown", "content": msg.content} for msg in conversation_history_lc_messages]

            )
            if not ai_text_response or "error" in ai_text_response.lower() or "Hippocrates Agent encountered an issue" in ai_text_response:
                 logger.warning(f"Hippocrates agent may have returned an empty or error response for session {session_id}: {ai_text_response}")
        except Exception as e:
            logger.error(f"Error calling Hippocrates agent for session {session_id}: {e}", exc_info=True)
            ai_text_response = f"Error: Hippocrates agent failed. {str(e)}" # Provide error info in response for MVP debugging

    else: # Default mode
        logger.info(f"Using default LLM for session {session_id} with user query: '{request.user_query_text}'")
        try:
            ai_text_response = await get_llm_response(
                prompt=request.user_query_text,
                conversation_history=conversation_history_lc_messages, # This is List[BaseMessage]
                llm_model_name=settings.DEFAULT_LLM_MODEL_NAME
                # tools_schema can be added here later when LangGraph orchestrates tool definitions
            )
            if ai_text_response.startswith("Error:"): # Handle errors from llm_service
                logger.error(f"LLM service error for session {session_id}: {ai_text_response}")
                # Let it be saved as is, and returned.
        except Exception as e:
            logger.error(f"Critical error calling default LLM service for session {session_id}: {e}", exc_info=True)
            # Consistent error handling with previous state, but consider if HTTPException is always desired
            # For MVP, returning an error message in the response might be more informative than a generic HTTP error.
            ai_text_response = f"Error: The default AI service encountered a problem. {str(e)}"
            # Re-raising HTTPException might be too disruptive if other parts of the flow can handle a text error.
            # raise HTTPException(
            #     status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            #     detail="The AI agent is currently unavailable. Please try again later."
            # )

    # 4. Save AI's response to interaction history
    try:
        # In this simplified flow, tool_calls and tool_responses are not generated by this direct LLM call.
        # These would be populated when LangGraph (with tool-using agents) is integrated.
        agent_interaction = await save_interaction(
            session_id=session_id,
            user_id=user_id, # The agent response is tied to the user's session
            actor=InteractionActor.AGENT,
            message_content=ai_text_response,
            tool_calls=None, # Placeholder for Phase 3
            tool_responses=None # Placeholder for Phase 3
        )
        interaction_id = agent_interaction.interaction_id
    except Exception as e:
        logger.error(f"Error saving agent message to history for session {session_id}: {e}", exc_info=True)
        interaction_id = "error_saving_agent_response" # Fallback ID

    return ChatResponse(
        agent_response_text=ai_text_response,
        session_id=session_id,
        interaction_id=interaction_id
    )
