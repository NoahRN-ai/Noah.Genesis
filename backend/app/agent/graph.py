import logging
import json # For stringifying complex content if needed
from typing import List, Dict, Any, TypedDict, Annotated, Sequence # Ensure all are present
import operator # For AgentState if messages uses it
from langchain_core.messages import BaseMessage # For AgentState
from backend.app.agent.state import AgentState # New: This replaces the local AgentState TypedDict
from backend.app.models.firestore_models import PydanticToolResponse, ToolCall as PydanticToolCall # New
from backend.app.agent.tool_definitions import RAG_TOOL_NAME # New
from backend.app.agent.tools import retrieve_knowledge_base_tool # Existing

logger = logging.getLogger(__name__)

async def execute_rag_tool_node(state: AgentState) -> AgentState:
    logger.info(f"[Graph Node] execute_rag_tool_node for session: {state.get('session_id', 'N/A')}")
    ai_message_with_actions = state.get('llm_response_with_actions')

    current_turn_executed_tool_responses: List[PydanticToolResponse] = []
    current_turn_pydantic_tool_calls: List[PydanticToolCall] = []

    # Initialize rag_context and error_message if they might not be present, to ensure safe updates
    if 'rag_context' not in state:
        state['rag_context'] = []
    if 'error_message' not in state:
        state['error_message'] = ""

    if ai_message_with_actions and getattr(ai_message_with_actions, 'tool_calls', None):
        for tool_call_request in ai_message_with_actions.tool_calls:
            tool_name = tool_call_request.get("name")
            tool_args_dict = tool_call_request.get("args", {})
            # Ensure tool_call_id_from_llm is a string, generate if not provided by LLM.
            # Some LLMs might not provide it, but LangChain tools often expect/generate it.
            # For direct PydanticToolResponse, it's good practice to have one.
            tool_call_id_from_llm = tool_call_request.get("id")
            if tool_call_id_from_llm is None:
                # Fallback if LLM does not provide an ID (though most do for function calling)
                tool_call_id_from_llm = f"call_{tool_name}_{json.dumps(tool_args_dict)}" # Simple unique enough ID
                logger.warning(f"Tool call for '{tool_name}' did not have an ID from LLM. Generated: {tool_call_id_from_llm}")


            current_turn_pydantic_tool_calls.append(
                PydanticToolCall(name=tool_name, args=tool_args_dict, id=tool_call_id_from_llm)
            )

            if tool_name == RAG_TOOL_NAME:
                try:
                    logger.info(f"Invoking RAG tool '{RAG_TOOL_NAME}' with args: {tool_args_dict} (Call ID: {tool_call_id_from_llm}) for session {state.get('session_id', 'N/A')}")
                    # Ensure tool_args_dict is correctly passed. If retrieve_knowledge_base_tool expects specific args like {"query": "..."},
                    # and tool_args_dict is already that, then it's fine.
                    # If tool_args_dict is {"arg_name": "value"} and tool expects {"query": "value"}, ensure mapping or correct LLM output.
                    # Assuming tool_args_dict is directly usable by .ainvoke()
                    tool_output_content: List[Dict[str, Any]] = await retrieve_knowledge_base_tool.ainvoke(tool_args_dict)

                    current_turn_executed_tool_responses.append(PydanticToolResponse(
                        tool_call_id=tool_call_id_from_llm,
                        name=tool_name,
                        content=tool_output_content # content is List[Dict[str, Any]]
                    ))

                    if isinstance(tool_output_content, list) and tool_output_content:
                        # Check if the first item in the list indicates an error from the tool itself
                        first_item = tool_output_content[0]
                        if isinstance(first_item, dict) and "error" in first_item:
                            error_msg = first_item["error"]
                            logger.warning(f"RAG tool '{RAG_TOOL_NAME}' (Call ID: {tool_call_id_from_llm}) returned an error: {error_msg} for session {state.get('session_id', 'N/A')}")
                            state['rag_context'] = [f"Information retrieval failed: {error_msg}"]
                            state['error_message'] = (state.get('error_message', "") + f" RAG Error: {error_msg};").strip()
                        else:
                            # Successfully retrieved chunks
                            state['rag_context'] = [chunk.get('chunk_text', '') for chunk in tool_output_content if isinstance(chunk, dict) and chunk.get('chunk_text')]
                            logger.info(f"RAG tool '{RAG_TOOL_NAME}' (Call ID: {tool_call_id_from_llm}) successfully retrieved {len(state['rag_context'])} text chunks for session {state.get('session_id', 'N/A')}.")
                    elif isinstance(tool_output_content, list) and not tool_output_content:
                         logger.info(f"RAG tool '{RAG_TOOL_NAME}' (Call ID: {tool_call_id_from_llm}) found no relevant information for session {state.get('session_id', 'N/A')}.")
                         state['rag_context'] = ["No specific information was found for your query in the knowledge base."] # Provide a user-friendly message
                    else:
                        # Unexpected format from the tool
                        logger.error(f"RAG tool '{RAG_TOOL_NAME}' (Call ID: {tool_call_id_from_llm}) returned unexpected output format: {type(tool_output_content)} - {tool_output_content} for session {state.get('session_id', 'N/A')}")
                        state['rag_context'] = ["There was an issue processing information from the knowledge base due to an unexpected data format."]
                        state['error_message'] = (state.get('error_message', "") + " RAG tool unexpected output format;").strip()

                except Exception as e:
                    logger.error(f"Exception during RAG tool '{RAG_TOOL_NAME}' (Call ID: {tool_call_id_from_llm}) execution: {e}", exc_info=True)
                    # This is a critical error in the node/tool call itself
                    error_content_for_response = [{"error": f"Internal error executing RAG tool: {str(e)}"}]
                    current_turn_executed_tool_responses.append(PydanticToolResponse(
                        tool_call_id=tool_call_id_from_llm,
                        name=tool_name,
                        content=error_content_for_response
                    ))
                    state['rag_context'] = [f"An error occurred while trying to access the knowledge base: {str(e)}"]
                    state['error_message'] = (state.get('error_message', "") + f" RAG tool execution critical error: {str(e)};").strip()
            else:
                logger.warning(f"Tool '{tool_name}' (Call ID: {tool_call_id_from_llm}) requested by LLM is not handled by 'execute_rag_tool_node' for session {state.get('session_id', 'N/A')}.")
                # Still record the attempt and provide an error response for this specific tool call
                current_turn_executed_tool_responses.append(PydanticToolResponse(
                    tool_call_id=tool_call_id_from_llm,
                    name=tool_name,
                    content=[{"error": "Tool not implemented or recognized in this execution path."}] # Content is List[Dict]
                ))
        else:
            logger.info(f"No tool calls found in 'llm_response_with_actions' for tool execution in session {state.get('session_id', 'N/A')}.")
            # If no tool calls, rag_context might remain empty or be explicitly set to empty.
            # state['rag_context'] = [] # Ensure it's empty if no RAG tool was called and it wasn't initialized.

        # Update state with all tool calls and their responses for this turn
        state['executed_tool_responses'] = (state.get('executed_tool_responses', []) + current_turn_executed_tool_responses)
        state['agent_turn_tool_calls'] = (state.get('agent_turn_tool_calls', []) + current_turn_pydantic_tool_calls)
        state['agent_turn_tool_responses'] = (state.get('agent_turn_tool_responses', []) + current_turn_executed_tool_responses)

        return state

# Placeholder for graph definition using StateGraph or similar
# from langgraph.graph import StateGraph, END
# Ensure this graph is correctly set up to handle async node functions.
#
# Example (illustrative, adapt to your full graph structure):
# workflow = StateGraph(AgentState)
# workflow.add_node("rag_tool_executor", execute_rag_tool_node)
# # ... other nodes (e.g., LLM call that uses rag_output)
# # ... define entry point and edges
# # workflow.set_entry_point("some_entry_node")
# # workflow.add_edge("some_entry_node", "rag_tool_executor")
# # app = workflow.compile()

# If you are using LangServe, ensure the graph is compiled and exposed correctly.
