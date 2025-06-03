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

The RAG tool (Python function `retrieve_knowledge_base_tool`) is executed within the LangGraph framework by the `execute_rag_tool_node` (asynchronous: `async def`) located in `backend/app/agent/graph.py`. This node handles all tool executions requested by the LLM.

**Graph Node (`graph.py`):** `execute_rag_tool_node`

This node has the following key responsibilities when processing tool calls:

1.  **Receives Agent State:** Takes the current `AgentState` as input.
2.  **Processes LLM Tool Calls:**
    *   Retrieves the list of tool call requests from `state['llm_response_with_actions']`.
    *   For each requested tool call:
        *   Creates a `PydanticToolCall` object (from `tool_call_request.name`, `tool_call_request.args`, `tool_call_request.id`) and adds it to `state['agent_turn_tool_calls']` for logging.
        *   If the `tool_name` matches `RAG_TOOL_NAME` ("retrieve_knowledge_base"):
            *   Invokes the RAG tool asynchronously: `await retrieve_knowledge_base_tool.ainvoke(tool_args_dict)`.
3.  **Handles RAG Tool Output and Updates State:**
    *   The direct output from `retrieve_knowledge_base_tool.ainvoke()` (a `List[Dict[str, Any]]`) is stored as the `content` in a `PydanticToolResponse` object. This response object (along with those from any other tools called in the same turn) is added to `state['executed_tool_responses']` and `state['agent_turn_tool_responses']`.
    *   `state['rag_context']` (a `List[str]`) is populated based on the RAG tool's output:
        *   **Success:** Contains a list of `chunk_text` strings extracted from the successfully retrieved chunks.
        *   **RAG Error:** Contains a message like `["Information retrieval failed: <error_details>"]`.
        *   **No Results:** Contains a message like `["No specific information was found for your query in the knowledge base."]`.
        *   **Unexpected Output:** Contains a message like `["There was an issue processing information from the knowledge base."]`.
    *   `state['error_message']` (an `Optional[str]`) may be updated with details if errors occur during RAG tool execution or if the RAG tool itself returns an error.
4.  **Handles Other Tools:** If a tool call is not for `RAG_TOOL_NAME`, it logs a warning and appends an error `PydanticToolResponse` indicating the tool is not handled by this specific execution path (for MVP).
5.  **Returns Updated State:** The node returns the modified `AgentState`.

The `state['rag_context']` is then available for subsequent nodes in the graph, typically an LLM node, to formulate a response grounded in the retrieved information. The fields `agent_turn_tool_calls` and `agent_turn_tool_responses` are primarily for logging and traceability of the agent's actions.

### Data Fidelity and Context
The RAG tool plays a crucial role in maintaining data fidelity by:
- **Grounding Responses:** Ensuring that the agent's responses are based on information from the verified knowledge base rather than solely on the LLM's parametric memory.
- **Reducing Hallucinations:** By providing relevant context, the tool helps minimize the chances of the LLM generating incorrect or fabricated information.
- **Access to Current Information:** If the knowledge base is kept up-to-date, the RAG tool allows the agent to access and utilize the latest information, which the LLM's training data might not include.

Regular updates to the underlying vector database or knowledge source are essential to ensure the continued accuracy and relevance of the information retrieved by this tool.
