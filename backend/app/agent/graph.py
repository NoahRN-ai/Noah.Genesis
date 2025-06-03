import logging
import json
import uuid # For generating tool call IDs if LLM doesn't provide them consistently

from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, ToolMessage
# langchain_core.tools.ToolCall is a TypedDict: {'name': str, 'args': Dict, 'id': str}

from backend.app.agent.state import AgentState
from backend.app.services import llm_service, rag_service # Assumes updated llm_service
from backend.app.agent import memory
from backend.app.models.firestore_models import InteractionActor, ToolCall as PydanticToolCall, ToolResponse as PydanticToolResponse
from backend.app.agent.tool_definitions import get_available_tools_for_llm, RAG_TOOL_NAME
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# --- Graph Nodes ---

async def get_session_history_node(state: AgentState) -> AgentState:
    logger.info(f"[Graph Node] get_session_history_node for session: {state['session_id']}")
    try:
        history = await memory.load_session_history(session_id=state['session_id'], user_id=state['user_id'], limit=settings.AGENT_HISTORY_LIMIT)
        state['conversation_history'] = history
        logger.debug(f"Loaded {len(history)} messages for session {state['session_id']}.")
    except Exception as e:
        logger.error(f"Error loading session history for {state['session_id']}: {e}", exc_info=True)
        state['error_message'] = f"Failed to load session history: {str(e)}"
        state['conversation_history'] = [] # Ensure it's an empty list on error
    return state

async def llm_reasoner_node(state: AgentState) -> AgentState:
    logger.info(f"[Graph Node] llm_reasoner_node for session: {state['session_id']}")
    if state.get('error_message') and not state.get('final_response_text'): # If critical error already, try to set final error response
        logger.warning(f"Skipping LLM reasoner due to prior error: {state['error_message']}")
        state['final_response_text'] = state['error_message'] # Ensure error is propagated
        state['llm_response_with_actions'] = AIMessage(content=state['error_message']) # Set a default AIMessage
        return state

    # Construct the prompt and message history for the LLM
    messages_for_llm: List[BaseMessage] = list(state.get('conversation_history', []))

    # Add tool responses from the previous turn as ToolMessages for context
    if state.get('executed_tool_responses'):
        for pydantic_tool_resp in state['executed_tool_responses']:
            # Ensure content is stringified for ToolMessage
            content_str = pydantic_tool_resp.content
            if not isinstance(content_str, str):
                try:
                    content_str = json.dumps(pydantic_tool_resp.content)
                except TypeError:
                    content_str = str(pydantic_tool_resp.content)

            messages_for_llm.append(ToolMessage(
                content=content_str,
                tool_call_id=pydantic_tool_resp.tool_call_id
            ))
        logger.debug(f"Added {len(state['executed_tool_responses'])} tool responses to LLM history.")

    # Add the current user input as the last message
    messages_for_llm.append(HumanMessage(content=state['user_input']))

    try:
        logger.debug(f"Calling LLM for session {state['session_id']}. History length for LLM: {len(messages_for_llm)}.")
        # Assumes llm_service.get_llm_response returns LLMServiceOutput(text_content: Optional[str], tool_calls: Optional[List[Dict]])
        # The 'tool_calls' from LLMServiceOutput should be a list of dicts {'name': ..., 'args': ..., 'id': ...}
        llm_output = await llm_service.get_llm_response(
            # Pass messages directly instead of a single 'prompt' string for chat models
            # `llm_service` needs to handle constructing the `contents` list for Vertex AI from these messages.
            messages_for_llm=messages_for_llm,
            # conversation_history is now part of messages_for_llm, `prompt` is user_input (last HumanMessage)
            llm_model_name=settings.DEFAULT_LLM_MODEL_NAME,
            tools_schema=get_available_tools_for_llm()
        )

        text_content = llm_output.text_content if llm_output.text_content is not None else ""

        # Ensure tool_calls have unique IDs if not provided by LLM or if needed for stricter tracking
        processed_tool_calls = []
        if llm_output.tool_calls:
            for tc in llm_output.tool_calls:
                processed_tool_calls.append({
                    "name": tc.get("name"),
                    "args": tc.get("args", {}),
                    "id": tc.get("id") or f"tool_{uuid.uuid4().hex[:8]}" # Ensure ID exists
                })

        state['llm_response_with_actions'] = AIMessage(
            content=text_content,
            tool_calls=processed_tool_calls # Use the processed list
        )
        # Reset contexts from previous iteration, as LLM will now use its new reasoning
        state['executed_tool_responses'] = None
        state['rag_context'] = None
        state['error_message'] = None # Clear any previous non-critical error message after successful LLM call
        logger.debug(f"LLM Reasoner Output for session {state['session_id']}: Text: '{text_content[:100]}...', Tool Calls: {processed_tool_calls}")

    except Exception as e:
        logger.error(f"Error in LLM reasoner node for session {state['session_id']}: {e}", exc_info=True)
        error_msg = f"AI model communication error: {str(e)}"
        state['error_message'] = error_msg
        state['llm_response_with_actions'] = AIMessage(content="I'm sorry, I encountered an error trying to process your request.")
        state['final_response_text'] = "I'm sorry, I encountered an error. Please try again." # Set final response on error
    return state

async def execute_rag_tool_node(state: AgentState) -> AgentState:
    logger.info(f"[Graph Node] execute_rag_tool_node for session: {state['session_id']}")
    ai_message_with_actions = state.get('llm_response_with_actions')
    executed_responses: List[PydanticToolResponse] = []
    # Store PydanticToolCall for logging with the agent's turn
    agent_turn_tool_calls: List[PydanticToolCall] = []


    if ai_message_with_actions and ai_message_with_actions.tool_calls:
        for tool_call_dict in ai_message_with_actions.tool_calls: # These are List[langchain_core.tools.ToolCall]
            tool_name = tool_call_dict.get("name")
            tool_args = tool_call_dict.get("args", {})
            tool_call_id = tool_call_dict.get("id") # This ID is from the AIMessage's tool_call

            # Log this intended tool call (Pydantic version)
            agent_turn_tool_calls.append(PydanticToolCall(name=tool_name, args=tool_args, id=tool_call_id))

            if tool_name == RAG_TOOL_NAME:
                try:
                    query = tool_args.get("query", "")
                    if not query:
                        logger.warning(f"RAG tool '{tool_name}' called with empty query for session {state['session_id']}.")
                        raise ValueError("Query for RAG tool cannot be empty.")

                    logger.info(f"Executing RAG tool '{tool_name}' with query: '{query[:100]}...' for session {state['session_id']}")
                    # rag_service returns List[Dict[str, Any]] where Dict has 'chunk_text', 'source_document_name'
                    retrieved_chunks_dicts = await rag_service.retrieve_relevant_chunks(query_text=query, top_k=settings.RAG_TOP_K)

                    retrieved_texts = [chunk['chunk_text'] for chunk in retrieved_chunks_dicts]
                    sources = [chunk.get('source_document_name', 'Unknown source') for chunk in retrieved_chunks_dicts]

                    # Update overall RAG context for the state (used by LLM in next step)
                    state['rag_context'] = retrieved_texts

                    tool_output_content = {
                        "retrieved_texts_count": len(retrieved_texts),
                        "retrieved_texts_preview": [text[:100] + "..." for text in retrieved_texts[:2]], # Preview
                        "sources_preview": sources[:2]
                    }
                    # The ToolMessage content should be a string, but LangChain also handles dicts which it might stringify.
                    # Let's provide a structured summary.
                    response_content_for_llm = f"Retrieved {len(retrieved_texts)} chunks. Preview: {json.dumps(tool_output_content)}"

                    executed_responses.append(PydanticToolResponse(
                        tool_call_id=tool_call_id, name=tool_name, content=response_content_for_llm
                    ))
                    logger.info(f"RAG tool '{tool_name}' executed for session {state['session_id']}, found {len(retrieved_texts)} chunks.")
                except Exception as e:
                    logger.error(f"Error executing RAG tool '{tool_name}' for session {state['session_id']}: {e}", exc_info=True)
                    error_content = f"Error in RAG tool: {str(e)}"
                    executed_responses.append(PydanticToolResponse(
                        tool_call_id=tool_call_id, name=tool_name, content=error_content
                    ))
                    state['error_message'] = (state.get('error_message', "") + f" RAG tool failed: {str(e)};").strip()
            else:
                logger.warning(f"Unknown tool '{tool_name}' requested by LLM for session {state['session_id']}.")
                executed_responses.append(PydanticToolResponse(
                    tool_call_id=tool_call_id, name=tool_name, content="Error: Tool not found or not implemented."
                ))
    else:
        logger.info(f"No tool calls found in 'llm_response_with_actions' for tool execution node (session {state['session_id']}).")

    state['executed_tool_responses'] = executed_responses
    state['agent_turn_tool_calls'] = agent_turn_tool_calls # Store the Pydantic versions of calls made this turn
    state['agent_turn_tool_responses'] = executed_responses # Store Pydantic versions of responses for this turn
    return state

async def final_response_generation_node(state: AgentState) -> AgentState:
    logger.info(f"[Graph Node] final_response_generation_node for session: {state['session_id']}")
    ai_message_with_actions = state.get('llm_response_with_actions')

    if state.get('error_message') and not state.get('final_response_text'):
        # If an error occurred in a previous node and wasn't handled by LLM re-reasoning
        state['final_response_text'] = state['error_message']
        logger.warning(f"Propagating error to final response for session {state['session_id']}: {state['error_message']}")
    elif ai_message_with_actions:
        # This node is hit when the router decides no more tools are needed.
        # The content of the AIMessage from the last llm_reasoner_node should be the final response.
        if not ai_message_with_actions.tool_calls: # Should be true if router sent here correctly
            state['final_response_text'] = ai_message_with_actions.content
        else:
            # This implies the router logic might be flawed or LLM is stuck in a tool loop.
            # For MVP, we'll take the text content anyway but log a warning.
            logger.warning(f"Final response node reached, but AIMessage still has tool_calls for session {state['session_id']}: {ai_message_with_actions.tool_calls}. Taking content as final.")
            state['final_response_text'] = ai_message_with_actions.content or "I performed some actions but couldn't form a final text response."
    else:
        # Should not happen if graph flows correctly
        state['final_response_text'] = "I'm sorry, I couldn't determine a final response for your request."
        logger.error(f"final_response_generation_node reached with no AIMessage and no error for session {state['session_id']}")

    logger.info(f"Final response for session {state['session_id']}: '{state.get('final_response_text', '')[:200]}...'")
    return state

async def save_agent_interaction_node(state: AgentState) -> AgentState:
    logger.info(f"[Graph Node] save_agent_interaction_node for session: {state['session_id']}")
    agent_response_text = state.get('final_response_text', "Agent did not produce a final text output.")

    # Tool calls and responses relevant to *this* agent's final textual response generation
    # These should have been populated by execute_rag_tool_node or other tool nodes before the final LLM reasoning
    # that produced final_response_text.
    tool_calls_for_turn = state.get('agent_turn_tool_calls')
    tool_responses_for_turn = state.get('agent_turn_tool_responses')

    try:
        saved_interaction = await memory.save_interaction(
            session_id=state['session_id'],
            user_id=state['user_id'],
            actor=InteractionActor.AGENT,
            message_content=agent_response_text,
            tool_calls=tool_calls_for_turn,
            tool_responses=tool_responses_for_turn
        )
        state['agent_turn_interaction_id'] = saved_interaction.interaction_id
        logger.info(f"Agent interaction saved for session {state['session_id']}, ID: {saved_interaction.interaction_id}")
    except Exception as e:
        logger.error(f"Error saving agent interaction for session {state['session_id']}: {e}", exc_info=True)
        # Append to existing error message or set new one
        current_error = state.get('error_message', "")
        state['error_message'] = (current_error + " Failed to save agent response.").strip()
        # Don't overwrite final_response_text if it was already set.
        if not state.get('final_response_text'):
            state['final_response_text'] = "An error occurred while saving my response."

    # Clear turn-specific tool data after saving
    state['agent_turn_tool_calls'] = None
    state['agent_turn_tool_responses'] = None
    return state

# --- Conditional Routing Logic ---

def should_execute_tools_router(state: AgentState) -> str:
    logger.info(f"[Graph Router] should_execute_tools_router for session: {state['session_id']}")
    ai_message = state.get('llm_response_with_actions')

    if state.get('error_message') and not state.get('final_response_text'): # If a critical error happened that prevented LLM response
        logger.warning(f"Router: Error detected ('{state['error_message']}'), routing to generate_final_response for session {state['session_id']}.")
        return "generate_final_response"

    if ai_message and ai_message.tool_calls and len(ai_message.tool_calls) > 0:
        # For MVP, we only expect RAG tool.
        # In a multi-tool setup, you'd inspect tc.name to route to different tool execution nodes.
        if any(tc.get("name") == RAG_TOOL_NAME for tc in ai_message.tool_calls):
            logger.info(f"Router: LLM decided to call RAG tool for session {state['session_id']}. Routing to execute_rag_tool.")
            return "execute_rag_tool"
        else:
            unsupported_tools = [tc.get("name") for tc in ai_message.tool_calls]
            logger.warning(f"Router: LLM requested unsupported/unknown tool(s) for session {state['session_id']}: {unsupported_tools}. Proceeding to generate text response.")
            # The AIMessage might have some text content even with tool calls.
            # If not, final_response_generation_node will handle default.
            return "generate_final_response"
    else:
        logger.info(f"Router: No tool calls from LLM for session {state['session_id']}. Routing to generate_final_response.")
        return "generate_final_response"

# --- Build the Graph ---

graph_builder = StateGraph(AgentState)

# Define nodes
graph_builder.add_node("get_session_history", get_session_history_node)
graph_builder.add_node("llm_reasoner", llm_reasoner_node)
graph_builder.add_node("execute_rag_tool", execute_rag_tool_node) # MVP: only one tool node
graph_builder.add_node("generate_final_response", final_response_generation_node)
graph_builder.add_node("save_agent_interaction", save_agent_interaction_node)

# Define edges
graph_builder.add_edge(START, "get_session_history")
graph_builder.add_edge("get_session_history", "llm_reasoner")

graph_builder.add_conditional_edges(
    "llm_reasoner",
    should_execute_tools_router,
    {
        "execute_rag_tool": "execute_rag_tool",
        "generate_final_response": "generate_final_response"
    }
)

# After tool execution, route back to LLM reasoner to process tool output
graph_builder.add_edge("execute_rag_tool", "llm_reasoner")

# After final response is decided, save it
graph_builder.add_edge("generate_final_response", "save_agent_interaction")

# After saving, end the graph flow
graph_builder.add_edge("save_agent_interaction", END)

# Compile the graph
agent_graph = graph_builder.compile()
logger.info("LangGraph agent graph compiled successfully for Project Noah.")

# Optional: For visualization if graphviz is installed and needed for debugging
# from langchain_core.utils.graph import print_ascii_graph
# print_ascii_graph(agent_graph)
