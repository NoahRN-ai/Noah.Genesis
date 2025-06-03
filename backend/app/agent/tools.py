import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# Assuming rag_service is in backend.app.services
# If this path is incorrect, it will need to be adjusted.
from backend.app.services import rag_service
# Assuming tool_definitions.py will be created or updated to have RAG_TOOL_NAME
# If this path is incorrect, or RAG_TOOL_NAME is not yet defined, this might cause issues.
from backend.app.agent.tool_definitions import RAG_TOOL_NAME
# Assuming config.py contains settings with RAG_TOP_K
# If this path is incorrect, or RAG_TOP_K is not defined, this will cause issues.
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# --- Pydantic Input Schema for the RAG Tool ---
class RAGQueryInputArgs(BaseModel):
    query: str = Field(description="The specific question, topic, or keywords to search for in the clinical knowledge base.")

# --- RAG Tool Implementation ---
@tool(name=RAG_TOOL_NAME, args_schema=RAGQueryInputArgs)
async def retrieve_knowledge_base_tool(query: str) -> List[Dict[str, Any]]:
    """
    Searches the clinical knowledge base to answer questions about critical care,
    medical protocols, patient guidelines, or other specific medical topics.
    Use this tool when the user's query requires factual information that is
    likely found within the curated medical documents and is not general knowledge.
    For example, use for 'What are the current sepsis bundle guidelines?' or 'Tell me about managing ARDS.'
    The query should be a clear, natural language question or a concise topic.
    """
    logger.info(f"RAG Tool '{RAG_TOOL_NAME}' invoked with query: '{query}'")
    if not query or not query.strip():
        logger.warning("RAG tool invoked with an empty or whitespace-only query.")
        return [{"error": "Query cannot be empty for knowledge base search."}]

    try:
        # Ensure rag_service and retrieve_relevant_chunks are structured as expected.
        # Specifically, rag_service.retrieve_relevant_chunks should be an async function.
        retrieved_chunks = await rag_service.retrieve_relevant_chunks(
            query_text=query,
            top_k=settings.RAG_TOP_K
        )

        if not retrieved_chunks:
            logger.info(f"RAG tool: No relevant chunks found for query: '{query}'")
            return [] # Return empty list to signify no results found

        logger.info(f"RAG tool: Retrieved {len(retrieved_chunks)} chunks for query: '{query}'")
        # rag_service.retrieve_relevant_chunks is expected to return List[Dict[str, Any]]
        # where each dict has "id", "chunk_text", "source_document_name", "score", etc.
        return retrieved_chunks
    except Exception as e:
        logger.error(f"Error during RAG tool ('{RAG_TOOL_NAME}') execution for query '{query}': {e}", exc_info=True)
        return [{"error": f"Failed to retrieve information from knowledge base due to an internal error: {str(e)}"}]

# To make this tool discoverable if building a list of LangChain tools (optional for current graph):
# available_langchain_tools = [retrieve_knowledge_base_tool]
