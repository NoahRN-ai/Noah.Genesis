# Noah.AI Agent Orchestration (`backend/app/agent/`)

This directory contains the core logic for the Noah.AI agent, including its state management, memory mechanisms, tool definitions, and graph-based orchestration using LangGraph.

## 1. Overview

The Noah.RN agent is designed as a stateful conversational system built with LangGraph. Its primary capabilities for the MVP include:
* Maintaining short-term conversation history via Firestore.
* Reasoning using Large Language Models (LLMs) from Google Vertex AI.
* Utilizing a Retrieval Augmented Generation (RAG) tool to access a curated clinical knowledge base for factual grounding.
* Generating contextual and informed responses to user queries.
* Persisting interactions for audit and potential future fine-tuning.

The orchestration of these capabilities is managed by a `StateGraph` defined in `graph.py`.

## 2. Agent State (`state.py`)

The `AgentState` (a `TypedDict`) defines the data structure that flows through and is modified by the LangGraph nodes. Key fields include:

* `user_input: str`: The most recent message from the user.
* `session_id: str`: Identifier for the current conversation session.
* `user_id: str`: Identifier for the authenticated user making the request.
* `conversation_history: List[BaseMessage]`: A list of LangChain `BaseMessage` objects (e.g., `HumanMessage`, `AIMessage`, `ToolMessage`) representing the prior turns in the conversation. Loaded from Firestore.
* `llm_response_with_actions: Optional[AIMessage]`: The direct output from the LLM, which is an `AIMessage`. This message may contain textual content for the user and/or `tool_calls` (a list of `langchain_core.tools.ToolCall` dicts) if the LLM decides to use a tool.
* `executed_tool_responses: Optional[List[PydanticToolResponse]]`: A list of `PydanticToolResponse` objects. These store the actual outputs received after executing the tools requested by `llm_response_with_actions.tool_calls`. This is used to form `ToolMessage` objects for the next LLM reasoning step.
* `rag_context: Optional[List[str]]`: A list of text strings (chunks) retrieved by the RAG tool, to be used by the LLM for grounding its response.
* `final_response_text: Optional[str]`: The final textual response that will be sent to the user after all reasoning and tool use.
* `error_message: Optional[str]`: Captures any error messages encountered during the graph's execution, which can be surfaced to the user or logged.
* `agent_turn_tool_calls: Optional[List[PydanticToolCall]]`: Stores the `PydanticToolCall` representations of tools the LLM decided to invoke for the current agent turn. Used for persistent logging.
* `agent_turn_tool_responses: Optional[List[PydanticToolResponse]]`: Stores the `PydanticToolResponse` representations of the actual outcomes of tool executions for the current agent turn. Used for persistent logging.
* `agent_turn_interaction_id: Optional[str]`: The Firestore document ID where the agent's complete turn (final response, tool usage details) is saved via `memory.save_interaction()`.

## 3. Memory Management (`memory.py`)

Short-term memory is managed via Firestore, specifically the `interaction_history` collection.
* **`save_interaction()`**: Persists individual user messages or complete agent turns (including textual response, any tools called, and their outputs) to Firestore.
* **`load_session_history()`**: Retrieves recent conversation turns for a given session, converting them into LangChain `BaseMessage` objects to provide context to the LLM.

(More detailed STM/LTM strategies can be found in `backend/app/agent/memory.md` if it exists, or future LTM docs).

## 4. Tool Definitions (`tool_definitions.py`)

This file defines the tools available to the agent's LLM.
* **Tool Schemas:** For MVP, it primarily defines the `retrieve_knowledge_base` tool (RAG_TOOL_NAME). The schema is structured for compatibility with Vertex AI's function calling capabilities (`vertexai.generative_models.Tool` and `FunctionDeclaration`).
* **Helper Functions:**
    * `get_available_tools_for_llm()`: Provides the list of `VertexTool` schemas to the `llm_reasoner_node`.
    * `get_tool_names()`: Returns a list of string names for the available tools.

## 5. LangGraph Orchestration (`graph.py`)

The core agent logic is orchestrated by a `StateGraph` compiled from the following nodes and conditional edges.

### 5.1. Critical Dependency: `llm_service.py` Refactor

**IMPORTANT:** The `llm_reasoner_node` in `graph.py` **fundamentally relies on a refactored `llm_service.py` (from Task 1.3).** The `llm_service.get_llm_response()` function must be updated to:
1.  Accept `tools_schema: Optional[List[VertexTool]]` to inform the LLM about available function calls.
2.  Parse the LLM's response (e.g., from Vertex AI's `GenerateContentResponse.candidates[0].content.parts`) for both textual content and `FunctionCallPart` instances.
3.  Return a structured object (e.g., a Pydantic model like `LLMServiceOutput` or a dictionary) that separates `text_content: Optional[str]` from `tool_calls: Optional[List[Dict[str, Any]]]`. Each item in `tool_calls` must be a dictionary compatible with LangChain's `AIMessage(tool_calls=...)` constructor (i.e., `{'name': str, 'args': Dict, 'id': str}`).
Without this refactor, the agent will not be able to correctly identify or process tool usage requests from the LLM.

### 5.2. Graph Nodes

* **`get_session_history_node(state: AgentState) -> AgentState`**:
    * **Entry:** First operational node after initial state setup by the API.
    * **Action:** Loads recent conversation history from Firestore using `memory.load_session_history()` and populates `state['conversation_history']`. Handles errors by setting `state['error_message']`.
* **`llm_reasoner_node(state: AgentState) -> AgentState`**:
    * **Action:** The primary decision-making unit. It constructs a list of `BaseMessage` objects (including history, previous `ToolMessage` results, and current user input) and calls `llm_service.get_llm_response()`, providing the available tool schemas.
    * **Output:** Populates `state['llm_response_with_actions']` with an `AIMessage` containing the LLM's textual response and/or requested `tool_calls`. It also clears `executed_tool_responses` and `rag_context` from any previous iteration within the same graph invocation to prepare for new reasoning. Handles LLM call errors.
* **`execute_rag_tool_node(state: AgentState) -> AgentState`**:
    * **Trigger:** Invoked if the `llm_reasoner_node` requests the `RAG_TOOL_NAME`.
    * **Action:** Extracts the query from the `tool_calls` in `state['llm_response_with_actions']`. Calls `rag_service.retrieve_relevant_chunks()`.
    * **Output:** Populates `state['rag_context']` with retrieved text. Populates `state['executed_tool_responses']` with `PydanticToolResponse` objects (which will be used to create `ToolMessage`s for the next LLM call). It also populates `state['agent_turn_tool_calls']` and `state['agent_turn_tool_responses']` with Pydantic models for logging the current turn's tool usage.
* **`final_response_generation_node(state: AgentState) -> AgentState`**:
    * **Trigger:** Reached when the graph determines no more tool executions are needed for the current user query.
    * **Action:** Sets `state['final_response_text']` based on the content of `state['llm_response_with_actions']` (if it contains no further tool calls) or an error message if one occurred.
* **`save_agent_interaction_node(state: AgentState) -> AgentState`**:
    * **Action:** Persists the agent's complete turn to Firestore using `memory.save_interaction()`. This includes `state['final_response_text']`, `state.get('agent_turn_tool_calls')`, and `state.get('agent_turn_tool_responses')`.
    * **Output:** Populates `state['agent_turn_interaction_id']` with the Firestore ID of the saved interaction. Clears `agent_turn_tool_calls` and `agent_turn_tool_responses` post-saving.

### 5.3. Graph Edges and Control Flow

The graph defines the sequence and conditional transitions between nodes:

1.  **START** -> `get_session_history_node`
2.  `get_session_history_node` -> `llm_reasoner_node`
3.  `llm_reasoner_node` -> **`should_execute_tools_router` (Conditional Edge)**:
    * If `llm_response_with_actions` contains a call to `RAG_TOOL_NAME` -> `execute_rag_tool_node`
    * If `llm_response_with_actions` contains calls to other (future, unsupported for MVP) tools -> `generate_final_response_node` (with a message indicating tool unavailability).
    * If `llm_response_with_actions` contains no tool calls (direct answer) OR if a critical error is already in `state['error_message']` -> `generate_final_response_node`
4.  `execute_rag_tool_node` -> `llm_reasoner_node` (The graph loops back to the LLM to process the tool's output and decide the next action – a common ReAct pattern).
5.  `generate_final_response_node` -> `save_agent_interaction_node`
6.  `save_agent_interaction_node` -> **END**

### 5.4. Visual Diagram (Mermaid Syntax)

```mermaid
graph TD
    UserInput[User Input via /chat API] --> SaveUserMessage[API: Save User Message];
    SaveUserMessage --> PrepareInitialState[API: Prepare Initial AgentState];
    PrepareInitialState --> InvokeGraph[API: Invoke Agent Graph];

    subgraph Noah Agent Graph (LangGraph Execution)
        direction LR
        GraphStart[START] --> GetHistory(get_session_history_node);
        GetHistory --> LLMReasoner{llm_reasoner_node};
        LLMReasoner -- Tool Call for RAG? --> ExecuteRAG(execute_rag_tool_node);
        LLMReasoner -- No Tool / Direct Answer / Error --> GenerateFinalResponse(final_response_generation_node);
        ExecuteRAG -- Tool Output Ready --> LLMReasoner; subgraph ReAct Loop end
        GenerateFinalResponse --> SaveAgentInteraction(save_agent_interaction_node);
        SaveAgentInteraction --> GraphEnd[END];
    end

    InvokeGraph -- final_state (contains final_response_text) --> ReturnToUser[API: Return ChatResponse];
```

## 6. Integration with /chat API Endpoint (`chat.py`)

The `/chat` API endpoint in `backend/app/api/v1/endpoints/chat.py` orchestrates the interaction with the LangGraph agent:

*   Receives `ChatRequest` (user query, session ID).
*   Authenticates the user.
*   Saves the user's message to `InteractionHistory` via `memory.save_interaction()` **before** invoking the graph.
*   Prepares an initial `AgentState` with `user_input`, `session_id`, `user_id`, and other fields initialized to `None` or empty lists.
*   Invokes the compiled `agent_graph.ainvoke(initial_state)`.
*   Extracts `final_response_text` and `agent_turn_interaction_id` from the returned `final_state`. It also checks for `error_message`.
*   Constructs and returns a `ChatResponse` to the client. Note: The saving of the agent's specific turn (response, tools used) is handled by the `save_agent_interaction_node` within the graph itself.

This LangGraph setup provides a resilient and extensible foundation for the Noah.AI agent's conversational and reasoning capabilities for the MVP.
