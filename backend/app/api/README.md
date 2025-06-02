# Backend API Documentation (Project Noah MVP - V1)

This document provides an overview of the FastAPI-based backend API for Project Noah MVP. The API facilitates interactions with the AI agent, manages user data, and handles conversation history.

## 1. Overview

*   **Framework:** FastAPI
*   **Authentication:** GCP Identity Platform (via Firebase Admin SDK for token verification). All relevant endpoints are protected.
*   **Deployment:** Google Cloud Run
*   **API Version Prefix:** `/api/v1` (defined in `backend.app.core.config.settings.API_V1_PREFIX`)

## 2. Core Components Referenced by API

*   **`main.py`:** Initializes the FastAPI application, includes routers, sets up middleware (CORS, structured logging), and exception handlers. Implements application lifespan events for resource initialization (e.g., Firebase Admin) and cleanup.
*   **`core/config.py`:** Manages application settings and environment variables using Pydantic's `BaseSettings`.
*   **`core/security.py`:** Handles authentication logic, specifically Firebase ID token verification to identify and authenticate users. Provides a `get_current_active_user` dependency for protected endpoints.
*   **`models/api_models.py`:** Defines Pydantic models for API request and response schemas, ensuring data validation and clear contracts.
*   **`api/v1/endpoints/`:** Contains individual `APIRouter` modules for different resource types.
*   **`api/v1/api.py`:** Aggregates all v1 endpoint routers. This is included by `main.py`.
*   **Services (`services/`)**: Contain the business logic (e.g., `firestore_service.py`, `llm_service.py`, `rag_service.py`) called by the API endpoints.
*   **Agent Logic (`agent/`)**: Contains memory management (`memory.py`) called by the API endpoints, and will later host LangGraph orchestration logic.

## 3. Authentication

All protected API endpoints require a valid Firebase ID token to be passed as a Bearer token in the `Authorization` header.

Example: `Authorization: Bearer <FIREBASE_ID_TOKEN>`

The `backend.app.core.security.get_current_active_user` dependency enforces this, providing user information (like `user_id`) to the endpoint handlers. If the token is missing, invalid, or expired, an appropriate HTTP 401 Unauthorized error is returned.

## 4. API Endpoints

All endpoints are prefixed with `/api/v1`. The live OpenAPI documentation (Swagger UI) is available at `/api/v1/docs` and ReDoc at `/api/v1/redoc` when the server is running.

### 4.1. Chat Endpoints

*   **Module:** `backend.app.api.v1.endpoints.chat`
*   **Router Prefix:** `/chat`
*   **Tags:** `Chat` (in OpenAPI documentation)

#### `POST /`
*   **Operation ID:** `handle_chat_message`
*   **Summary:** Handles incoming user chat messages and returns the AI agent's response.
*   **Request Body:** `ChatRequest` (from `backend.app.models.api_models`)
    ```json
    {
      "user_query_text": "What are common symptoms of flu?",
      "user_voice_input_bytes": null, // Optional: base64 encoded string for voice data, for future STT
      "session_id": "optional_existing_session_uuid" // If null or omitted, a new session might be implied/created by the endpoint
    }
    ```
*   **Response Body (200 OK):** `ChatResponse` (from `backend.app.models.api_models`)
    ```json
    {
      "agent_response_text": "Common symptoms include fever, cough, sore throat...",
      "session_id": "generated_or_provided_session_uuid",
      "interaction_id": "agent_interaction_log_uuid" // ID of the agent's response InteractionHistory entry
    }
    ```
*   **Authentication:** Required.
*   **MVP Note (Task 1.5):** This endpoint currently makes a simplified direct call to the `llm_service` after loading/saving history using `agent.memory` functions. Full LangGraph orchestration (including RAG tool use) will be integrated in Phase 3.

### 4.2. Session History Endpoints

*   **Module:** `backend.app.api.v1.endpoints.history`
*   **Router Prefix:** `/sessions`
*   **Tags:** `Session History`

#### `GET /{session_id}/history`
*   **Operation ID:** `get_session_history`
*   **Summary:** Retrieves interaction history for a specific session.
*   **Path Parameters:**
    *   `session_id: str` (required): The ID of the session.
*   **Query Parameters:**
    *   `limit: int` (optional, default: 20, min: 1, max: 100): Number of interactions to return.
*   **Response Body (200 OK):** `SessionHistoryResponse` (from `backend.app.models.api_models`)
    ```json
    {
      "session_id": "session_abc",
      "interactions": [
        // List of InteractionOutput objects
        {
          "interaction_id": "interaction_xyz",
          "session_id": "session_abc",
          "user_id": "user_123",
          "timestamp": "2025-07-04T10:30:00Z",
          "actor": "user", // "user" or "agent"
          "message_content": "Hello there!",
          "tool_calls": null,
          "tool_responses": null
        }
        // ... more interactions
      ]
    }
    ```
*   **Authentication:** Required. For MVP, users can only access history for sessions associated with their `user_id`.

### 4.3. Patient Data Log Endpoints

*   **Module:** `backend.app.api.v1.endpoints.patient_data`
*   **Router Prefix:** `/patient-data-logs`
*   **Tags:** `Patient Data Logs`

#### `POST /`
*   **Operation ID:** `submit_patient_data_log`
*   **Summary:** Submits a new patient data log entry.
*   **Query Parameters:**
    *   `target_patient_user_id: str` (required): The User ID of the patient this data log pertains to.
*   **Request Body:** `PatientDataLogCreateInput` (from `backend.app.models.api_models`)
    ```json
    {
      "timestamp": "2025-07-04T09:00:00Z", // When the observation/event occurred
      "data_type": "observation", // e.g., "observation", "symptom_report"
      "content": {"blood_pressure": "120/80", "heart_rate": 70},
      "source": "Manual Nurse Input" // Optional, defaults to "Noah.Genesis_MVP"
    }
    ```
*   **Response Body (201 Created):** `PatientDataLogResponse` (the created log entry, from `backend.app.models.api_models`).
*   **Authentication:** Required. The `created_by_user_id` for the log is the authenticated user's ID. Authorization (e.g., patient self-logging, nurse logging for others) is simplified for MVP.

#### `GET /`
*   **Operation ID:** `get_patient_data_logs`
*   **Summary:** Retrieves patient data logs for a specified patient.
*   **Query Parameters:**
    *   `patient_user_id: str` (required): User ID of the patient whose logs are to be retrieved.
    *   `limit: int` (optional, default: 20, min: 1, max: 100)
    *   `order_by: str` (optional, default: "timestamp"; e.g., "timestamp" or "created_at")
    *   `descending: bool` (optional, default: true)
*   **Response Body (200 OK):** `List[PatientDataLogResponse]` (from `backend.app.models.api_models`).
*   **Authentication:** Required. For MVP, users can only retrieve their own data logs unless further role-based access is implemented.

### 4.4. User Profile Endpoints

*   **Module:** `backend.app.api.v1.endpoints.user_profiles`
*   **Router Prefix:** `/users`
*   **Tags:** `User Profiles`

#### `GET /{user_id}/profile`
*   **Operation ID:** `read_user_profile`
*   **Summary:** Retrieves a user's profile.
*   **Path Parameters:**
    *   `user_id: str` (required): The ID of the user whose profile is to be retrieved.
*   **Response Body (200 OK):** `UserProfileResponse` (from `backend.app.models.api_models`).
*   **Authentication:** Required. For MVP, users can only access their own profile.

#### `PUT /{user_id}/profile`
*   **Operation ID:** `update_user_profile_endpoint`
*   **Summary:** Updates a user's profile.
*   **Path Parameters:** `user_id: str` (required).
*   **Request Body:** `UserProfileUpdateInput` (from `backend.app.models.api_models`)
    ```json
    {
      "display_name": "Nurse Jane Doe",
      "role": "nurse", // Optional
      "preferences": {"summary_length": "concise", "notification_sound": "default.mp3"} // Optional
    }
    ```
*   **Response Body (200 OK):** `UserProfileResponse` (the updated profile, from `backend.app.models.api_models`).
*   **Authentication:** Required. For MVP, users can only update their own profile.

## 5. Error Handling

The API includes global exception handlers in `main.py` for common error scenarios:
*   **422 Unprocessable Entity (`RequestValidationError`):** For Pydantic model validation failures on request bodies or parameters. The response includes detailed information about the validation errors.
*   **FastAPI `HTTPException`s:** Standard HTTP errors raised within endpoint logic (e.g., 401, 403, 404) are returned as is.
*   **Google Cloud API Errors (`google_exceptions.GoogleAPICallError`):** Errors from downstream Google services (like Firestore, Vertex AI) are caught and mapped to appropriate HTTP status codes (e.g., 503, 404, 403, 429) with a generic detail message.
*   **Generic Server Errors (500 `Exception`):** Any other unhandled exceptions are caught and returned as a generic HTTP 500 Internal Server Error.

Error responses generally follow the format: `{"detail": "Error message"}`. For validation errors, the "detail" will contain a list of specific validation issues.

## 6. `dynamous.ai` API Design Contributions

*   **Clarity & REST Principles:** The API structure attempts to follow RESTful conventions, using clear resource naming (e.g., `/users/{user_id}/profile`, `/patient-data-logs`) and appropriate HTTP methods (GET, POST, PUT).
*   **Data Validation:** Pydantic models are used extensively for request and response validation, ensuring data integrity and providing clear API contracts.
*   **Boilerplate & Best Practices:**
    *   Global exception handlers provide consistent error responses.
    *   Structured logging middleware (basic) is included for request/response logging.
    *   FastAPI's dependency injection (`Depends`) is used for authentication and will be for other shared components.
*   **Modularity:** The API is organized into modules by resource type (`endpoints/chat.py`, etc.), all aggregated by `api/v1/api.py`, promoting maintainability.
*   **Security:** Authentication using Firebase ID tokens is integrated as a core part of the API design for protected endpoints.
*   **`Logos_Accord` Considerations:** API responses are designed to be factual and clear. Error messages are informative but avoid exposing sensitive internal details. The overall design supports user-centric data management.
