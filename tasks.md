# Project Noah - Optimization and Enhancement Tasks

This document outlines identified areas for optimization, enhancement, and refactoring within the Project Noah codebase. It is intended to be a living document, updated as new tasks are identified or existing ones are addressed.

## Task Prioritization Legend (Optional)

*   **[C] Critical:** Must be addressed, major impact on security, functionality, or stability.
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

**ID:** `BE-API-003`
**Title:** Critical: Implement User ID Filtering for Session History API
**Description:** Modify `list_interaction_history_for_session` service function (in `backend/app/services/firestore_service.py`) and its caller in the API endpoint (`backend/app/api/v1/endpoints/history.py`) to include `user_id` filtering. This ensures users can only access their own session history, preventing a critical data exposure vulnerability.
**Category:** Backend API, Backend Services, Security
**Type:** Bug Fix, Security
**Affected Files/Modules:** `backend/app/api/v1/endpoints/history.py`, `backend/app/services/firestore_service.py`
**Priority:** [C] Critical
**Status:** Open

**ID:** `BE-API-004`
**Title:** Critical: Implement Basic Self-Logging Authorization for Patient Data
**Description:** In the `POST /patient-data-logs` endpoint (`backend/app/api/v1/endpoints/patient_data.py`), implement an authorization check to ensure that for MVP, a user can only submit data logs for themselves (i.e., `current_user.user_id == target_patient_user_id`). This addresses a potential security gap.
**Category:** Backend API, Security
**Type:** Bug Fix, Security
**Affected Files/Modules:** `backend/app/api/v1/endpoints/patient_data.py`
**Priority:** [C] Critical
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
**Title:** Externalize LLM Model Configuration from `llm_service.py`
**Description:** The LLM model name (e.g., "gemini-1.0-pro-001") is hardcoded as a default parameter in `get_llm_response`. This should be primarily sourced from `settings.DEFAULT_LLM_MODEL_NAME` (from `core/config.py`). Review `llm_service.py` to ensure it uses the centralized configuration for model name and other key generation parameters (e.g., temperature, top_p). Direct `os.getenv` calls in `llm_service.py` for `GCP_PROJECT_ID` and `VERTEX_AI_REGION` should be replaced by `settings` values.
**Category:** Backend Services, Configuration
**Type:** Enhancement, Refactoring
**Affected Files/Modules:** `backend/app/services/llm_service.py`, `backend/app/core/config.py`
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

**ID:** `BE-MEM-003`
**Title:** Critical Bug Fix: Remove Invalid `name` Parameter from `ToolMessage`
**Description:** The `ToolMessage` constructor in LangChain typically does not accept a `name` parameter. Remove this parameter from the `ToolMessage` instantiation in `backend/app/agent/memory.py` to prevent runtime errors.
**Category:** Backend Services, Bug Fix
**Type:** Bug Fix
**Affected Files/Modules:** `backend/app/agent/memory.py`
**Priority:** [C] Critical
**Status:** Open

**ID:** `BE-MEM-004`
**Title:** Refine `ToolCall` Instantiation in Agent Memory
**Description:** Consider using `langchain_core.messages.ToolCall` objects directly instead of dictionaries when constructing the `tool_calls` attribute for `AIMessage` in `backend/app/agent/memory.py`. This can improve type safety and explicitness, if compatible with the LangChain version being used.
**Category:** Backend Services
**Type:** Refactoring
**Affected Files/Modules:** `backend/app/agent/memory.py`
**Priority:** [P3] Low
**Status:** Open

**ID:** `BE-MEM-005`
**Title:** Add Error Handling for Non-Serializable `ToolMessage.content`
**Description:** Before saving to Firestore, ensure `ToolMessage.content` (which is stringified if originally a dict) is handled gracefully if it contains non-serializable data that might cause issues during JSON stringification or Firestore saving. Add specific error handling or data sanitization.
**Category:** Backend Services
**Type:** Enhancement
**Affected Files/Modules:** `backend/app/agent/memory.py`
**Priority:** [P2] Medium
**Status:** Open

    #### RAG Service (`backend/app/services/rag_service.py`)
**ID:** `BE-RAG-001`
**Title:** Standardize Configuration Sourcing in RAG Service
**Description:** Modify `rag_service.py` to source all its configurations (e.g., `GCP_PROJECT_ID`, region, RAG-specific GCS bucket/object names, Vertex AI Index/Endpoint IDs) from the central `settings` object (`backend.app.core.config.settings`) instead of `os.getenv` directly. This requires defining these RAG-specific settings in `core/config.py`.
**Category:** Backend Services, Configuration
**Type:** Refactoring, Enhancement
**Affected Files/Modules:** `backend/app/services/rag_service.py`, `backend/app/core/config.py`
**Priority:** [P2] Medium
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

### D. Core (`backend/app/core/`)

**ID:** `BE-CORE-001`
**Title:** Critical: Ensure Robust Firebase Admin SDK Initialization
**Description:** Verify that `initialize_firebase_admin()` (from `backend/app/core/security.py`) is reliably called once during application startup (e.g., within FastAPI's lifespan event in `backend/app/main.py`). Handle potential initialization failures robustly, possibly preventing app startup if Firebase is critical.
**Category:** Backend Core, Reliability
**Type:** Enhancement, Bug Fix (Potential)
**Affected Files/Modules:** `backend/app/core/security.py`, `backend/app/main.py`
**Priority:** [C] Critical
**Status:** Open

**ID:** `BE-CORE-002`
**Title:** Ensure `.env.example` Includes All Mandatory Backend Variables
**Description:** The `.env.example` file (to be created from `DEVELOPMENT.md` guidance) should list all environment variables required for the backend's local operation, especially those without defaults in `core/config.py`.
**Category:** Backend Core, Documentation
**Type:** Documentation
**Affected Files/Modules:** `.env.example` (project root), `backend/app/core/config.py`
**Priority:** [P1] High
**Status:** Open

**ID:** `BE-CORE-003`
**Title:** Promote ADC for Production Firebase/GCP Authentication
**Description:** In documentation and configuration (`core/config.py`), clearly recommend using Application Default Credentials (ADC) for Firebase Admin SDK and other GCP service authentication in deployed production environments, rather than relying on explicit service account key files (e.g., via `FIREBASE_ADMIN_SDK_CREDENTIALS_PATH` or `GOOGLE_APPLICATION_CREDENTIALS` pointing to a file).
**Category:** Backend Core, Security, Configuration
**Type:** Best Practice
**Affected Files/Modules:** `backend/app/core/config.py`, relevant documentation.
**Priority:** [P2] Medium
**Status:** Open

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

**ID:** `FE-API-003`
**Title:** Improve Error Typing in API Service Catch Blocks
**Description:** In all API service files (e.g., `chatApiService.ts`, `historyApiService.ts`, `patientDataApiService.ts`, `userProfileApiService.ts`), refine error handling in `catch` blocks to use `axios.isAxiosError` for more type-safe access to Axios-specific error properties like `error.response?.data`.
**Category:** Frontend Services, Code Quality
**Type:** Refactoring
**Affected Files/Modules:** `frontend/src/services/chatApiService.ts`, `frontend/src/services/historyApiService.ts`, `frontend/src/services/patientDataApiService.ts`, `frontend/src/services/userProfileApiService.ts`
**Priority:** [P2] Medium
**Status:** Open

    #### Chat Service (`frontend/src/services/chatApiService.ts`)
*(FE-CHAT-001 already exists and covers expanding capabilities including history)*

    #### Auth Context (`frontend/src/contexts/AuthContext.tsx`)

**ID:** `FE-AUTH-001`
**Title:** Review and Enhance AuthContext Error Propagation
**Description:** The `AuthContext.tsx` handles errors internally (e.g., during token refresh, sign-out). Review if these errors need to be more explicitly propagated or made available to consuming components for displaying user-facing messages (e.g., "Session expired, please sign in again," "Failed to refresh session"). Currently, errors are set to an `error` state, but UI components need to actively consume this.
**Category:** Frontend State Management
**Type:** Enhancement
**Affected Files/Modules:** `frontend/src/contexts/AuthContext.tsx`, UI components consuming `useAuth()`.
**Priority:** [P3] Low
**Status:** Open

**ID:** `FE-AUTH-002`
**Title:** Critical: Review and Correct `useEffect`/`useCallback` Dependency Arrays
**Description:** In `AuthContext.tsx`, thoroughly review and correct the dependency arrays for all `useEffect` and `useCallback` hooks (especially for `handleUserChange` and the `onFirebaseAuthStateChanged` effect). Incorrect dependencies can lead to stale closures, infinite loops, or missed updates.
**Category:** Frontend State Management, Bug Fix
**Type:** Bug Fix
**Affected Files/Modules:** `frontend/src/contexts/AuthContext.tsx`
**Priority:** [C] Critical
**Status:** Open

### B. UI/UX
    *   (Placeholder for future UI/UX specific tasks - may not be heavily populated from this initial code review. Tasks here would typically come from design reviews or user feedback.)

**ID:** `FE-UI-001`
**Title:** Implement Global Notification System for API/Auth Errors
**Description:** To provide better user feedback, implement a global notification system (e.g., using toast messages via Mantine `notifications`) that can display errors originating from API calls (`apiClient.ts`) or authentication issues (`AuthContext.tsx`). This system should be easily invokable from services or contexts.
**Category:** Frontend UI/UX
**Type:** Enhancement
**Affected Files/Modules:** New notification component/context, `frontend/src/services/apiClient.ts`, `frontend/src/contexts/AuthContext.tsx`.
**Priority:** [P2] Medium
**Status:** Open

### C. Components & Pages

**ID:** `FE-COMP-001`
**Title:** Robust Loading Fallback Height in `App.tsx`
**Description:** Ensure the `LoadingFallback` component used for lazy-loaded pages in `App.tsx` (and also the loader in `ProtectedRoute.tsx`) correctly fills the available height within the main content area of `AppLayout`, rather than relying on fixed `100vh` calculations that might ignore layout elements like headers.
**Category:** Frontend Components
**Type:** Enhancement, Bug Fix (Layout)
**Affected Files/Modules:** `frontend/src/App.tsx`, `frontend/src/components/common/ProtectedRoute.tsx`, `frontend/src/components/common/Layout.tsx`
**Priority:** [P2] Medium
**Status:** Open

**ID:** `FE-COMP-002`
**Title:** Ensure `AppShell.Main` Fills Vertical Space
**Description:** Configure `AppShell` in `Layout.tsx` and its parent elements such_that `AppShell.Main` correctly occupies the full available vertical space. This is crucial for components like `ChatPage` and loading fallbacks to render correctly without incorrect height calculations. This may involve flexbox styling on parent containers.
**Category:** Frontend Components, Layout
**Type:** Enhancement, Bug Fix (Layout)
**Affected Files/Modules:** `frontend/src/components/common/Layout.tsx`, `frontend/src/styles/theme.ts`
**Priority:** [P2] Medium
**Status:** Open

**ID:** `FE-COMP-003`
**Title:** Optimize `useStyles` in `ChatInterface.tsx`
**Description:** Review and optimize the `useStyles` style definition and usage within `ChatInterface.tsx`. Ensure styles are memoized or defined outside the component if static to prevent re-creation on every render, potentially improving performance.
**Category:** Frontend Components, Optimization
**Type:** Optimization
**Affected Files/Modules:** `frontend/src/components/ChatInterface.tsx`
**Priority:** [P3] Low
**Status:** Open

**ID:** `FE-PAGE-001`
**Title:** Ensure Reliable CSS Variable for Header Height
**Description:** The `ChatPage.tsx` and other layout calculations rely on `--app-shell-header-height`. Ensure this CSS variable is reliably defined (e.g., in global styles or via `AppLayout`) and consistently used, or replace its usage with a value from the Mantine theme.
**Category:** Frontend Pages, Layout
**Type:** Enhancement
**Affected Files/Modules:** `frontend/src/pages/ChatPage.tsx`, `frontend/src/components/common/Layout.tsx`, `frontend/src/styles/theme.ts`
**Priority:** [P2] Medium
**Status:** Open

**ID:** `FE-PAGE-002`
**Title:** Improve Post-Registration UX on `LoginPage.tsx`
**Description:** After successful user registration on `LoginPage.tsx`, automatically navigate the user to the main application (e.g., `/chat`). Firebase `createUserWithEmailAndPassword` signs the user in, so `AuthContext` should handle the new user state and trigger the redirect. Remove the step that switches back to login mode post-registration.
**Category:** Frontend Pages, UX
**Type:** Enhancement
**Affected Files/Modules:** `frontend/src/pages/LoginPage.tsx`
**Priority:** [P2] Medium
**Status:** Open

**ID:** `FE-PAGE-003`
**Title:** Refine Firebase Error Message Parsing on `LoginPage.tsx`
**Description:** Improve the parsing of Firebase error codes in `handleSubmit` and `handleGoogleSignIn` on `LoginPage.tsx` to provide more user-friendly and specific messages. Consider a helper function for mapping common error codes.
**Category:** Frontend Pages, UX
**Type:** Enhancement
**Affected Files/Modules:** `frontend/src/pages/LoginPage.tsx`
**Priority:** [P2] Medium
**Status:** Open

**ID:** `FE-PAGE-004`
**Title:** Correct Error Variable Usage in Notifications on `LoginPage.tsx`
**Description:** In the `catch` blocks of `handleSubmit` and `handleGoogleSignIn` on `LoginPage.tsx`, ensure the `message` in `notifications.show` uses the error object from the current `catch` block (e.g., `parsedFirebaseError`) rather than the component's `error` state, which might be stale.
**Category:** Frontend Pages, Bug Fix
**Type:** Bug Fix
**Affected Files/Modules:** `frontend/src/pages/LoginPage.tsx`
**Priority:** [P2] Medium
**Status:** Open

---

## III. Database (Firestore & RAG Storage)

*   Tasks specifically targeting Firestore usage patterns, indexing strategies, RAG storage, data migration plans (if any emerge).

**ID:** `DB-FS-001`
**Title:** Review Firestore Indexing Strategy
**Description:** As the application scales and query patterns become more diverse, review Firestore indexing. While Firestore auto-indexes many queries, complex queries or specific ordering/filtering might require composite indexes. Analyze common query patterns from `firestore_service.py` and `memory.py` and define necessary composite indexes in `firestore.indexes.json` (or via Terraform if preferred). *Update: This task should also include documenting these indexes and ensuring a process for their creation, possibly via Terraform or clear manual steps in `services/README.md`.*
**Category:** Database
**Type:** Optimization, Enhancement, Documentation
**Affected Files/Modules:** `backend/app/services/firestore_service.py`, `backend/app/agent/memory.py`, Firestore console/config, `backend/app/services/README.md`
**Priority:** [P2] Medium *(was P3, increased due to documentation need)*
**Status:** Open

**ID:** `DB-RAG-001`
**Title:** Critical Infrastructure: Ensure Firestore Composite Indexes for RAG
**Description:** Based on queries in `firestore_service.py` (especially those that might be used by RAG for metadata or history), ensure all necessary Firestore composite indexes are documented in `backend/app/services/README.md` and a process exists for their creation (manual or Terraform). This is critical for performance.
**Category:** Database, DevOps
**Type:** Performance, Documentation
**Affected Files/Modules:** `backend/app/services/README.md`, `backend/app/services/firestore_service.py`, Terraform files if used for index management.
**Priority:** [C] Critical
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
**Description:** The `Makefile` provides good basic commands. Enhance it with:
    *   A target to run backend and frontend dev servers concurrently.
    *   Targets for common deployment tasks (if applicable).
    *   Targets for cleaning frontend build artifacts.
    *   Targets for common Terraform commands (init, plan, apply, destroy).
    *   Target to run the RAG pipeline script.
    *   Update `make help` with new commands.
    *   Consider a less aggressive default `clean` target (not removing `.venv`).
**Category:** DevOps
**Type:** Enhancement
**Affected Files/Modules:** `Makefile`.
**Priority:** [P2] Medium *(was P3, increased with more items)*
**Status:** Open

**ID:** `DV-BUILD-004`
**Title:** Investigate/Update Backend `POETRY_VERSION` in Dockerfile
**Description:** The `backend/Dockerfile` specifies `POETRY_VERSION=1.7.1`. Investigate if a newer stable version is available and update if beneficial.
**Category:** DevOps, Dependencies
**Type:** Maintenance
**Affected Files/Modules:** `backend/Dockerfile`
**Priority:** [P3] Low
**Status:** Open

**ID:** `DV-BUILD-005`
**Title:** Schedule Regular Checks for Backend Base Image Vulnerabilities
**Description:** The `backend/Dockerfile` uses `python:3.11-slim`. Schedule regular (e.g., monthly or on new base image releases) checks for known vulnerabilities in this base image and update as necessary.
**Category:** DevOps, Security
**Type:** Maintenance
**Affected Files/Modules:** `backend/Dockerfile`
**Priority:** [P2] Medium
**Status:** Open

### B. Infrastructure (`terraform/`)

**ID:** `DV-INFRA-001`
**Title:** Add Detailed READMEs for All Terraform Files
**Description:** Create/update detailed `README.md` files for each main Terraform functional area (e.g., `networking.md`, `project_iam.md`, `secrets.md`, `monitoring_logging.md`, `vector_search.md`). Ensure they explain the purpose, resources created, inputs, outputs, and any important operational considerations. *(Partially covered by existing .md files, ensure all .tf files have corresponding detailed .md)*
**Category:** DevOps, Documentation
**Type:** Enhancement
**Affected Files/Modules:** All files in `terraform/`.
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

**ID:** `DV-INFRA-004`
**Title:** Critical: Update/Parameterize Terraform Dashboard & Alert Placeholders
**Description:** The `google_monitoring_dashboard` in `terraform/monitoring_logging.tf` and the example alert policy use placeholder service names. These must be updated with actual deployed resource names or parameterized using Terraform variables/outputs to be effective.
**Category:** DevOps, Infrastructure
**Type:** Bug Fix, Configuration
**Affected Files/Modules:** `terraform/monitoring_logging.tf`
**Priority:** [C] Critical
**Status:** Open

**ID:** `DV-INFRA-005`
**Title:** Configure Notification Channels for Terraform Alerts
**Description:** Create `google_monitoring_notification_channel` resources and link them to alert policies in `terraform/monitoring_logging.tf` to ensure alerts are actionable.
**Category:** DevOps, Infrastructure
**Type:** Configuration
**Affected Files/Modules:** `terraform/monitoring_logging.tf`
**Priority:** [P1] High
**Status:** Open

**ID:** `DV-INFRA-006`
**Title:** Critical: Parameterize Subnet IP CIDR Range in Terraform
**Description:** The `ip_cidr_range` in `terraform/networking.tf` is hardcoded. Change this to use a variable defined in `terraform/variables.tf` to avoid conflicts and improve reusability.
**Category:** DevOps, Infrastructure
**Type:** Configuration, Best Practice
**Affected Files/Modules:** `terraform/networking.tf`, `terraform/variables.tf`
**Priority:** [C] Critical
**Status:** Open

**ID:** `DV-INFRA-007`
**Title:** Add Serverless VPC Access Connector in Terraform
**Description:** Provision a `google_vpc_access_connector` in `terraform/networking.tf` if Cloud Run services require NAT for non-Google APIs or access to VPC-internal resources.
**Category:** DevOps, Infrastructure
**Type:** Enhancement
**Affected Files/Modules:** `terraform/networking.tf`, `terraform/variables.tf`
**Priority:** [P2] Medium
**Status:** Open

**ID:** `DV-INFRA-008`
**Title:** Expand Terraform Outputs Significantly
**Description:** Add more outputs to `terraform/outputs.tf` for key resource identifiers like VPC name, subnet name, NAT IP, logging bucket URL, BigQuery dataset ID, RAG GCS bucket name, Vertex AI Index/Endpoint IDs.
**Category:** DevOps, Infrastructure
**Type:** Enhancement
**Affected Files/Modules:** `terraform/outputs.tf`, all other `*.tf` files.
**Priority:** [P1] High
**Status:** Open

**ID:** `DV-INFRA-009`
**Title:** Critical: Grant `sa-rag-pipeline` GCS Write Permission in Terraform
**Description:** The `sa-rag-pipeline` service account needs permission to write to the RAG GCS bucket. Add the appropriate IAM binding (e.g., `roles/storage.objectAdmin` or `objectCreator` on the specific bucket) in `terraform/project_iam.tf` or `terraform/vector_search.tf`.
**Category:** DevOps, Infrastructure, Security
**Type:** Bug Fix, Configuration
**Affected Files/Modules:** `terraform/project_iam.tf` (or `terraform/vector_search.tf`)
**Priority:** [C] Critical
**Status:** Open

**ID:** `DV-INFRA-010`
**Title:** Critical: Clarify RAG Index Population Workflow & Permissions
**Description:** Clarify in `terraform/vector_search.tf` and `scripts/rag_pipeline/README.md` the timing of the RAG pipeline script execution relative to `terraform apply` for initial index population via `contents_delta_uri`. Ensure `sa-rag-pipeline` has permissions to update the Vertex AI Index if it manages content post-creation.
**Category:** DevOps, Infrastructure, RAG
**Type:** Process, Documentation, Configuration
**Affected Files/Modules:** `terraform/vector_search.tf`, `scripts/rag_pipeline/README.md`, `terraform/project_iam.tf`
**Priority:** [C] Critical
**Status:** Open

**ID:** `DV-INFRA-011`
**Title:** Recommend Terraform Remote State Backend
**Description:** Add a section to `terraform/README.md` recommending and guiding the setup of a remote backend (e.g., GCS bucket) for Terraform state management.
**Category:** DevOps, Infrastructure, Best Practice
**Type:** Documentation
**Affected Files/Modules:** `terraform/README.md`
**Priority:** [P1] High
**Status:** Open

### C. Scripts & Automation (`scripts/`)

**ID:** `DV-SCRIPT-001`
**Title:** Maintain and Enhance `setup_dev_env.sh`
**Description:** The `scripts/setup_dev_env.sh` script is crucial for developer onboarding. Regularly review and update it to reflect any changes in the development setup process, new dependencies, or improved automation steps. *Enhancements: Make GCP Project ID setup more interactive, add Docker installation check, offer to copy `.env.example`.*
**Category:** DevOps
**Type:** Maintenance, Enhancement
**Affected Files/Modules:** `scripts/setup_dev_env.sh`.
**Priority:** [P2] Medium
**Status:** Open

**ID:** `DV-SCRIPT-002`
**Title:** Enhance RAG Pipeline Script (`01_process_and_embed_docs.py`)
**Description:** Improve the RAG pipeline script by:
    *   Making embedding model name, chunking parameters, and batch size configurable (env vars/CLI).
    *   Standardizing GCP config sourcing.
    *   Adding progress indicators (e.g., `tqdm`).
    *   Validating all necessary GCS env vars.
**Category:** DevOps, Scripts, RAG
**Type:** Enhancement
**Affected Files/Modules:** `scripts/rag_pipeline/01_process_and_embed_docs.py`
**Priority:** [P1] High
**Status:** Open

---

## V. Testing

**ID:** `TEST-BE-001`
**Title:** Develop a Backend Test Plan and Improve Coverage
**Description:** While Pytest is set up, a formal test plan or coverage analysis might be missing. Analyze critical backend components (API endpoints, services, agent logic) and identify areas with low test coverage. Prioritize writing new unit and integration tests for these areas. Aim for a defined coverage target (e.g., 80%). *Update: `backend/README.md` should also document this need.*
**Category:** Testing
**Type:** Enhancement
**Affected Files/Modules:** `backend/tests/`, all backend source files, `backend/README.md`.
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
**Title:** Set Up Frontend Testing Framework and Strategy
**Description:** No frontend tests were observed. Set up a testing framework for the React frontend (e.g., Vitest or Jest with React Testing Library). Start by writing unit tests for critical components (e.g., `AuthContext`, UI components involved in core workflows) and services (`apiClient.ts`, `chatApiService.ts`). *Update: `frontend/README.md` should document this strategy.*
**Category:** Testing
**Type:** Enhancement, New Feature
**Affected Files/Modules:** `frontend/src/`, new `frontend/src/tests/` directory, `frontend/README.md`.
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
**Description:** Review and expand the root `README.md` to ensure it provides a comprehensive project overview, clear setup instructions (linking to `DEVELOPMENT.md`), a summary of the architecture (tech stack, project structure), testing overview, contribution guidelines, and license information.
**Category:** Documentation
**Type:** Enhancement
**Affected Files/Modules:** `README.md`.
**Priority:** [P1] High *(was P2)*
**Status:** Open

**ID:** `DOC-GEN-002`
**Title:** Maintain and Update `DEVELOPMENT.md`
**Description:** The `DEVELOPMENT.md` is a critical guide for developers. Ensure it's regularly updated to reflect any changes in the setup process, tooling, coding standards, or project structure. *Enhancements: Create `.env.example`, add frontend & Terraform setup sections, update frontend status description.*
**Category:** Documentation
**Type:** Maintenance, Enhancement
**Affected Files/Modules:** `DEVELOPMENT.md`, `.env.example` (project root).
**Priority:** [P1] High *(was P2)*
**Status:** Open

**ID:** `DOC-BE-001`
**Title:** Enforce Comprehensive Backend Docstrings
**Description:** Mandate and progressively add comprehensive Google Style Python docstrings for all backend modules, classes, functions, and methods. This is crucial for maintainability and onboarding new developers. Consider a tool to measure docstring coverage. *Update: `backend/Dockerfile` comment for `--no-root` can be added here.*
**Category:** Documentation, Code Quality
**Type:** Enhancement
**Affected Files/Modules:** All Python files in `backend/app/`, `backend/Dockerfile`.
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
**Description:** The `DEVELOPMENT.md` mentions that `noah_workspace_rules.json` should reflect current coding standards and project structure. Review and update this file to align with the actual state of the project and any newly established standards. *Also, clarify/provide the referenced `coding-standards.md_vCurrent` and `project-structure.md_vCurrent` or update the reference.*
**Category:** Documentation, Code Quality
**Type:** Maintenance
**Affected Files/Modules:** `noah_workspace_rules.json`, `DEVELOPMENT.md`.
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

**ID:** `DOC-BE-002`
**Title:** Update Backend Models README for Tool Definitions
**Description:** The `backend/app/models/README.md` needs its descriptions of `ToolCall` and `ToolResponse` updated to match the correct Pydantic model definitions found in `firestore_models.py` (which are LangChain compatible).
**Category:** Documentation
**Type:** Correction
**Affected Files/Modules:** `backend/app/models/README.md`
**Priority:** [P1] High
**Status:** Open

**ID:** `DOC-BE-003`
**Title:** Document Backend Plans and Verify Document Versions
**Description:** In `backend/README.md`:
    *   Document plans for LangGraph and agent tools integration (Phase 3).
    *   Document plans for robust authorization logic (beyond MVP).
    *   Document plans for further Cloud Monitoring/Logging integration.
    *   Verify that `TA_Noah_MVP_v1.1` referenced is the latest version.
    *   Check/confirm `textembedding-gecko@003` recommendation against latest GCP offerings.
**Category:** Documentation
**Type:** Enhancement, Maintenance
**Affected Files/Modules:** `backend/README.md`
**Priority:** [P2] Medium
**Status:** Open

**ID:** `DOC-FE-002`
**Title:** Enhance Frontend README
**Description:** In `frontend/README.md`:
    *   Add a section on Testing Strategy (tools, types of tests).
    *   Add a section explaining environment variable management for local development.
    *   Clarify Vite path alias setup (e.g., `vite-tsconfig-paths`).
**Category:** Documentation
**Type:** Enhancement
**Affected Files/Modules:** `frontend/README.md`
**Priority:** [P1] High
**Status:** Open

**ID:** `DOC-SCRIPT-001`
**Title:** Enhance RAG Pipeline README
**Description:** In `scripts/rag_pipeline/README.md`:
    *   Clarify dependency scope for `langchain-text-splitters`, `pypdf`.
    *   Add an example/reference for `index_metadata_update_config.yaml`.
    *   Add a note about the script's idempotency.
**Category:** Documentation
**Type:** Enhancement
**Affected Files/Modules:** `scripts/rag_pipeline/README.md`
**Priority:** [P2] Medium
**Status:** Open

**ID:** `DOC-PLAN-001`
**Title:** Critical: Provide Access to Core Planning Documents
**Description:** The `planning.md` file lists numerous "source of truth" documents (e.g., `TA_Noah_MVP_v1.1`, `PB_Noah_Genesis_V1.1_AI_Optimized`, "Final IDE Prompting Guide"). These must be made accessible (e.g., added to repo or linked) for AI/developers to conform to project standards. Also, clarify "MuskOS Engineering Principles."
**Category:** Documentation, Project Management
**Type:** Critical Requirement
**Affected Files/Modules:** `planning.md`, Project Documentation Repository.
**Priority:** [C] Critical
**Status:** Open

**ID:** `DOC-TASK-001`
**Title:** Migrate Tasks to Formal Issue Tracker
**Description:** Plan for and execute the migration of tasks from this `tasks.md` file to a formal issue tracking system (e.g., GitHub Issues, Jira) for better tracking, assignment, and lifecycle management.
**Category:** Project Management, DevOps
**Type:** Process Improvement
**Affected Files/Modules:** `tasks.md`
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

**ID:** `CQ-FE-002`
**Title:** Resolve `AppShell.main.minHeight` Calculation in Theme
**Description:** The `AppShell.main.minHeight` calculation in `frontend/src/styles/theme.ts` using CSS variables is unlikely to work correctly. Refactor to ensure the main content area properly fills available space, likely using flexbox layout solutions in `Layout.tsx` and global styles, rather than `calc()` with potentially undefined CSS variables.
**Category:** Code Quality, Frontend Layout
**Type:** Bug Fix
**Affected Files/Modules:** `frontend/src/styles/theme.ts`, `frontend/src/components/common/Layout.tsx`
**Priority:** [P2] Medium
**Status:** Open

**ID:** `CQ-FE-003`
**Title:** Implement Font Import for "Roboto"
**Description:** If "Roboto" font is not a standard system font expected on all client devices, add a font import statement (e.g., from Google Fonts) in `frontend/index.html` or a global CSS file to ensure consistent typography.
**Category:** Code Quality, Frontend UI
**Type:** Enhancement
**Affected Files/Modules:** `frontend/index.html` (or global CSS)
**Priority:** [P3] Low
**Status:** Open

**ID:** `CQ-FE-004`
**Title:** Frontend Accessibility Review for Color Contrast
**Description:** Perform a color contrast check for the defined color combinations in `frontend/src/styles/theme.ts` (especially primary text on backgrounds, alert/notification colors) to ensure they meet WCAG AA accessibility standards. Adjust theme shades if necessary.
**Category:** Code Quality, Accessibility
**Type:** Enhancement
**Affected Files/Modules:** `frontend/src/styles/theme.ts`
**Priority:** [P2] Medium
**Status:** Open

---
## VIII. Optimization (Performance, Bundle Size, etc.)

**ID:** `OPT-FE-001`
**Title:** Post-MVP: Review Frontend Bundle Size
**Description:** After MVP, review frontend bundle size. Investigate alternatives or optimized imports for large dependencies like `react-markdown`, `date-fns` if they contribute significantly. Ensure tree-shaking is effective.
**Category:** Optimization, Frontend
**Type:** Enhancement
**Affected Files/Modules:** `frontend/` build outputs, `package.json`
**Priority:** [P3] Low
**Status:** Open

**ID:** `OPT-FE-002`
**Title:** Consider Preloading Strategy for Lazy-Loaded Routes
**Description:** For a more advanced optimization post-MVP, investigate preloading strategies for some lazy-loaded routes in `frontend/src/App.tsx` that are highly likely to be visited next (e.g., using `rel="prefetch"` or other techniques).
**Category:** Optimization, Frontend
**Type:** Enhancement
**Affected Files/Modules:** `frontend/src/App.tsx`
**Priority:** [P3] Low
**Status:** Open
---
