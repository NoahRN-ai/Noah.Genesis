# Agent Tools Documentation

This document provides an overview of the tools available to the agent, their schemas, and how they are integrated into the system.

## RAG (Retrieval Augmented Generation) Tool: `retrieve_knowledge_base_tool`

**Purpose:** The RAG tool, named `retrieve_knowledge_base_tool` (defined as `RAG_TOOL_NAME` in constants), is designed to retrieve relevant information from a clinical knowledge base to augment the agent's responses. This helps in providing more accurate, context-aware, and up-to-date factual information for medical queries.

**File Location:** `backend/app/agent/tools.py`
**Function Name:** `retrieve_knowledge_base_tool` (asynchronous: `async def`)

### Input Schema

The tool expects input according to the `RAGQueryInputArgs` Pydantic schema:

```python
from pydantic import BaseModel, Field

class RAGQueryInputArgs(BaseModel):
    query: str = Field(description="The specific question, topic, or keywords to search for in the clinical knowledge base.")
```

- **`query` (str)**: This field should contain a clear, natural language question or a concise topic for searching the clinical knowledge base (e.g., 'What are the current sepsis bundle guidelines?'). An empty or whitespace-only query will result in an error.

### Return Values

The `retrieve_knowledge_base_tool` function returns a `List[Dict[str, Any]]`. The structure of the return value can be:
- **Successful Retrieval:** A list of dictionaries, where each dictionary represents a retrieved chunk of information (e.g., `[{"id": "...", "chunk_text": "...", "source_document_name": "...", "score": 0.85}, ...]`).
- **No Chunks Found:** An empty list (`[]`) if no relevant chunks are found for the query.
- **Error During Execution:** A list containing a single dictionary with an error key (e.g., `[{"error": "Query cannot be empty..."}]` or `[{"error": "Failed to retrieve information..."}]`) if an issue occurs, such as an invalid query or an internal error during retrieval.

### LLM Integration (Vertex AI Function Calling)

The RAG tool is made available to the LLM via Vertex AI Function Calling. Its definition is specified in `backend/app/agent/tool_definitions.py`.

**Tool Definition (`tool_definitions.py` excerpt):**
```python
from pydantic import BaseModel, Field

class RAGQueryInputArgs(BaseModel):
    query: str = Field(description="The specific question, topic, or keywords to search for in the clinical knowledge base.")

RAG_TOOL_NAME = "retrieve_knowledge_base_tool"

rag_tool_definition = {
    "name": RAG_TOOL_NAME,
    "description": (
        "Searches the clinical knowledge base to answer questions about critical care, "
        "medical protocols, patient guidelines, or other specific medical topics. "
        "Use this tool when the user's query requires factual information that is "
        "likely found within the curated medical documents and is not general knowledge. "
        "For example, use for 'What are the current sepsis bundle guidelines?' or 'Tell me about managing ARDS.' "
        "The query should be a clear, natural language question or a concise topic."
    ),
    "input_schema": RAGQueryInputArgs
}
```
The LLM uses this definition (name, detailed description, and input schema) to understand when and how to correctly invoke the tool.

### LangGraph Integration

The RAG tool is executed within the LangGraph framework via a dedicated asynchronous node.

**Graph Node (`graph.py`):** `execute_rag_tool_node` (asynchronous: `async def`)

This node is responsible for:
1. Receiving the agent's current state (`AgentState`).
2. Extracting the query for the RAG tool from the state (e.g., from the latest message).
3. Asynchronously invoking the tool: `await retrieve_knowledge_base_tool.ainvoke({"query": query})`.
4. Processing the returned `List[Dict[str, Any]]` (which could be retrieved chunks, an empty list, or an error dictionary).
5. Updating the `AgentState`'s `rag_output: List[Dict[str, Any]]` field with these results.

The `rag_output` is then available for subsequent nodes in the graph, typically used by an LLM node to formulate a response grounded in the retrieved information.

### Data Fidelity and Context

The RAG tool plays a crucial role in maintaining data fidelity by:
- **Grounding Responses:** Ensuring that the agent's responses are based on information from the verified knowledge base rather than solely on the LLM's parametric memory.
- **Reducing Hallucinations:** By providing relevant context, the tool helps minimize the chances of the LLM generating incorrect or fabricated information.
- **Access to Current Information:** If the knowledge base is kept up-to-date, the RAG tool allows the agent to access and utilize the latest information, which the LLM's training data might not include.

Regular updates to the underlying vector database or knowledge source are essential to ensure the continued accuracy and relevance of the information retrieved by this tool.
