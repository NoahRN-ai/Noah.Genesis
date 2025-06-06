# Project Noah - Optimization and Enhancement Tasks

This document outlines identified areas for optimization, enhancement, and refactoring within the Project Noah codebase. It is intended to be a living document, updated as new tasks are identified or existing ones are addressed.

## Task Prioritization Legend (Optional)

*   **[P1] High:** Urgent or high-impact tasks.
*   **[P2] Medium:** Important tasks that should be addressed in the near term.
*   **[P3] Low:** Tasks that are beneficial but can be addressed when time permits.

## Task Format

Each task should ideally follow this format:

**ID:** `TASK-XXX` (A unique identifier, e.g., `BE-001`, `FE-001`)
**Title:** A concise summary of the task.
**Description:** Detailed explanation of the task, why it's needed, and potential approaches.
**Category:** (e.g., Backend API, Backend Services, Frontend, Database, DevOps, Testing, Documentation, Code Quality)
**Type:** (e.g., Optimization, Enhancement, Refactoring, New Feature, Bug Fix)
**Affected Files/Modules:** List of key files or modules related to the task.
**Priority:** (Optional, using the legend above)
**Status:** (e.g., Open, In Progress, Done, On Hold)

---

## I. Backend Enhancements & Optimizations

### A. API and Core Logic
    *   Tasks related to FastAPI, general API design, request/response handling.

**ID:** `BE-API-001`
**Title:** Standardize API Error Response Structure
**Description:** Currently, error handling in services (e.g., `llm_service.py`, `firestore_service.py`) returns strings or `None`. API routes building on these services might return inconsistent error structures. Define a standard Pydantic model for error responses (e.g., `{"detail": "error message", "code": "ERROR_CODE"}`) and ensure all API endpoints use it for client-side predictability. This involves refactoring service layers to raise custom exceptions that can be caught by FastAPI exception handlers to generate these standard responses.
**Category:** Backend API
**Type:** Enhancement, Refactoring
**Affected Files/Modules:** All FastAPI route handlers, `backend/app/services/firestore_service.py`, `backend/app/services/llm_service.py`, potentially a new `backend/app/exceptions.py`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `BE-API-002`
**Title:** Implement Global FastAPI Exception Handlers
**Description:** To complement `BE-API-001`, create global exception handlers in FastAPI (using `@app.exception_handler`) for custom exceptions raised by service layers (e.g., `ItemNotFoundError`, `LLMError`, `DatabaseError`). This centralizes error response generation and cleans up API route logic.
**Category:** Backend API
**Type:** Refactoring, Enhancement
**Affected Files/Modules:** `backend/app/main.py` (or wherever FastAPI app is initialized), service files.
**Priority:** [P2] Medium
**Status:** Open

### B. Services
    *   Tasks related to specific services like LLM interaction, database interactions, agent memory, etc.

    #### LLM Service (`backend/app/services/llm_service.py`)

**ID:** `BE-LLM-001`
**Title:** Enhance LLM Service Response to Structured Object
**Description:** The `get_llm_response` function currently returns a string. To better support LangGraph and tool usage, modify it to return a structured Pydantic model (e.g., `LLMOutput(text: Optional[str], tool_calls: Optional[List[ToolCallOutput]])`). This allows the caller (LangGraph agent) to more easily parse and act on text responses versus tool invocation requests from the LLM.
**Category:** Backend Services
**Type:** Enhancement, Refactoring
**Affected Files/Modules:** `backend/app/services/llm_service.py`, any code calling `get_llm_response`.
**Priority:** [P1] High
**Status:** Open

**ID:** `BE-LLM-002`
**Title:** Implement LLM Token Usage Tracking
**Description:** The `llm_service.py` has a placeholder comment for token usage tracking. Implement this by extracting `prompt_token_count`, `candidates_token_count`, and `total_token_count` from `response.usage_metadata` (if available for the model) and log this information. Consider sending this data to a monitoring system or a dedicated Firestore collection for cost analysis and usage monitoring.
**Category:** Backend Services
**Type:** Enhancement
**Affected Files/Modules:** `backend/app/services/llm_service.py`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `BE-LLM-003`
**Title:** Externalize LLM Model Configuration
**Description:** The LLM model name (e.g., "gemini-1.0-pro-001") is hardcoded as a default parameter. Move this and other key generation parameters (e.g., temperature, top_p, max_output_tokens if not using `DEFAULT_GENERATION_CONFIG`) to environment variables or a configuration file to allow easier updates and environment-specific settings without code changes.
**Category:** Backend Services
**Type:** Enhancement, Refactoring
**Affected Files/Modules:** `backend/app/services/llm_service.py`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `BE-LLM-004`
**Title:** Refactor `_convert_lc_messages_to_vertex_content` for Clarity
**Description:** The function `_convert_lc_messages_to_vertex_content` in `llm_service.py` handles multiple LangChain message types. While functional, its complexity could be reduced for better maintainability. Consider breaking down parts of its logic into smaller helper functions, each responsible for converting a specific message type (e.g., `_human_message_to_vertex_content`, `_ai_message_to_vertex_content`).
**Category:** Backend Services
**Type:** Refactoring
**Affected Files/Modules:** `backend/app/services/llm_service.py`.
**Priority:** [P3] Low
**Status:** Open

    #### Firestore Service (`backend/app/services/firestore_service.py`)

**ID:** `BE-FS-001`
**Title:** Implement Custom Exceptions in Firestore Service
**Description:** The Firestore service functions (e.g., `get_user_profile`, `update_user_profile`) currently return `Optional[Model]` or `bool`. Refactor to raise custom exceptions (e.g., `DocumentNotFound`, `UpdateFailedError`) when operations don't yield expected results. This allows API route handlers to catch specific errors and return appropriate HTTP responses.
**Category:** Backend Services
**Type:** Refactoring, Enhancement
**Affected Files/Modules:** `backend/app/services/firestore_service.py`, API route handlers using this service.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `BE-FS-002`
**Title:** Centralize Firestore Client Initialization
**Description:** The `AsyncClient()` for Firestore is instantiated directly in `firestore_service.py`. For better resource management and testability within a FastAPI application, initialize and manage the Firestore client using FastAPI's lifespan events or a dependency injection system.
**Category:** Backend Services
**Type:** Refactoring
**Affected Files/Modules:** `backend/app/services/firestore_service.py`, `backend/app/main.py` (or app initialization module).
**Priority:** [P2] Medium
**Status:** Open

**ID:** `BE-FS-003`
**Title:** Evaluate and Implement Firestore Batch Operations
**Description:** Identify scenarios where multiple Firestore documents are created or updated as part of a single logical operation. For these cases (e.g., potentially complex agent interactions saving multiple history parts), implement `AsyncWriteBatch` to ensure atomicity and potentially improve performance.
**Category:** Backend Services, Database
**Type:** Optimization, Enhancement
**Affected Files/Modules:** `backend/app/services/firestore_service.py`, other services performing multiple writes.
**Priority:** [P3] Low
**Status:** Open

    #### Agent Memory (`backend/app/agent/memory.py`)

**ID:** `BE-MEM-001`
**Title:** Add Sophisticated Context Window Management to Agent Memory
**Description:** The `load_session_history` currently loads the N most recent interactions. For very long conversations, this might exceed token limits or include irrelevant context. Research and implement more sophisticated context window management techniques, such as:
    *   Summarizing older messages.
    *   Using token-based truncation.
    *   Employing knowledge distillation from older parts of the conversation.
**Category:** Backend Services
**Type:** Enhancement
**Affected Files/Modules:** `backend/app/agent/memory.py`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `BE-MEM-002`
**Title:** Optimize Session History Loading Order
**Description:** `load_session_history` loads N messages ordered by timestamp descending, then reverses the list in Python. Investigate if Firestore can directly return the last N items in ascending chronological order with equivalent performance using a single query, potentially simplifying the code by removing the `interaction_history_docs.reverse()` step. This is a minor optimization unless proven significant.
**Category:** Backend Services
**Type:** Optimization
**Affected Files/Modules:** `backend/app/agent/memory.py`.
**Priority:** [P3] Low
**Status:** Open

### C. Data Models (`backend/app/models/`)

**ID:** `BE-MOD-001`
**Title:** Implement Granular Pydantic Field Validators
**Description:** Review all Pydantic models in `firestore_models.py` (and any other API models). Add field-level validators (`@field_validator`) for specific constraints beyond basic types, such as string lengths (min/max), numerical ranges, regex patterns for specific IDs, or ensuring lists are not empty where applicable. This improves data integrity at the model level.
**Category:** Backend Data Models
**Type:** Enhancement
**Affected Files/Modules:** `backend/app/models/firestore_models.py`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `BE-MOD-002`
**Title:** Consistent Management of `updated_at` Timestamps
**Description:** While `created_at` and `updated_at` are generally server-set in `firestore_service.py`, conduct a thorough review to ensure that *all* document update operations correctly and consistently set the `updated_at` field to the current server time. This is crucial for data auditing and tracking.
**Category:** Backend Data Models, Backend Services
**Type:** Enhancement, Bug Fix (Potential)
**Affected Files/Modules:** `backend/app/services/firestore_service.py`.
**Priority:** [P2] Medium
**Status:** Open
---

## VIII. Mock Data and Placeholder Implementations Audit

This section lists identified mock data, placeholder functions, and in-memory data stores used across the Project Noah codebase. These are typically implemented for MVP development, testing, or when actual backend services/external APIs are not yet integrated. They should be progressively replaced with real implementations.

**ID:** `MOCK-AUDIT-001`
**Title:** Hippocrates Agent Mock Data & Placeholders
**Description:** The `hippocrates_agent.py` uses several placeholders for its research and response generation workflow.
**Category:** Backend Agents, Mock Data
**Type:** Refactoring, Enhancement
**Affected Files/Modules:** `backend/app/agents/hippocrates_agent.py`
**Priority:** [P2] Medium
**Status:** Open
**Details:**
    *   **`medical_literature_search_tool` function (lines 20-26):**
        *   **Mock:** Placeholder tool returning hardcoded mock search results (2 mock studies).
        *   **Represents:** Calls to actual medical literature databases.
        *   **Potential Real Data Source(s)/API(s):** Vertex AI Search (with medical datasets), PubMed API, Google Scholar API, Semantic Scholar API.
        *   **High-Level Integration Strategy:**
            *   Modify `medical_literature_search_tool` to use chosen service SDK (e.g., Vertex AI Search SDK) or HTTP client (`requests` for REST APIs).
            *   Implement authentication (Google Cloud ADC for Vertex AI, API keys for others).
            *   Transform API responses to `List[dict]` with `title`, `summary`, `url`.
            *   Add API/service configurations (endpoints, project/dataset IDs, keys) to `backend/app/core/config.py` or environment variables.
        *   **Conceptual Priority:** P0 - Critical (Core to Hippocrates agent's purpose of research).
        *   **Note:** Contains `TODO: Replace with actual medical literature search tool integration`.
    *   **`start_research_node` function (lines 30-35):**
        *   **Mock:** Simple pass-through for `research_question`.
        *   **Represents:** Potential LLM call to refine user query.
        *   **Potential Real Data Source(s)/API(s):** `llm_service.py` (Vertex AI Gemini).
        *   **High-Level Integration Strategy:** Call `llm_service.get_llm_response` with a prompt designed to refine `state['user_query']` into `state['research_question']`.
        *   **Conceptual Priority:** P1 - Important (Enhances quality of research by refining the question).
        *   **Note:** Contains `TODO: Add LLM call to refine user_query into a research_question`.
    *   **`analyze_search_results_node` function (lines 47-56):**
        *   **Mock:** Simple analysis by concatenating mock search result summaries.
        *   **Represents:** LLM call to analyze and summarize actual search results.
        *   **Potential Real Data Source(s)/API(s):** `llm_service.py` (Vertex AI Gemini).
        *   **High-Level Integration Strategy:** Call `llm_service.get_llm_response` with a prompt that takes `state['search_results']` and generates `state['analysis_summary']`.
        *   **Conceptual Priority:** P0 - Critical (Core to processing research results for Hippocrates agent).
        *   **Note:** Contains `TODO: Replace with LLM call to analyze/summarize search results`.
    *   **`synthesize_response_node` function (lines 58-70):**
        *   **Mock:** Uses an f-string template to generate the final response from mock analysis.
        *   **Represents:** LLM call to synthesize a response.
        *   **Potential Real Data Source(s)/API(s):** `llm_service.py` (Vertex AI Gemini).
        *   **High-Level Integration Strategy:** Call `llm_service.get_llm_response` using `state['user_query']` and `state['analysis_summary']` to generate `state['final_response']`.
        *   **Conceptual Priority:** P0 - Critical (Core to generating the final output for Hippocrates agent).
        *   **Note:** Contains `TODO: Replace with LLM call to synthesize response based on analysis and query`.

**ID:** `MOCK-AUDIT-002`
**Title:** Agent Interfaces Orchestration Fallbacks
**Description:** The `agent_interfaces.py` file in `noah_agent_orchestration_groundwork` provides facade functions that attempt to call actual agent MVP implementations. If these imports fail, it uses local fallback mock data.
**Category:** Backend Agents, Mock Data
**Type:** Refactoring, Enhancement
**Affected Files/Modules:** `noah_agent_orchestration_groundwork/agent_interfaces.py`
**Priority:** [P2] Medium
**Status:** Open
**Details:**
    *   **`PSA_PROFILES` (line 30, fallback line 33):**
        *   **Mock:** Dictionary of patient profiles (2 mock patients in fallback).
        *   **Represents:** Patient data from Firestore or similar.
        *   **Potential Real Data Source(s)/API(s):** Firestore (via `firestore_service.py` and `PatientProfile` model).
        *   **High-Level Integration Strategy:** Ensure `patient_summary_agent.py` (or equivalent) correctly imports and uses `firestore_service.py` for profile data. Fallbacks become obsolete if imports are reliable.
        *   **Conceptual Priority:** P3 - Testing/Demo/Internal (These fallbacks should ideally not be used if main agents are integrated).
    *   **`SECA_SHARED_EVENTS` (line 44, fallback line 47):**
        *   **Mock:** Dictionary to store event logs, keyed by patient ID. Fallback is an empty dict.
        *   **Represents:** Event data from AlloyDB or similar.
        *   **Potential Real Data Source(s)/API(s):** AlloyDB (schema defined in `noah_foundational_data_aggregation_mvp/alloydb_schemas.sql`), or Firestore for event logs.
        *   **High-Level Integration Strategy:** Ensure `shift_event_capture.py` (or equivalent) correctly writes to the chosen persistent event store. Fallbacks become obsolete.
        *   **Conceptual Priority:** P3 - Testing/Demo/Internal.
    *   **`TLM_TASKS_DB` (line 62, fallback line 65):**
        *   **Mock:** List to store To-Do task dictionaries. Fallback is an empty list.
        *   **Represents:** Task data from a database or task management system.
        *   **Potential Real Data Source(s)/API(s):** Firestore or AlloyDB.
        *   **High-Level Integration Strategy:** Ensure `todo_list_manager.py` (or equivalent) correctly uses a persistent store. Fallbacks become obsolete.
        *   **Conceptual Priority:** P3 - Testing/Demo/Internal.
    *   **Facade function fallbacks:** `call_data_aggregation_firestore`, `call_data_aggregation_alloydb_events`, `call_patient_summary_agent`, `call_shift_event_capture_agent`, `call_todo_list_manager` all have logic to use these mock stores if their primary imports fail. Their real sources are the same as the primary agents they try to call.
        *   **High-Level Integration Strategy:** Focus on making primary agent integrations robust. Log warnings if fallbacks are ever used in production.
        *   **Conceptual Priority:** P3 - Testing/Demo/Internal.

**ID:** `MOCK-AUDIT-003`
**Title:** Patient Summary Agent Mock Data & Placeholders
**Description:** The `patient_summary_agent.py` in `noah_patient_summary_agent_mvp` heavily relies on mock data and simulated functionalities.
**Category:** Backend Agents, Mock Data
**Type:** Refactoring, Enhancement
**Affected Files/Modules:** `noah_patient_summary_agent_mvp/patient_summary_agent.py`, `noah_patient_summary_agent_mvp/mock_clinical_kb.json`
**Priority:** [P1] High (as this is a core agent MVP)
**Status:** Open
**Details:**
    *   **`MOCK_PATIENT_PROFILES` dictionary (lines 6-25):**
        *   **Mock:** Hardcoded profiles for "patient123" and "patient456".
        *   **Represents:** Patient master data.
        *   **Potential Real Data Source(s)/API(s):** Firestore (via `firestore_service.py` and `PatientProfile` model), FHIR server API, EHR system API, or a clinical data warehouse (e.g., BigQuery with healthcare data).
        *   **High-Level Integration Strategy:** Create a data service module (e.g., `fhir_service.py`, `ehr_service.py`, or extend `firestore_service.py`). This service handles API/DB calls, auth, and data mapping to Python dicts/Pydantic models. Update agent to use this service. Configure connection details and auth.
        *   **Conceptual Priority:** P0 - Critical (Core to patient summary generation).
    *   **`MOCK_EVENT_LOGS` dictionary (lines 27-46):**
        *   **Mock:** Hardcoded event logs for "patient123" and "patient456".
        *   **Represents:** Patient event data.
        *   **Potential Real Data Source(s)/API(s):** AlloyDB (schema in `noah_foundational_data_aggregation_mvp/alloydb_schemas.sql`), FHIR server API (e.g., Observation resources), or other event logging systems.
        *   **High-Level Integration Strategy:** Similar to profiles, create/use a service for event data. This service would connect to AlloyDB (using SQLAlchemy or Google Cloud SDKs) or a FHIR server. Agent calls this service. Map raw data to Python dicts. Configure connections.
        *   **Conceptual Priority:** P0 - Critical (Core to patient summary context).
    *   **`MOCK_CLINICAL_KB` (loaded from `mock_clinical_kb.json`, lines 49-54):**
        *   **Mock:** 5 mock clinical articles loaded from `mock_clinical_kb.json`.
        *   **Represents:** Real clinical knowledge base / RAG vector store.
        *   **Potential Real Data Source(s)/API(s):** Vertex AI Search (with uploaded clinical documents/textbooks), a dedicated graph database, or an external clinical knowledge base API.
        *   **High-Level Integration Strategy:** If using Vertex AI Search, ingest actual KB content into a datastore. Update `query_vertex_ai_search` to use Vertex AI Search SDK. If using external API, implement an API client. Configure datastore ID/API details.
        *   **Conceptual Priority:** P1 - Important (If RAG via Vertex AI Search is the primary, this direct file use is secondary. If this IS the RAG source, then P0).
    *   **`query_vertex_ai_search` function (lines 65-86):**
        *   **Mock:** Placeholder simulating RAG queries against `MOCK_CLINICAL_KB` using simple keyword matching.
        *   **Represents:** Calls to Vertex AI Search or similar RAG system.
        *   **Potential Real Data Source(s)/API(s):** Vertex AI Search API.
        *   **High-Level Integration Strategy:** Ensure this function uses the Vertex AI Search SDK, authenticates via ADC, and queries the correct datastore. Configure project and datastore IDs.
        *   **Conceptual Priority:** P0 - Critical (Core to providing accurate, evidence-based summaries).
    *   **`generate_summary_with_llm` function (lines 88-130):**
        *   **Mock:** Placeholder simulating LLM calls using f-strings to construct summaries.
        *   **Represents:** Calls to MedGemma/Gemini or other LLMs.
        *   **Potential Real Data Source(s)/API(s):** `llm_service.py` (Vertex AI Gemini).
        *   **High-Level Integration Strategy:** Replace f-string logic with calls to `backend.app.services.llm_service.get_llm_response`, passing appropriately constructed prompts and context.
        *   **Conceptual Priority:** P0 - Critical (Core to summary generation; assumes `llm_service.py` is the actual LLM interface).

**ID:** `MOCK-AUDIT-004`
**Title:** Shift Event Capture Agent Mock Data & Placeholders
**Description:** The `shift_event_capture.py` in `noah_shift_event_capture_agent_mvp` uses an in-memory store and placeholder functions.
**Category:** Backend Agents, Mock Data
**Type:** Refactoring, Enhancement
**Affected Files/Modules:** `noah_shift_event_capture_agent_mvp/shift_event_capture.py`
**Priority:** [P1] High (as this is a core agent MVP)
**Status:** Open
**Details:**
    *   **`SHARED_MOCK_EVENTS_DB` dictionary (line 8):**
        *   **Mock:** In-memory dictionary for storing event data.
        *   **Represents:** Event database like AlloyDB.
        *   **Potential Real Data Source(s)/API(s):** AlloyDB (schema in `noah_foundational_data_aggregation_mvp/alloydb_schemas.sql`), Firestore, or another persistent database.
        *   **High-Level Integration Strategy:** Modify `log_event` (and its caller `store_event_in_alloydb`) to use chosen database SDK (e.g., `google-cloud-firestore`, `sqlalchemy` with AlloyDB connector). Define data models/schemas for the chosen DB. Configure connection details and auth (IAM for GCP DBs).
        *   **Conceptual Priority:** P0 - Critical (Core to logging and persisting shift events).
    *   **`store_event_in_alloydb` function (lines 56-88):**
        *   **Mock:** Placeholder that writes to `SHARED_MOCK_EVENTS_DB`.
        *   **Represents:** Database write operations to AlloyDB.
        *   **Potential Real Data Source(s)/API(s):** AlloyDB client library, Firestore client library.
        *   **High-Level Integration Strategy:** This function should be refactored to become the actual DB interaction logic using the chosen DB SDK, as part of the `SHARED_MOCK_EVENTS_DB` replacement.
        *   **Conceptual Priority:** P0 - Critical (Part of the `SHARED_MOCK_EVENTS_DB` integration).
    *   **`transcribe_voice_input` function (lines 90-100):**
        *   **Mock:** Placeholder simulating Speech-to-Text; returns hardcoded transcriptions.
        *   **Represents:** Calls to a Speech-to-Text service.
        *   **Potential Real Data Source(s)/API(s):** Google Cloud Speech-to-Text API.
        *   **High-Level Integration Strategy:** Replace mock logic with calls to Google Cloud Speech-to-Text SDK. Handle API authentication (ADC). The calling function (e.g., `log_general_note_from_voice`) would manage audio input (e.g., from frontend) and pass to this service. Configure API details if needed.
        *   **Conceptual Priority:** P1 - Important (If voice input is a key feature).

**ID:** `MOCK-AUDIT-005`
**Title:** Plan of Care To-Do List Manager Mock Data
**Description:** The `todo_list_manager.py` in `noah_plan_of_care_todo_mvp` uses an in-memory list as a database.
**Category:** Backend Agents, Mock Data
**Type:** Refactoring, Enhancement
**Affected Files/Modules:** `noah_plan_of_care_todo_mvp/todo_list_manager.py`
**Priority:** [P1] High (as this is a core agent MVP)
**Status:** Open
**Details:**
    *   **`MOCK_TASKS_DB` list (line 5):**
        *   **Mock:** In-memory list for storing To-Do task dictionaries.
        *   **Represents:** Task database or an interface to a task management system.
        *   **Potential Real Data Source(s)/API(s):** Firestore or AlloyDB.
        *   **High-Level Integration Strategy:** Modify `add_task`, `get_all_tasks`, `update_task_status` to interact with the chosen database (Firestore or AlloyDB) using appropriate SDKs. Define data models/schemas. Configure DB connection and authentication.
        *   **Conceptual Priority:** P0 - Critical (Core to plan of care / ToDo functionality).
    *   All functions in this module operate on the `MOCK_TASKS_DB`.
---

## II. Frontend Enhancements & Optimizations

### A. Services & State Management
    *   Tasks related to API client, chat service, authentication context, etc.

    #### API Client (`frontend/src/services/apiClient.ts`)

**ID:** `FE-API-001`
**Title:** Enhance 401 Error Handling in API Client
**Description:** The `apiClient.ts` response interceptor has basic 401 handling. Enhance this to:
    1. Attempt an ID token refresh (using `AuthContext`'s `refreshIdToken` method, possibly via an event bus or a shared service) if the error indicates an expired token.
    2. If refresh is successful, retry the original request.
    3. If refresh fails or the 401 is not due to token expiration, then proceed with global sign-out or dispatching an 'auth-error-401' event.
This can provide a smoother user experience by avoiding unnecessary sign-outs.
**Category:** Frontend Services
**Type:** Enhancement, Refactoring
**Affected Files/Modules:** `frontend/src/services/apiClient.ts`, `frontend/src/contexts/AuthContext.tsx`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `FE-API-002`
**Title:** Make API Client Timeout Configurable
**Description:** The `apiClient.ts` has a hardcoded timeout of 15 seconds. While reasonable for many requests, some specific API calls (e.g., complex LLM interactions or data processing) might require longer. Make this timeout configurable, perhaps through an environment variable (`VITE_API_TIMEOUT`) or by allowing specific requests to override the default.
**Category:** Frontend Services
**Type:** Enhancement
**Affected Files/Modules:** `frontend/src/services/apiClient.ts`.
**Priority:** [P3] Low
**Status:** Open

    #### Chat Service (`frontend/src/services/chatApiService.ts`)

**ID:** `FE-CHAT-001`
**Title:** Expand Chat Service Capabilities
**Description:** The `chatApiService.ts` currently only supports sending messages. Plan and add functions for other anticipated chat functionalities, such as:
    *   Fetching chat message history for a session.
    *   Sending typing indicators.
    *   Handling message read receipts (if applicable).
    *   Support for message attachments (if planned).
Define the corresponding API endpoints and payload types (`frontend/src/types/api.ts`) as these are developed.
**Category:** Frontend Services
**Type:** Enhancement, New Feature
**Affected Files/Modules:** `frontend/src/services/chatApiService.ts`, `frontend/src/types/api.ts`, relevant backend API modules.
**Priority:** [P2] Medium
**Status:** Open

    #### Auth Context (`frontend/src/contexts/AuthContext.tsx`)

**ID:** `FE-AUTH-001`
**Title:** Review and Enhance AuthContext Error Propagation
**Description:** The `AuthContext.tsx` handles errors internally (e.g., during token refresh, sign-out). Review if these errors need to be more explicitly propagated or made available to consuming components for displaying user-facing messages (e.g., "Session expired, please sign in again," "Failed to refresh session"). Currently, errors are set to an `error` state, but UI components need to actively consume this.
**Category:** Frontend State Management
**Type:** Enhancement
**Affected Files/Modules:** `frontend/src/contexts/AuthContext.tsx`, UI components consuming `useAuth()`.
**Priority:** [P3] Low
**Status:** Open

### B. UI/UX
    *   (Placeholder for future UI/UX specific tasks - may not be heavily populated from this initial code review. Tasks here would typically come from design reviews or user feedback.)

**ID:** `FE-UI-001`
**Title:** Implement Global Notification System for API/Auth Errors
**Description:** To provide better user feedback, implement a global notification system (e.g., using toast messages) that can display errors originating from API calls (`apiClient.ts`) or authentication issues (`AuthContext.tsx`). This system should be easily invokable from services or contexts.
**Category:** Frontend UI/UX
**Type:** Enhancement
**Affected Files/Modules:** New notification component/context, `frontend/src/services/apiClient.ts`, `frontend/src/contexts/AuthContext.tsx`.
**Priority:** [P2] Medium
**Status:** Open
---

## III. Database (Firestore)

*   Tasks specifically targeting Firestore usage patterns, indexing strategies (if applicable from analysis), data migration plans (if any emerge). Many Firestore items might be linked to Backend Services.

**ID:** `DB-FS-001`
**Title:** Review Firestore Indexing Strategy
**Description:** As the application scales and query patterns become more diverse, review Firestore indexing. While Firestore auto-indexes many queries, complex queries or specific ordering/filtering might require composite indexes. Analyze common query patterns from `firestore_service.py` and `memory.py` and define necessary composite indexes in `firestore.indexes.json` (or via Terraform if preferred).
**Category:** Database
**Type:** Optimization, Enhancement
**Affected Files/Modules:** `backend/app/services/firestore_service.py`, `backend/app/agent/memory.py`, Firestore console/config.
**Priority:** [P3] Low
**Status:** Open
---

## IV. DevOps & Developer Experience

### A. Build System & Dependencies (`pyproject.toml`, `Makefile`)

**ID:** `DV-BUILD-001`
**Title:** Add Stricter Static Type Checking with MyPy
**Description:** `pyproject.toml` configures Ruff for linting and formatting. Enhance static analysis by integrating `mypy` for stricter type checking in the backend Python code. Add a `mypy` configuration to `pyproject.toml` or `mypy.ini` and include a `make lint-types` (or similar) command in the Makefile and pre-commit hooks.
**Category:** DevOps, Code Quality
**Type:** Enhancement
**Affected Files/Modules:** `pyproject.toml`, `Makefile`, `.pre-commit-config.yaml`, all backend Python files.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `DV-BUILD-002`
**Title:** Periodically Review and Update Dependencies
**Description:** Key dependencies like `langgraph`, `google-cloud-*` libraries, and `fastapi` are subject to updates. Schedule periodic reviews (e.g., quarterly) to check for new versions, assess changelogs for relevant features or breaking changes, and update dependencies in `pyproject.toml` accordingly. Ensure tests pass after updates.
**Category:** DevOps
**Type:** Maintenance, Enhancement
**Affected Files/Modules:** `pyproject.toml`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `DV-BUILD-003`
**Title:** Enhance Makefile for More Workflows
**Description:** The `Makefile` provides good basic commands. Consider enhancing it with:
    *   A target to run backend and frontend dev servers concurrently (e.g., using `concurrently` or simple backgrounding).
    *   Targets for common deployment tasks (if applicable, e.g., deploying to Cloud Run).
    *   Targets for cleaning frontend build artifacts.
**Category:** DevOps
**Type:** Enhancement
**Affected Files/Modules:** `Makefile`.
**Priority:** [P3] Low
**Status:** Open

### B. Infrastructure (`terraform/`)
    *   (Tasks in this section are based on file names and general best practices as content wasn't deeply analyzed)

**ID:** `DV-INFRA-001`
**Title:** Add Detailed READMEs for Terraform Modules
**Description:** For each Terraform directory/module (e.g., `networking`, `project_iam`, `secrets`, `monitoring_logging`), create a `README.md` file. This README should explain the purpose of the module, its inputs (variables), outputs, and any important considerations or dependencies.
**Category:** DevOps, Documentation
**Type:** Enhancement
**Affected Files/Modules:** All directories within `terraform/`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `DV-INFRA-002`
**Title:** Review Terraform Configuration Against GCP Best Practices
**Description:** Conduct a review of all Terraform configurations (`*.tf` files) against Google Cloud Platform best practices for security (e.g., least privilege IAM, secure network configurations), cost optimization (e.g., appropriate machine types, storage classes), and reliability. Document findings and create specific tasks for any identified gaps.
**Category:** DevOps
**Type:** Optimization, Enhancement
**Affected Files/Modules:** All `*.tf` files in `terraform/`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `DV-INFRA-003`
**Title:** Implement Terraform Linting and Formatting
**Description:** Integrate tools like `tflint` for linting Terraform code and `terraform fmt` for formatting. Add these checks to pre-commit hooks and potentially to a CI pipeline to ensure consistency and catch potential errors early.
**Category:** DevOps, Code Quality
**Type:** Enhancement
**Affected Files/Modules:** `terraform/`, `.pre-commit-config.yaml`.
**Priority:** [P2] Medium
**Status:** Open

### C. Scripts & Automation (`scripts/`)

**ID:** `DV-SCRIPT-001`
**Title:** Maintain and Enhance `setup_dev_env.sh`
**Description:** The `scripts/setup_dev_env.sh` script is crucial for developer onboarding. Regularly review and update it to reflect any changes in the development setup process, new dependencies, or improved automation steps. Ensure it's robust and provides clear guidance.
**Category:** DevOps
**Type:** Maintenance, Enhancement
**Affected Files/Modules:** `scripts/setup_dev_env.sh`.
**Priority:** [P2] Medium
**Status:** Open
---

## V. Testing

**ID:** `TEST-BE-001`
**Title:** Develop a Backend Test Plan and Improve Coverage
**Description:** While Pytest is set up, a formal test plan or coverage analysis might be missing. Analyze critical backend components (API endpoints, services, agent logic) and identify areas with low test coverage. Prioritize writing new unit and integration tests for these areas. Aim for a defined coverage target (e.g., 80%).
**Category:** Testing
**Type:** Enhancement
**Affected Files/Modules:** `backend/tests/`, all backend source files.
**Priority:** [P1] High
**Status:** Open

**ID:** `TEST-BE-002`
**Title:** Implement Mocking Strategy for External Services in Backend Tests
**Description:** For backend integration tests involving Firestore or Vertex AI, ensure a consistent and effective mocking strategy is in place (e.g., using `pytest-mock` for external API calls). This makes tests more reliable, faster, and avoids costs associated with real service usage during testing. Document this strategy.
**Category:** Testing
**Type:** Enhancement, Refactoring
**Affected Files/Modules:** `backend/tests/integration/`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `TEST-FE-001`
**Title:** Set Up Frontend Testing Framework
**Description:** No frontend tests were observed. Set up a testing framework for the React frontend (e.g., Jest with React Testing Library). Start by writing unit tests for critical components (e.g., `AuthContext`, UI components involved in core workflows) and services (`apiClient.ts`, `chatApiService.ts`).
**Category:** Testing
**Type:** Enhancement, New Feature
**Affected Files/Modules:** `frontend/src/`, new `frontend/src/tests/` directory.
**Priority:** [P1] High
**Status:** Open

**ID:** `TEST-FE-002`
**Title:** Develop Frontend Test Plan and Coverage Goals
**Description:** Similar to the backend, develop a test plan for the frontend. Identify key user flows and components that require testing. Define coverage goals and prioritize writing tests for critical functionalities.
**Category:** Testing
**Type:** Enhancement
**Affected Files/Modules:** `frontend/src/`.
**Priority:** [P2] Medium
**Status:** Open
---

## VI. Documentation

**ID:** `DOC-GEN-001`
**Title:** Enhance Root `README.md`
**Description:** Review and expand the root `README.md` to ensure it provides a comprehensive project overview, clear setup instructions (linking to `DEVELOPMENT.md`), a summary of the architecture, and contribution guidelines.
**Category:** Documentation
**Type:** Enhancement
**Affected Files/Modules:** `README.md`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `DOC-GEN-002`
**Title:** Maintain and Update `DEVELOPMENT.md`
**Description:** The `DEVELOPMENT.md` is a critical guide for developers. Ensure it's regularly updated to reflect any changes in the setup process, tooling, coding standards, or project structure.
**Category:** Documentation
**Type:** Maintenance
**Affected Files/Modules:** `DEVELOPMENT.md`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `DOC-BE-001`
**Title:** Enforce Comprehensive Backend Docstrings
**Description:** Mandate and progressively add comprehensive Google Style Python docstrings for all backend modules, classes, functions, and methods. This is crucial for maintainability and onboarding new developers. Consider a tool to measure docstring coverage.
**Category:** Documentation, Code Quality
**Type:** Enhancement
**Affected Files/Modules:** All Python files in `backend/app/`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `DOC-FE-001`
**Title:** Implement Frontend Code Documentation (JSDoc/TSDoc)
**Description:** Adopt and enforce JSDoc/TSDoc standards for documenting frontend TypeScript code, especially for components, services, contexts, and complex functions. This improves code clarity and maintainability.
**Category:** Documentation, Code Quality
**Type:** Enhancement
**Affected Files/Modules:** All `.ts` and `.tsx` files in `frontend/src/`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `DOC-GEN-003`
**Title:** Update `noah_workspace_rules.json`
**Description:** The `DEVELOPMENT.md` mentions that `noah_workspace_rules.json` should reflect current coding standards and project structure. Review and update this file to align with the actual state of the project and any newly established standards.
**Category:** Documentation, Code Quality
**Type:** Maintenance
**Affected Files/Modules:** `noah_workspace_rules.json`.
**Priority:** [P3] Low
**Status:** Open

**ID:** `DOC-API-001`
**Title:** Generate and Publish API Documentation
**Description:** Leverage FastAPI's OpenAPI schema generation capabilities to produce human-readable API documentation (e.g., using Swagger UI or ReDoc, which FastAPI can serve automatically). Ensure this documentation is accessible to frontend developers and other API consumers.
**Category:** Documentation
**Type:** Enhancement
**Affected Files/Modules:** `backend/app/main.py`, FastAPI configuration.
**Priority:** [P2] Medium
**Status:** Open
---

## VII. Code Quality & Standards

**ID:** `CQ-GEN-001`
**Title:** Review and Refine Ruff Linters and Formatters Configuration
**Description:** Periodically review the Ruff configuration in `pyproject.toml`. Explore new linting rules or adjust existing ones to further improve code quality and consistency. Ensure the configuration aligns with team preferences and project needs.
**Category:** Code Quality, DevOps
**Type:** Enhancement, Maintenance
**Affected Files/Modules:** `pyproject.toml`.
**Priority:** [P3] Low
**Status:** Open

**ID:** `CQ-GEN-002`
**Title:** Enhance Pre-Commit Hooks
**Description:** Review the `.pre-commit-config.yaml`. Consider adding more hooks for:
    *   Checking for large files.
    *   Validating JSON, YAML files.
    *   Detecting secrets or sensitive information (e.g., with `detect-secrets`).
    *   Ensuring consistent line endings.
**Category:** Code Quality, DevOps
**Type:** Enhancement
**Affected Files/Modules:** `.pre-commit-config.yaml`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `CQ-BE-001`
**Title:** Backend Security Best Practices Review
**Description:** Conduct a review of the backend code against common security best practices for web applications, including:
    *   Input validation (covered by Pydantic, but ensure thoroughness).
    *   Output encoding (FastAPI handles much of this).
    *   Authentication and authorization mechanisms.
    *   Protection against common vulnerabilities (OWASP Top 10 relevant points).
    *   Secure handling of secrets and configurations.
**Category:** Code Quality, Security
**Type:** Enhancement
**Affected Files/Modules:** All backend code, especially API handlers and service layers.
**Priority:** [P1] High
**Status:** Open

**ID:** `CQ-FE-001`
**Title:** Frontend Security Best Practices Review
**Description:** Conduct a review of the frontend code against common security best practices, including:
    *   Protection against XSS (React helps, but vigilance is needed with `dangerouslySetInnerHTML`, etc.).
    *   Secure handling of tokens and user data.
    *   CSP (Content Security Policy) considerations (may involve backend headers).
**Category:** Code Quality, Security
**Type:** Enhancement
**Affected Files/Modules:** All frontend code, especially auth handling and data display.
**Priority:** [P2] Medium
**Status:** Open
---
