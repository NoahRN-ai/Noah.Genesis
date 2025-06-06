# Noah.Genesis

AI-Powered Nursing Assistant MVP for Noah.RN

## Overview/Purpose

Project Noah.Genesis is the Minimum Viable Product (MVP) for an AI-assisted tool designed to support nurses in their daily workflows. This MVP focuses on delivering core functionalities that demonstrate the potential of AI in streamlining tasks, providing quick information access, and improving patient communication.

## Key Features (MVP)

The MVP encompasses a range of features across its backend, frontend, and database components:

### Backend (Python/FastAPI)
*   **AI Agent Core:** Utilizes LangGraph for building a stateful, multi-turn AI agent capable of complex interactions.
*   **Patient-Friendly Summaries:** Generates easy-to-understand summaries from `PatientDataLog` entries for patients.
*   **Simplified Note Drafting:** Assists nurses in drafting initial sections of nursing notes.
*   **Shift Handoff Reports:** Provides concise summaries and key points for effective shift handovers (simplified for MVP).
*   **Retrieval Augmented Generation (RAG):** Enables the agent to access and cite curated clinical information for evidence-based responses.
*   **Secure API:** FastAPI endpoints are secured using Firebase Authentication.
*   **HIPAA Considerations:** Design and data handling incorporate considerations for HIPAA compliance (detailed in `HIPAA_MVP_Checklist.md`).

### Frontend (TypeScript/React)
*   A user interface (developed in TypeScript and React) allows users to interact with the AI agent, manage patient data, and access other features. *(Frontend codebase is separate but interacts with this backend).*

### Database
*   Patient profiles (`UserProfile`, FHIR-like `PatientProfile`), patient-generated data logs (`PatientDataLog`), and agent interaction history (`InteractionHistory`) are stored securely in Google Cloud Firestore.

## Core Technologies

*   **Backend:** Python (^3.11), FastAPI, Langchain, LangGraph, Pydantic
*   **AI/ML:** Google Vertex AI (Gemini LLMs for generative tasks, Vector Search for RAG), Text Embedding Models (e.g., `textembedding-gecko`)
*   **Database:** Google Cloud Firestore (NoSQL, serverless)
*   **Frontend:** TypeScript, React, Vite *(Based on typical modern frontend stack for such projects)*
*   **Cloud Platform:** Google Cloud Platform (GCP) - services like Cloud Run, Vertex AI, Firestore.
*   **DevOps & Tooling:** Docker, Terraform (for Infrastructure as Code), Pre-commit hooks (Ruff, Black for linting/formatting).

## Project Structure

The project is organized into several key directories:

*   `backend/`: Contains the FastAPI application, including API endpoints, AI agent logic (LangGraph, tools, memory), services for interacting with Firestore and LLMs, and Pydantic data models.
*   `frontend/`: *(Typically contains the React/TypeScript frontend application - not part of this specific backend-focused review but mentioned for completeness).*
*   `terraform/`: Infrastructure as Code configurations for setting up GCP resources.
*   `scripts/`: Utility scripts for development, setup, and operational tasks (e.g., `setup_dev_env.sh`).
*   **Key Documentation Files:**
    *   `DEVELOPMENT.md`: Detailed guide for setting up the development environment and running the project.
    *   `HIPAA_MVP_Checklist.md`: Outlines HIPAA technical safeguards and their status within the MVP.
    *   `tasks.md`: Tracks development tasks and project progress.
    *   `backend/app/agent/README.md`: Details on the agent's memory and capabilities.
    *   `backend/app/agent/prompts.md`: Documentation of prompts used by the AI agent.

## Prerequisites

Before you begin, ensure you have the following installed and configured:

*   Python (version ^3.11 recommended)
*   Poetry (for Python dependency management in the backend)
*   Node.js and npm/yarn (for frontend development, if applicable)
*   Google Cloud SDK (`gcloud` CLI tool)
*   Access to a Google Cloud Platform (GCP) project with the following APIs enabled:
    *   Vertex AI API
    *   Firestore API
    *   Cloud Storage API (if using GCS for RAG or other purposes)
    *   IAM API
    *   Other APIs as required by Terraform configurations.
*   A Firebase Project for user authentication.
*   Terraform CLI (for managing infrastructure).

## Getting Started / Setup

1.  **Clone the repository.**
2.  **Backend Setup:** For detailed instructions on setting up the backend, including Python environment, dependencies, and environment variables, please refer to `DEVELOPMENT.md`.
3.  **Frontend Setup:** *(If applicable, refer to frontend-specific documentation).*
4.  **Environment Variables:** Ensure all necessary environment variables are configured. These typically include GCP project ID, region, Firebase configuration details, and any API keys or paths specified (e.g., `FIREBASE_SERVICE_ACCOUNT_JSON_PATH` if not using default credentials). A `.env.example` file might be provided as a template if available.

## Running the Application

Please refer to `DEVELOPMENT.md` for comprehensive instructions on:
*   Running the backend FastAPI server (e.g., using Uvicorn).
*   Running the frontend development server (if applicable).

## Testing

The backend includes a suite of unit and integration tests developed using Pytest.

*   **Running Tests:**
    *   To run all backend tests, navigate to the `backend/` directory and execute:
        ```bash
        poetry run pytest
        ```
    *   Alternatively, if a `Makefile` target is available at the root:
        ```bash
        make test
        ```
*   **Test Coverage:** (Details on test coverage can be added here once reports are generated).
*   **Further Test Details:** More information on the testing strategy, types of tests, and specific test locations can be found in `backend/tests/README.md` (to be created).

## License

This project is currently under a Proprietary License. Please refer to the `license` field in the `pyproject.toml` file for more details.
```
