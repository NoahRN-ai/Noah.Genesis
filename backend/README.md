# Project Noah MVP - Backend Application

This directory contains the source code for the backend application of Project Noah MVP. It's a Python FastAPI application designed to serve as the core logic and API layer for the AI agent nurse.

## 1. Overview

The backend provides a RESTful API for:
*   Handling chat interactions with the AI agent.
*   Managing user profiles and preferences.
*   Storing and retrieving patient-related data logs.
*   Logging and retrieving conversation history.

It is built with a focus on modularity, scalability (via Cloud Run), and security, adhering to the principles outlined in `TA_Noah_MVP_v1.1` and other guiding project documents.

## 2. Technology Stack

*   **Programming Language:** Python 3.11+
*   **Web Framework:** FastAPI
*   **ASGI Server:** Uvicorn
*   **Data Validation & Settings:** Pydantic
*   **Dependency Management:** Poetry
*   **Authentication:** GCP Identity Platform (Firebase Authentication) - Tokens verified by Firebase Admin SDK.
*   **Primary Database (User/App Data):** Google Cloud Firestore (for user profiles, patient data logs, interaction history).
*   **LLM Interaction:** Google Vertex AI (via `llm_service.py`).
*   **RAG System (Vector Store):** Google Vertex AI Vector Search.
*   **RAG System (Embedding Generation):** Google Vertex AI Embedding API (`textembedding-gecko@003`).
*   **Agent Orchestration (Future):** LangGraph (to be fully integrated in Phase 3).
*   **Deployment:** Docker & Google Cloud Run (managed via Google Cloud Build).
*   **Linting/Formatting:** Ruff (Black-compatible styling).
*   **Testing:** Pytest.

## 3. Project Structure (`backend/`)

*   **`app/`**: Main application package.
    *   **`main.py`**: FastAPI application entry point, global middleware, exception handlers, lifespan events, and main API router inclusion.
    *   **`core/`**: Core utilities.
        *   `config.py`: Pydantic `BaseSettings` for application configuration and environment variables.
        *   `security.py`: Authentication logic (Firebase ID token verification, user model).
    *   **`models/`**: Pydantic data models.
        *   `api_models.py`: Schemas for API request and response bodies.
        *   `firestore_models.py`: Schemas for data objects stored in Firestore.
    *   **`api/v1/`**: Version 1 of the API.
        *   `api.py`: Aggregates all endpoint routers for API v1.
        *   `endpoints/`: Individual modules for specific API resources (e.g., `chat.py`, `user_profiles.py`, `history.py`, `patient_data.py`).
    *   **`services/`**: Business logic layer, interacting with databases and external services.
        *   `firestore_service.py`: CRUD operations for Firestore collections.
        *   `llm_service.py`: Abstraction layer for interacting with LLMs on Vertex AI.
        *   `rag_service.py`: Service for RAG system (querying Vector Search, retrieving chunk details).
    *   **`agent/`**: Logic related to the AI agent's behavior and memory.
        *   `memory.py`: Short-term memory management (saving/loading conversation history from Firestore).
        *   *(Future: `graph.py` for LangGraph state machine, `tools.py` for agent tools - Phase 3)*
*   **`tests/`**: Pytest unit and integration tests (to be developed).
*   **`Dockerfile`**: Defines the Docker container image for the backend application.
*   **`cloudbuild.yaml`**: Google Cloud Build configuration for CI/CD pipeline (build, push to Artifact Registry, deploy to Cloud Run).
*   **`README.md`**: This file - overview of the backend.

## 4. Setup and Development

For detailed instructions on setting up your local development environment, installing dependencies, running the application, linting, formatting, testing, and configuring local environment variables, please refer to the main **`DEVELOPMENT.md`** file in the **repository root**.

Common tasks can be run using the `Makefile` in the repository root (e.g., `make lint`, `make test`, `make run_dev_server`).

## 5. API Documentation

Detailed API endpoint documentation (including paths, methods, request/response schemas, and authentication requirements) can be found in:
*   **`backend/app/api/README.md`**
*   Live OpenAPI documentation will be available at `/api/v1/docs` (Swagger UI) and `/api/v1/redoc` (ReDoc UI) when the server is running.

## 6. Deployment

The application is designed for deployment to Google Cloud Run.
*   The `backend/Dockerfile` defines how the container image is built.
*   The `backend/cloudbuild.yaml` script defines the CI/CD pipeline using Google Cloud Build. This pipeline automates building the Docker image, pushing it to Google Artifact Registry, and deploying it to the configured Cloud Run service.
*   Environment variables for the Cloud Run service, including sensitive values like database credentials or API keys (if any were needed beyond SA auth), are intended to be sourced from Google Secret Manager, as configured in `cloudbuild.yaml`.

## 7. Key Architectural Principles & `dynamous.ai` Contributions

*   **MVP Focus & Radical Velocity:** Prioritizing essential features and leveraging managed GCP services (Cloud Run, Firestore, Vertex AI Suite) to accelerate development and reduce operational overhead.
*   **Modularity & Separation of Concerns:** Code is organized into distinct layers (API, services, models, core) for improved maintainability and testability.
*   **API-Driven Design:** A well-defined FastAPI interface serves as the entry point for all backend functionalities.
*   **Configuration Management:** Centralized application settings via Pydantic `BaseSettings` and environment variables.
*   **Security:** Authentication handled via GCP Identity Platform (Firebase). Secure access to GCP services via IAM roles for service accounts. Placeholder for robust authorization logic.
*   **Scalability:** Cloud Run provides automatic scaling capabilities for the serverless backend.
*   **Observability:** Basic structured logging and global exception handling are implemented. Further integration with Cloud Monitoring and Logging is planned (some via Terraform Task 0.4).
*   **Adherence to `Logos_Accord`:** Design considerations for data privacy, responsible AI interaction, and information sanctity are integrated into data models and service logic where applicable.
*   **`ALETHIA_FIDELITY_CONSTRAINT`:** Supported by the RAG system design, which aims to provide source information for retrieved knowledge.
