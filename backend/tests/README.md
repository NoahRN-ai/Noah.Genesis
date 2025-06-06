# Backend Testing Strategy - Project Noah MVP

This document outlines the testing strategy for the backend application of Project Noah MVP.

## 1. Overview

The testing suite aims to ensure the reliability, correctness, and robustness of the backend components, including API endpoints, services, agent logic, and data interactions. We employ a combination of unit tests and integration tests using Pytest as the primary test runner.

## 2. Types of Tests

### 2.1. Unit Tests

*   **Location:** `backend/tests/unit/`
*   **Purpose:** To test individual modules, classes, or functions in isolation. Dependencies are typically mocked to ensure that the test focuses solely on the logic of the unit under test.
*   **Scope:**
    *   **Services (`services/`):** Test business logic within services (e.g., `firestore_service.py`, `llm_service.py`, `rag_service.py`), mocking external clients like database connections (Firestore `AsyncClient`) or third-party APIs (Vertex AI SDK components).
    *   **Agent Logic (`agent/`):** Test functions within the agent's memory, tools, or core graph nodes, mocking service layer dependencies.
    *   **API Endpoints (`api/`):** Test the logic within API endpoint handlers (e.g., request/response validation, authorization checks, calls to service layers). Service dependencies and authentication (`get_current_active_user`) are mocked.
    *   **Core Components (`core/`):** Test utility functions and core functionalities like security helpers (e.g., `core/security.py`), mocking external SDKs like Firebase Admin.
*   **Key Characteristic:** Fast execution, fine-grained error localization.

### 2.2. Integration Tests

*   **Location:** `backend/tests/integration/`
*   **Purpose:** To test the interaction between different components of the application, ensuring they work together as expected. These tests involve fewer mocks, focusing on actual data flow and component collaboration.
*   **Scope (MVP):**
    *   **Core Application Flows:**
        *   **Chat Flow:** Verifying that an API request to the chat endpoint correctly invokes agent logic, saves interaction history to Firestore (via emulator), while the LLM interaction itself is mocked.
        *   **Patient Data Log Flow:** Verifying that creating and retrieving `PatientDataLog` entries via API endpoints correctly interacts with the `firestore_service` and persists/retrieves data from the Firestore emulator, including authorization checks.
*   **Key Characteristic:** Verifies component interoperability, may require external services like a database emulator, and typically runs slower than unit tests.

## 3. Running Tests

Tests are executed using Pytest.

1.  **Ensure Poetry Environment is Active:**
    If you haven't already, install dependencies and activate the virtual environment:
    ```bash
    cd backend
    poetry install
    poetry shell
    ```

2.  **Run All Tests:**
    From the `backend/` directory:
    ```bash
    pytest
    ```
    Alternatively, if a `Makefile` target `make test` is configured at the project root and handles `cd backend && poetry run pytest`, that can also be used.

3.  **Run Specific Test Files or Tests:**
    ```bash
    # Run all tests in a specific file
    pytest tests/unit/services/test_firestore_service.py

    # Run a specific test function in a file
    pytest tests/unit/services/test_firestore_service.py::test_get_user_profile_found

    # Run tests matching a keyword expression
    pytest -k "firestore and user_profile"
    ```

## 4. Key Libraries and Tools

*   **Pytest:** The primary test runner.
*   **`pytest-mock`:** Used for mocking objects and functions in unit tests.
*   **`httpx.AsyncClient`:** Used for making asynchronous HTTP requests to FastAPI endpoints during API unit and integration tests.
*   **`unittest.mock.AsyncMock` / `MagicMock`:** Used for creating mock objects, especially for asynchronous code.
*   **Google Cloud Firestore Emulator:** Essential for running integration tests that involve Firestore interactions without connecting to a live database.

## 5. Test Environment Setup (for Integration Tests)

Integration tests involving Firestore require the Firestore Emulator to be running and configured.

*   **Environment Variables:** Tests that interact with the emulator expect the following environment variables to be set:
    *   `FIRESTORE_EMULATOR_HOST`: The address of the running emulator (e.g., `localhost:8686`).
    *   `FIRESTORE_PROJECT_ID`: A dummy project ID for the emulator to use (e.g., `test-noah-project`).
    *   Tests are designed to skip if `FIRESTORE_EMULATOR_HOST` is not set.

*   **Starting the Firestore Emulator:**
    You can start the Firestore emulator using the Google Cloud SDK:
    ```bash
    gcloud beta emulators firestore start --project=test-noah-project --host-port="localhost:8686"
    ```
    Alternatively, you can use the Firebase CLI or Docker images for the emulator. Ensure it's running before executing integration tests.

*   **Data Isolation:** Integration tests are designed to clear emulator data before each test run (via the `clear_emulator_firestore` fixture) to ensure test isolation.

## 6. Conventions

*   **File Naming:** Test files are named `test_*.py` (e.g., `test_firestore_service.py`).
*   **Test Function Naming:** Test functions are named `test_*()` (e.g., `test_get_user_profile_success()`).
*   **Fixtures:** Pytest fixtures are used for setting up preconditions, managing resources (like mock objects or emulator clients), and ensuring test isolation.
*   **Asynchronous Tests:** Test functions for asynchronous code are defined using `async def`.

## 7. Coverage (Future Goal)

While specific test coverage targets and reporting (e.g., using `pytest-cov`) are not formally set up for the MVP, the goal is to achieve good coverage for critical application components and business logic. Future enhancements may include integrating coverage reporting into the CI/CD pipeline.
```
