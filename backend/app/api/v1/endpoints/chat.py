import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.models.api_models import ChatRequest, ChatResponse
from backend.app.core.security import UserInfo, get_current_active_user
from backend.app.agent.memory import save_interaction # For user message
from backend.app.models.firestore_models import InteractionActor
from backend.app.agent.graph import agent_graph # Import the compiled graph
from backend.app.agent.state import AgentState # Import the state definition
from backend.app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("", response_model=ChatResponse)
async def handle_chat_message(
    request: ChatRequest,
    current_user: UserInfo = Depends(get_current_active_user)
):
    """
    Handles incoming user chat messages, invokes the LangGraph agent,
    and returns the AI agent's response.
    """
    session_id = request.session_id or str(uuid.uuid4()) # Use provided or generate new session ID
    user_id = current_user.user_id

    logger.info(f"Chat request for session_id: {session_id}, user_id: {user_id}, query: '{request.user_query_text[:70]}...'")

    # 1. Save user's message to interaction history BEFORE invoking the graph
    try:
        user_interaction = await save_interaction(
            session_id=session_id,
            user_id=user_id,
            actor=InteractionActor.USER,
            message_content=request.user_query_text
            # No tool calls/responses for user messages
        )
        logger.info(f"User interaction saved (id: {user_interaction.interaction_id}) for session_id: {session_id}")
    except Exception as e:
        logger.error(f"Failed to save user message for session_id {session_id}: {e}", exc_info=True)
        # For MVP, log and continue. Consider if this should be a hard failure.
        # If history is critical for the agent's first response, could raise HTTPException here.

    # 2. Prepare initial state for the LangGraph agent
    # Ensure all keys defined in AgentState (even if Optional) are initialized if graph nodes expect them.
    initial_graph_state = AgentState(
        user_input=request.user_query_text,
        session_id=session_id,
        user_id=user_id,
        conversation_history=[], # Will be populated by 'get_session_history_node'
        llm_response_with_actions=None,
        executed_tool_responses=None,
        rag_context=None,
        final_response_text=None,
        error_message=None,
        agent_turn_tool_calls=None,
        agent_turn_tool_responses=None,
        agent_turn_interaction_id=None
    )

    # 3. Invoke the LangGraph agent
    try:
        logger.debug(f"Invoking agent_graph for session_id {session_id} with initial state: {initial_graph_state.get('user_input')}")
        # Configuration for recursion limit, etc., can be added here if needed
        # config = {"recursion_limit": settings.AGENT_MAX_ITERATIONS}
        final_state: AgentState = await agent_graph.ainvoke(initial_graph_state) #, config=config)
        logger.debug(f"Agent_graph invocation completed for session_id {session_id}. Final state keys: {final_state.keys()}")

        agent_response_text = final_state.get('final_response_text')
        graph_error_message = final_state.get('error_message') # Check for errors from within graph execution
        agent_interaction_id = final_state.get('agent_turn_interaction_id', "unknown_agent_interaction_id")

        if graph_error_message and not agent_response_text:
            # If graph explicitly set an error and no fallback response, use the error.
            logger.error(f"Agent graph returned an error for session_id {session_id}: {graph_error_message}")
            ai_text_response = graph_error_message # This might already be user-friendly
        elif not agent_response_text:
            logger.warning(f"Agent graph did not produce a 'final_response_text' for session_id {session_id}.")
            ai_text_response = "I'm not sure how to respond to that. Could you try rephrasing?"
        else:
            ai_text_response = agent_response_text
            if graph_error_message: # Log error even if there's a response
                 logger.warning(f"Agent graph produced a response but also an error for session_id {session_id}: {graph_error_message}")


        logger.info(f"Agent response for session_id {session_id}: '{ai_text_response[:100]}...' (Interaction ID: {agent_interaction_id})")

    except Exception as e:
        # This catches errors from the .ainvoke() call itself or unhandled exceptions within the graph.
        logger.error(f"Critical error during agent_graph invocation for session_id {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI agent encountered a critical processing error. Please try again later."
        )

    # The agent's turn (response, tool usage) is saved by the `save_agent_interaction_node` within the graph.
    # The `agent_interaction_id` from `final_state` refers to that saved record.

    return ChatResponse(
        agent_response_text=ai_text_response,
        session_id=session_id, # Return the session_id used (or generated)
        interaction_id=agent_interaction_id # ID of the agent's saved InteractionHistory entry
    )
