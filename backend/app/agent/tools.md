# Agent Tools for Project Noah MVP (`tools.py`)

This document describes the tools available to the Noah.AI agent, how they are defined, integrated into the LangGraph orchestration, and used by the LLM. For the MVP, the primary tool is focused on Retrieval Augmented Generation (RAG) to access a curated clinical knowledge base.

## 1. Overview of Tool Usage in LangGraph

Tools extend the capabilities of the Large Language Model (LLM) by allowing it to interact with external data sources or perform specific, pre-defined functions. In Project Noah, tools are crucial for enabling the agent to:
* Access and retrieve information from the specialized clinical knowledge base (via RAG).
* Provide factually grounded responses by referencing this curated data.

The agent's interaction with tools within the LangGraph framework generally follows this sequence:

1.  **LLM Decision (`llm_reasoner_node`):** The LLM analyzes the user's query and the conversation history. Using the descriptions of available tools (provided via Vertex AI Function Calling schemas from `tool_definitions.py`), it determines if a tool is necessary to fulfill the request.
2.  **Tool Invocation Request:** If a tool is deemed necessary, the LLM generates a structured request. This request specifies the tool's name and the required input arguments. This is captured in the `tool_calls` attribute of the `AIMessage` returned by the `llm_reasoner_node`.
3.  **Graph Routing (`should_execute_tools_router`):** The LangGraph's conditional router detects the tool call request in the `AIMessage` and directs the agent's state to the appropriate tool execution node.
4.  **Tool Execution (e.g., `execute_rag_tool_node`):** The designated graph node invokes the actual Python function for the requested tool (defined in `tools.py`), passing the arguments provided by the LLM.
5.  **Output Processing & State Update:** The tool's output is captured. This output, along with details of the tool call, is structured into `PydanticToolResponse` objects and stored in `AgentState.executed_tool_responses`. Specialized fields in the state, like `AgentState.rag_context`, are also populated with processed tool output (e.g., extracted text chunks for RAG).
6.  **LLM Synthesis (`llm_reasoner_node`):** The agent state, now augmented with the tool's output, is typically routed back to the `llm_reasoner_node`. The LLM uses this new information (provided as `ToolMessage` context from `executed_tool_responses`) to synthesize a final, informed response for the user.

## 2. RAG Tool: `retrieve_knowledge_base_tool`

This is the primary tool for the MVP, enabling the agent to query the clinical knowledge base.

* **Implementation File:** `backend/app/agent/tools.py`
* **Core Function:** `async def retrieve_knowledge_base_tool(query: str) -> List[Dict[str, Any]]`
* **LangChain Integration:** The function is decorated with `@tool` from `langchain_core.tools`. This decorator helps in:
    * Defining the tool's `name` for the LLM (`RAG_TOOL_NAME` from `tool_definitions.py`).
    * Specifying the input argument schema using a Pydantic model (`args_schema=RAGQueryInputArgs`).
    * Using the function's docstring as a description for the LLM, guiding its decision on when to use the tool.
* **Purpose:** To search the project-specific, curated clinical knowledge base (indexed in Vertex AI Vector Search as per Task 1.4) for information relevant to a given query. This allows the agent to provide answers grounded in trusted medical documents, rather than relying solely on its general pre-training.
* **Underlying Service Call:** Internally, this tool calls `await rag_service.retrieve_relevant_chunks(query_text=query, top_k=settings.RAG_TOP_K)` from `backend/app/services/rag_service.py`.

### 2.1. Input Schema (`RAGQueryInputArgs`)

The `retrieve_knowledge_base_tool` expects its arguments to conform to the `RAGQueryInputArgs` Pydantic schema, defined in `tools.py`:

```python
from pydantic import BaseModel, Field

class RAGQueryInputArgs(BaseModel):
    query: str = Field(description="The specific question, topic, or keywords to search for in the clinical knowledge base.")
```
-   **`query: str`**: This field should contain the natural language question or topic that the LLM formulates based on the user's request, intended for searching the knowledge base.

### 2.2. Output Structure

The `retrieve_knowledge_base_tool` function (and thus `rag_service.retrieve_relevant_chunks`) returns a list of dictionaries. Each dictionary represents a relevant text chunk retrieved from the knowledge base.

Example structure of a single dictionary item in the returned list:
```json
{
  "id": "unique_chunk_identifier_string",
  "chunk_text": "The actual content of the retrieved text chunk...",
  "source_document_name": "source_file_name.pdf_or_id",
  "score": 0.88,
  "metadata": { }
}
```
(Note: `score` is a relevance score from the vector search. `metadata` could include other details like page number, document title, etc.)

If no relevant chunks are found for the query, the tool returns an empty list (`[]`).
If an error occurs during the retrieval process, the tool returns a list containing a single dictionary indicating the error, for example: `[{"error": "Failed to retrieve information..."}]`.

### 2.3. LLM Awareness and Schema Definition

For the LLM to effectively use this tool, it must be aware of its existence, purpose, and how to call it (i.e., its input arguments).

*   **Vertex AI Tool Schema:** This is defined in `backend/app/agent/tool_definitions.py` as `rag_tool_vertex_declaration` (an instance of `vertexai.generative_models.Tool`). This object includes:
    *   `name`: Set to `RAG_TOOL_NAME` ("retrieve_knowledge_base").
    *   `description`: A detailed explanation for the LLM on what the tool does and when to use it (e.g., "Searches the clinical knowledge base... Use this tool when...").
    *   `parameters`: A JSON schema object defining the expected input arguments, which must align with `RAGQueryInputArgs` (e.g., requiring a `query` string).
*   **Provision to LLM:** The `get_available_tools_for_llm()` function in `tool_definitions.py` provides `rag_tool_vertex_declaration` to the `llm_reasoner_node`. This schema is then passed to `llm_service.get_llm_response()` when calling the Vertex AI LLM, enabling its function calling capability.

### 2.4. Invocation within LangGraph

*   **LLM Request:** The `llm_reasoner_node` gets an `AIMessage` from the LLM. If this message contains `tool_calls` with the name `RAG_TOOL_NAME`, the graph routes to `execute_rag_tool_node`.
*   **Execution in `execute_rag_tool_node`:**
    *   The node extracts the `args` dictionary (e.g., `{"query": "details on sepsis management"}`) from the LLM's tool call request.
    *   It then calls the RAG tool: `await retrieve_knowledge_base_tool.ainvoke(tool_args_dict)`. The `@tool` decorator ensures `tool_args_dict` is correctly parsed into the `query` argument for the underlying function.
*   **State Update:**
    *   The direct output from `retrieve_knowledge_base_tool.ainvoke()` (the list of chunk dictionaries or error list) is stored as the `content` field of a `PydanticToolResponse` object. This `PydanticToolResponse` is then added to the `AgentState.executed_tool_responses` list. This structured logging is important for tracing and for constructing `ToolMessage` objects for subsequent LLM calls.
    *   A simplified list, containing only the `chunk_text` strings from successfully retrieved chunks, is stored in `AgentState.rag_context`. This `rag_context` is often more convenient for direct inclusion in subsequent LLM prompts when synthesizing the final answer. If RAG fails or returns no results, `rag_context` will contain an appropriate message or an empty list.
    *   Details of the tool call (`PydanticToolCall`) and the response (`PydanticToolResponse`) are also temporarily stored in `agent_turn_tool_calls` and `agent_turn_tool_responses` respectively, for logging the complete agent turn in `save_agent_interaction_node`.

### 2.5. Supporting ALETHIA_FIDELITY_CONSTRAINT (Truthfulness and Traceability)

The RAG tool is a cornerstone for ensuring the agent's responses are truthful and grounded in reliable information. Key aspects include:

*   **Curated Knowledge Base:** The RAG system retrieves information exclusively from a project-defined, curated set of clinical documents, rather than the open internet or the LLM's general training data.
*   **Source Attribution:** The `rag_service.retrieve_relevant_chunks` function (and therefore the `retrieve_knowledge_base_tool`) is designed to return the `source_document_name` (and potentially other metadata like page numbers if available) for each retrieved text chunk.
*   **Availability to LLM:** This source information is part of the `tool_output_content` stored in `PydanticToolResponse` and can be implicitly available to the LLM if the `ToolMessage` content includes it, or explicitly if the prompt for synthesizing the answer (in `llm_reasoner_node` or a dedicated `response_generator_node`) instructs the LLM to refer to or cite sources from the provided `rag_context` or tool outputs.
*   **Future Enhancement:** For more explicit traceability, the system could be enhanced to:
    *   Always include source document names/links directly within the `rag_context` strings presented to the LLM.
    *   Specifically prompt the LLM to cite sources in its final answer when information is derived from RAG.
    *   Provide a UI mechanism for users to see the sources of information.

This tool integration strategy ensures that the Noah.AI agent can effectively leverage its RAG capabilities, with a focus on providing accurate, traceable, and contextually relevant information to users.
