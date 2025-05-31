# Agent Memory Mechanisms for Project Noah MVP

This document describes the Short-Term Memory (STM) and the explicitly simplified Long-Term Memory (LTM) mechanisms implemented for the Project Noah MVP AI agent. The design prioritizes functionality for the MVP while ensuring alignment with HIPAA considerations and leveraging `dynamous.ai` principles for efficiency.

## 1. Short-Term Memory (STM)

Short-Term Memory is essential for maintaining context within a single conversational session, allowing the agent to provide coherent, relevant, and multi-turn interactions.

### 1.1. STM Implementation: Firestore `InteractionHistory`

*   **Storage Medium:** STM is persisted in Google Cloud Firestore using the `interaction_history` collection. Each document within this collection meticulously records a single turn of a conversation (either a user's message or the agent's response).
*   **Data Model & Structure:** The schema for these documents is rigorously defined by the `InteractionHistory` Pydantic model (refer to `backend/app/models/firestore_models.py`). Key fields relevant to STM include:
    *   `interaction_id`: Unique ID for the interaction log entry (Firestore Document ID).
    *   `session_id`: Groups interactions belonging to the same conversational session.
    *   `user_id`: Identifies the user.
    *   `timestamp`: Server-set UTC timestamp indicating when the interaction was logged. Crucial for ordering.
    *   `actor`: (`USER` or `AGENT`) - Specifies the originator of the message.
    *   `message_content`: The textual content. For an agent, this can be its direct reply or a message accompanying tool calls.
    *   `tool_calls` (Agent only): A list of `ToolCall` Pydantic objects (`id: str`, `name: str`, `args: Dict[str, Any]`) if the agent decided to invoke tools. The `id` is a unique identifier for this specific tool invocation.
    *   `tool_responses` (Agent only): A list of `ToolResponse` Pydantic objects (`tool_call_id: str`, `name: str`, `content: Any`) representing the outcomes of the tools called. The `tool_call_id` links back to the `id` of the corresponding `ToolCall`.

### 1.2. Core Memory Functions for LangGraph (`backend/app/agent/memory.py`)

The STM is managed through the following core asynchronous functions, designed for seamless integration with LangGraph's state:

*   **`async def save_interaction(...) -> InteractionHistory`**
    *   **Purpose:** Persists a single interaction turn to the Firestore `interaction_history` collection.
    *   **Mechanism:** It accepts interaction details (session ID, user ID, actor, message content, and optional tool calls/responses as Pydantic models), constructs an `InteractionHistoryCreate` Pydantic object, and utilizes the `create_interaction_history_entry` service function from `firestore_service.py` to save it. The service layer ensures accurate timestamping for the record.
    *   **LangGraph Role:** LangGraph will invoke this function to record each step of the conversation (user input, agent response, tool execution results) as it unfolds.

*   **`async def load_session_history(session_id: str, limit: int = 20) -> List[BaseMessage]`**
    *   **Purpose:** Retrieves a sequence of recent interactions for a given `session_id` to serve as the conversational context for the LLM.
    *   **Mechanism:**
        1.  Queries Firestore (via `list_interaction_history_for_session`) for the `limit` most recent `InteractionHistory` documents for the `session_id`, sorted by their logging `timestamp` in descending order.
        2.  Reverses this list to ensure the messages are in **chronological order** (oldest of the retrieved recent messages first), which is the standard format expected by LLMs.
        3.  **Crucial Mapping to LangChain Messages:** Each `InteractionHistory` document is meticulously converted into a corresponding `langchain_core.messages.BaseMessage` object:
            *   If `entry.actor == InteractionActor.USER`: Mapped to `HumanMessage(content=entry.message_content)`.
            *   If `entry.actor == InteractionActor.AGENT`:
                *   Mapped to `AIMessage(content=entry.message_content, tool_calls=[...])`.
                *   The `tool_calls` attribute of `AIMessage` is populated by transforming each `PydanticToolCallModel` (from `entry.tool_calls`) into a dictionary with `id`, `name`, and `args`, as defined in our Pydantic model and expected by LangChain.
                *   If `entry.tool_responses` are present (logged with the same agent turn), each `PydanticToolResponseModel` is then converted into a `ToolMessage(content=stringified_output, tool_call_id=..., name=...)`. The `tool_call_id` from the `PydanticToolResponseModel` correctly links it to the original `ToolCall`'s `id`. The `content` of `ToolMessage` is JSON stringified if it's a dictionary.
    *   **LangGraph Role:** LangGraph will call this function to populate its state with the relevant conversation history before invoking the LLM or other agent components.

### 1.3. STM Efficiency & `dynamous.ai` Contributions

*   **Context Window Management (`dynamous.ai` MVP Strategy):** The `limit` parameter in `load_session_history` is the primary mechanism for controlling the size of the STM provided to the LLM. This directly impacts:
    *   **Performance:** Smaller context windows generally lead to faster LLM responses.
    *   **Cost:** LLM token usage is often proportional to context size.
    *   **Relevance:** Prevents overwhelming the LLM with very old, potentially irrelevant history for the current turn.
*   **Database-Side Filtering (`dynamous.ai` Efficiency):** Retrieving only the required `limit` of messages directly from Firestore is more efficient than fetching extensive history and truncating it in the application.
*   **Robust Message Mapping (`dynamous.ai` Clarity):** The explicit and careful mapping from stored Pydantic models (including the refined `ToolCall` with its `id` and `ToolResponse` with its `tool_call_id`) to LangChain's message types ensures that LangGraph receives state in the correct format. This is critical for reliable agent execution, especially for tool-using agents.
*   **Future `dynamous.ai` Enhancements (Post-MVP):** While not in MVP scope, `dynamous.ai` capabilities could later be applied to implement more sophisticated STM management, such as dynamic summarization of older conversation turns within the loaded history if performance or context quality with simple limiting becomes a bottleneck.

## 2. Long-Term Memory (LTM) - MVP Scope & Simplification

Project Noah MVP V1.0 adopts a **radically simplified approach to LTM** to ensure rapid development and focus on core features.

*   **Primary "Knowledge" LTM (Not Conversational): Retrieval Augmented Generation (RAG) - Task 1.4**
    *   The agent's ability to access and reason over a curated knowledge base of critical care clinical information via RAG will serve as its primary long-term *knowledge* store.
    *   This provides factual grounding for responses related to clinical topics but is **not** a memory of past user-specific conversations.

*   **Basic User-Specific Personalization LTM: `UserProfile.preferences` - Task 1.1**
    *   The `preferences: Dict[str, Any]` field within the `UserProfile` Firestore documents allows storing simple key-value preferences for each user.
    *   This data can be loaded and used to tailor LLM prompts or agent behavior (e.g., "Summarize information concisely as per user preference").
    *   This is a very basic form of persistent user-specific memory, not a comprehensive conversational LTM.

*   **Explicitly Out of Scope for MVP V1.0:**
    *   Advanced LTM solutions like `Mem0`.
    *   Vectorizing all past user interactions for semantic search-based conversational recall.
    *   Any form of autonomous "learning" or model fine-tuning based on individual user conversations during the MVP phase.

This focused LTM strategy aligns with the "BUILD\_WORKING\_MVP\_FAST" mandate and defers complexity, ensuring the MVP delivers core value effectively.

## 3. HIPAA and Data Privacy for Conversational Memory (STM)

The `InteractionHistory` stored in Firestore contains conversational data that is sensitive and may constitute Protected Health Information (PHI), depending on the content shared by users.

*   **Encryption:** All data in Firestore, including `InteractionHistory`, is encrypted at rest and in transit by Google Cloud by default.
*   **Access Control:**
    *   **IAM:** The backend service account (`sa-cloudrun-agent`) has restricted permissions to access Firestore (as defined in `terraform/project_iam.tf`).
    *   **Firestore Security Rules (Critical - Task 4.1):** Fine-grained security rules will be implemented to ensure that:
        *   Authenticated users can only access their own interaction history.
        *   Authorized healthcare professionals (e.g., nurses) can only access interaction history relevant to patients under their care, based on robust authorization logic within the application.
        *   Unauthorized access is strictly prevented.
*   **Data Minimization:** While full conversation logging is necessary for STM and potential debugging, the system should avoid soliciting or encouraging users to share unnecessary PHI.
*   **`Logos_Accord` Alignment:** The handling of `InteractionHistory` adheres to the principles of "Sanctity of Information" and "Privacy of the Soul" by ensuring data is protected, access is controlled, and the data pertains directly to the user's interaction with the system.
*   **Auditability:** GCP Cloud Audit Logs, combined with application-level logging, will provide records of data access and system activity.

By implementing these STM mechanisms and adhering to these principles, Project Noah MVP will provide a contextually aware agent while maintaining necessary security and privacy standards for user interactions.
