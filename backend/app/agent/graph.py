import logging
from typing import TypedDict, Annotated, Sequence, List, Dict, Any
import operator
from langchain_core.messages import BaseMessage
# from langgraph.graph import StateGraph, END # Keep if you are defining the graph here

# Import the specific async tool function
from backend.app.agent.tools import retrieve_knowledge_base_tool

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # Add other state fields as needed
    rag_output: List[Dict[str, Any]] # Updated to store the list of dicts from the RAG tool

async def execute_rag_tool_node(state: AgentState) -> Dict[str, List[Dict[str, Any]]]:
    """
    Executes the RAG tool asynchronously and updates the agent state with the results.
    The results are a list of dictionaries, where each dictionary is a retrieved chunk
    or an error message.
    """
    logger.info("Executing RAG tool node...")
    messages = state.get('messages', []) # Use .get for safety

    # Simplified query extraction: assumes the last message content is the query.
    # Adapt this logic based on how your agent determines the query for the RAG tool.
    if not messages or not isinstance(messages[-1], BaseMessage) or not messages[-1].content:
        logger.warning("No valid query found in messages for RAG tool.")
        # Return a list with an error dictionary, matching the tool's error format
        return {"rag_output": [{"error": "No query found in messages for RAG tool."}]}

    query = str(messages[-1].content)
    logger.info(f"Query for RAG tool: '{query}'")

    try:
        # Asynchronously invoke the RAG tool
        # The tool itself handles empty query string, but good to be defensive here too.
        rag_results = await retrieve_knowledge_base_tool.ainvoke({"query": query})
        logger.info(f"RAG tool returned {len(rag_results)} items.")
        # The tool returns List[Dict[str, Any]], which could be empty or contain an error dict
        return {"rag_output": rag_results}
    except Exception as e:
        logger.error(f"Exception during RAG tool node execution: {e}", exc_info=True)
        # Return a list with an error dictionary, matching the tool's error format
        return {"rag_output": [{"error": f"Failed to execute RAG tool due to an internal error: {str(e)}"}]}

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
