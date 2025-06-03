from typing import List, Optional, Dict, Any, TypedDict
from langchain_core.messages import BaseMessage, AIMessage
from backend.app.models.firestore_models import ToolCall as PydanticToolCall
from backend.app.models.firestore_models import ToolResponse as PydanticToolResponse

class AgentState(TypedDict, total=False):
    """
    Represents the state of the AI agent's conversation and reasoning process.
    `total=False` means keys are not required at instantiation.
    """
    # Core Identifiers
    user_input: str  # The latest input from the user
    session_id: str  # ID of the current session
    user_id: str     # ID of the current user

    # Conversation Context
    conversation_history: List[BaseMessage] # History of LangChain messages (e.g., HumanMessage, AIMessage, ToolMessage)

    # LLM Interaction & Tool Handling
    # AIMessage from LLM potentially containing tool calls (List[langchain_core.tools.ToolCall])
    # langchain_core.tools.ToolCall is a TypedDict: {'name': str, 'args': Dict, 'id': str}
    llm_response_with_actions: Optional[AIMessage]

    # Stores PydanticToolResponse objects after tools have been executed.
    # These correspond to the tool_calls requested by the llm_response_with_actions.
    executed_tool_responses: Optional[List[PydanticToolResponse]]

    # Specific Contexts
    rag_context: Optional[List[str]]  # Context retrieved from RAG, list of text chunks

    # Output & Errors
    final_response_text: Optional[str] # The final text response for the user
    error_message: Optional[str]     # Any error encountered during graph execution

    # For Persisting Agent's Turn
    # These fields help in saving the complete agent interaction, including tool usage.
    # PydanticToolCall objects decided by the LLM for the current turn.
    agent_turn_tool_calls: Optional[List[PydanticToolCall]]
    # PydanticToolResponse objects from actual tool execution for the current turn.
    agent_turn_tool_responses: Optional[List[PydanticToolResponse]]
    agent_turn_interaction_id: Optional[str] # Firestore ID of the saved agent InteractionHistory entry
