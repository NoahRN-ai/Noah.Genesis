# Agent Tools Documentation

This document provides an overview of the tools available to the agent, their schemas, and how they are integrated into the system.

## RAG (Retrieval Augmented Generation) Tool: `retrieve_knowledge_base`

**Purpose:** The RAG tool, registered with the LLM as `retrieve_knowledge_base` (this exact name is stored in the `RAG_TOOL_NAME` constant in `tool_definitions.py`), is designed to retrieve relevant information from a clinical knowledge base. The underlying Python implementation is the `async def retrieve_knowledge_base_tool` function. This tool helps in providing accurate, context-aware, and up-to-date factual information for medical queries.

**File Location:** `backend/app/agent/tools.py`
**Python Function Name:** `retrieve_knowledge_base_tool` (asynchronous: `async def`)
**LLM Registered Name:** `retrieve_knowledge_base` (via `RAG_TOOL_NAME`)

### Input Schema (for Python function)

The `retrieve_knowledge_base_tool` Python function expects input according to the `RAGQueryInputArgs` Pydantic schema (defined in `tools.py`):

```python
# From backend/app/agent/tools.py
from pydantic import BaseModel, Field

class RAGQueryInputArgs(BaseModel):
    query: str = Field(description="The specific question, topic, or keywords to search for in the clinical knowledge base.")
```

- **`query` (str)**: This field should contain a clear, natural language question or a concise topic for searching the clinical knowledge base (e.g., 'What are the current sepsis bundle guidelines?'). An empty or whitespace-only query will result in an error by the tool.

Note: For LLM function calling, a similar Pydantic model `RAGQueryInput` is defined in `tool_definitions.py` to structure the parameters provided to the LLM.

### Return Values

The `retrieve_knowledge_base_tool` function returns a `List[Dict[str, Any]]`. The structure of the return value can be:
- **Successful Retrieval:** A list of dictionaries, where each dictionary represents a retrieved chunk of information (e.g., `[{"id": "...", "chunk_text": "...", "source_document_name": "...", "score": 0.85}, ...]`).
- **No Chunks Found:** An empty list (`[]`) if no relevant chunks are found for the query.
- **Error During Execution:** A list containing a single dictionary with an error key (e.g., `[{"error": "Query cannot be empty..."}]` or `[{"error": "Failed to retrieve information..."}]`) if an issue occurs, such as an invalid query or an internal error during retrieval.

### LLM Integration (Vertex AI Function Calling)

The RAG tool is defined for the LLM using specific Vertex AI classes. The definition is located in `backend/app/agent/tool_definitions.py` and is part of the `AVAILABLE_TOOLS_SCHEMAS_FOR_LLM` list.

**Tool Definition for Vertex AI (`tool_definitions.py` excerpt):**
```python
# From backend/app/agent/tool_definitions.py
from pydantic import BaseModel, Field
from vertexai.generative_models import Tool as VertexTool, FunctionDeclaration

# Schema for LLM parameters (mirrors RAGQueryInputArgs from tools.py)
class RAGQueryInput(BaseModel):
    query: str = Field(description="The specific question, topic, or keywords to search for in the clinical knowledge base. This should be a well-formed query derived from the user's current request.")

RAG_TOOL_NAME = "retrieve_knowledge_base"

rag_tool_vertex_declaration = VertexTool(
    function_declarations=[
        FunctionDeclaration(
            name=RAG_TOOL_NAME,
            description=(
                "Searches the clinical knowledge base to answer questions about critical care, "
                "medical protocols, patient guidelines, or other specific medical topics. "
                "Use this tool when the user's query requires specific factual information that is "
                "likely found within curated medical documents and is not general knowledge or part of common sense. "
                "For example, for queries like 'What are the current sepsis bundle guidelines?' "
                "or 'Tell me about managing ARDS protocol details'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The specific question, keywords, or topic to search for effectively in the knowledge base. Formulate a clear and concise search query based on the user's need for information from the clinical knowledge base."
                    }
                },
                "required": ["query"]
            }
        )
    ]
)

# AVAILABLE_TOOLS_SCHEMAS_FOR_LLM = [rag_tool_vertex_declaration]
```
The LLM uses this `VertexTool` definition (name, detailed description, and parameters schema) to understand when and how to correctly invoke the tool. The `parameters` directly define the JSON schema for the LLM.

### LangGraph Integration

The RAG tool (Python function `retrieve_knowledge_base_tool`) is executed within the LangGraph framework via a dedicated asynchronous node.

**Graph Node (`graph.py`):** `execute_rag_tool_node` (asynchronous: `async def`)

This node is responsible for:
1. Receiving the agent's current state (`AgentState`).
2. Extracting the query for the RAG tool from the state (e.g., from the latest message).
3. Asynchronously invoking the Python tool function: `await retrieve_knowledge_base_tool.ainvoke({"query": query})`.
4. Processing the returned `List[Dict[str, Any]]`.
5. Updating the `AgentState`'s `rag_output: List[Dict[str, Any]]` field with these results.

The `rag_output` is then available for subsequent nodes in the graph.

### Data Fidelity and Context
The RAG tool plays a crucial role in maintaining data fidelity by:
- **Grounding Responses:** Ensuring that the agent's responses are based on information from the verified knowledge base rather than solely on the LLM's parametric memory.
- **Reducing Hallucinations:** By providing relevant context, the tool helps minimize the chances of the LLM generating incorrect or fabricated information.
- **Access to Current Information:** If the knowledge base is kept up-to-date, the RAG tool allows the agent to access and utilize the latest information, which the LLM's training data might not include.

Regular updates to the underlying vector database or knowledge source are essential to ensure the continued accuracy and relevance of the information retrieved by this tool.
