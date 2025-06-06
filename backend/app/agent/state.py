from typing import TypedDict, Annotated, Sequence, List, Any, Optional
import operator
from langchain_core.messages import BaseMessage # For messages
# Assuming PydanticToolResponse and PydanticToolCall are in firestore_models
from backend.app.models.firestore_models import PydanticToolResponse, ToolCall as PydanticToolCall

# Define a more specific type for llm_response_with_actions if possible,
# for now, using Any. It might be a Pydantic model or a LangChain specific type.
# from langchain_core.agents import AgentActionMessageLog # Example if it's a list of AgentActionMessageLog

class AgentState(TypedDict):
    # Existing fields (or anticipated from previous context)
    messages: Annotated[Sequence[BaseMessage], operator.add]
    session_id: str

    # New fields required by the updated execute_rag_tool_node from Chunk 3
    llm_response_with_actions: Any # Replace Any with a more specific type if known (e.g., AIMessage or a Pydantic model)

    # To store the direct output from tool execution (List[Dict] for RAG, or other types for other tools)
    # This was previously rag_output: List[Dict[str, Any]] but now more generic for multiple tools
    executed_tool_responses: List[PydanticToolResponse] # Stores PydanticToolResponse objects

    rag_context: List[str] # Specifically for RAG tool's output (list of text chunks or error/info messages)

    error_message: Optional[str] # Accumulates error messages, initialize with None or ""

    # For logging the agent's turn, as Pydantic models
    agent_turn_tool_calls: List[PydanticToolCall]
    agent_turn_tool_responses: List[PydanticToolResponse] # Re-uses PydanticToolResponse

    # You might have other fields, e.g.:
    # current_user_query: Optional[str]
    # final_response: Optional[str]
    # etc.
