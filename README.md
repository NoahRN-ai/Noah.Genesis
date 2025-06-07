
# Project Noah Genesis MVP

Welcome to Project Noah, an AI-powered nursing assistant. This MVP aims to provide core functionalities including intelligent chat, patient data logging, user profile management, and AI-generated summaries.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Firebase Project Setup](#firebase-project-setup)
- [Local Development Setup](#local-development-setup)
  - [1. Clone Repository](#1-clone-repository)
  - [2. Initial Environment Setup Script](#2-initial-environment-setup-script)
  - [3. Google Cloud (GCP) CLI Authentication](#3-google-cloud-gcp-cli-authentication)
  - [4. Environment Variables (.env)](#4-environment-variables-env)
- [Backend Development](#backend-development)
  - [Dependencies](#dependencies)
  - [Running the Backend](#running-the-backend)
- [Frontend Development](#frontend-development)
  - [Dependencies (Assumed)](#dependencies-assumed)
  - [Environment Variables (Frontend)](#environment-variables-frontend)
  - [Running the Frontend](#running-the-frontend)
- [Running the Full Application](#running-the-full-application)
- [Code Structure](#code-structure)
- [Available `make` Commands](#available-make-commands)
- [Contributing](#contributing)

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Git:** For version control.
*   **Python:** Version 3.11 (as specified in `pyproject.toml`). Using a Python version manager like `pyenv` is recommended.
*   **Poetry:** For Python backend dependency management. Follow installation instructions at [python-poetry.org](https://python-poetry.org/docs/#installation).
*   **Node.js:** Latest LTS version recommended (e.g., v18 or v20). Required for the frontend. Use a version manager like `nvm`.
*   **npm or Yarn:** JavaScript package manager (comes with Node.js or can be installed separately).
*   **Google Cloud SDK (gcloud CLI):** For interacting with GCP services. Install from [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install).
*   **Firebase CLI (Optional but Recommended):** For managing Firebase projects. Install via `npm install -g firebase-tools`.
*   **Make (Optional but Recommended):** For using the `Makefile` to run common project tasks.
*   **Docker (Optional):** If you plan to run local instances of PostgreSQL (for RAG development) or other containerized services.

## Firebase Project Setup

Project Noah utilizes Firebase for authentication and as a NoSQL database (Firestore).

1.  **Create a Firebase Project:**
    *   Go to the [Firebase Console](https://console.firebase.google.com/).
    *   Click on "Add project" and follow the on-screen instructions.

2.  **Enable Authentication:**
    *   In your Firebase project, navigate to "Authentication" (under Build).
    *   Go to the "Sign-in method" tab.
    *   Enable "Email/Password" provider.
    *   Enable "Google" provider, providing a project support email.

3.  **Set up Firestore Database:**
    *   Navigate to "Firestore Database" (under Build).
    *   Click "Create database."
    *   Start in **test mode** for initial development (allows open access). Remember to secure your rules before production.
        *   Default rules for test mode:
            ```
            rules_version = '2';
            service cloud.firestore {
              match /databases/{database}/documents {
                match /{document=**} {
                  allow read, write: if true; // Insecure, for testing only!
                }
              }
            }
            ```
    *   Choose a region for your Firestore database (e.g., `us-central`).

4.  **Obtain Firebase Configuration for Frontend:**
    *   In your Firebase project settings (click the gear icon next to "Project Overview"), scroll down to "Your apps."
    *   Click the web icon (`</>`) to add a web app.
    *   Register your app (e.g., "Noah MVP Frontend"). You do **not** need to set up Firebase Hosting at this stage.
    *   After registration, Firebase will provide you with a `firebaseConfig` object. This contains your `apiKey`, `authDomain`, `projectId`, etc. You will need these for the frontend setup.

5.  **Generate a Service Account Key for Backend:**
    *   In the Firebase Console, go to "Project settings" > "Service accounts."
    *   Select "Python" for Admin SDK configuration snippets.
    *   Click "Generate new private key" and save the JSON file securely. **Do not commit this file to your repository.**
    *   You will use the path to this file in your backend `.env` configuration (`FIREBASE_SERVICE_ACCOUNT_JSON_PATH`) or set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to its path.

## Local Development Setup

Follow these steps to set up your local development environment after meeting the prerequisites.

### 1. Clone Repository

```bash
git clone <YOUR_REPOSITORY_URL> # Replace <YOUR_REPOSITORY_URL> with the actual URL
cd <YOUR_REPOSITORY_DIRECTORY>   # Replace <YOUR_REPOSITORY_DIRECTORY> with the folder name
```

### 2. Initial Environment Setup Script

The project includes a script to help automate initial setup:

```bash
chmod +x scripts/setup_dev_env.sh
./scripts/setup_dev_env.sh
```
This script will:
*   Check for Poetry and guide installation if missing.
*   Install backend Python dependencies using `poetry install --no-root`.
*   Install pre-commit hooks for code quality.
*   Guide you on GCP CLI authentication.

### 3. Google Cloud (GCP) CLI Authentication

Authenticate your local environment to access GCP services:

```bash
gcloud auth application-default login
```
Follow the prompts. Then, set your default GCP project (replace `YOUR_GCP_PROJECT_ID_HERE` with your actual project ID, which will be provisioned by Terraform in Task 0.1):

```bash
gcloud config set project YOUR_GCP_PROJECT_ID_HERE
```

### 4. Environment Variables (`.env`)

The application uses a `.env` file at the project root for managing environment-specific configurations for local development. This file is ignored by Git.

Create a `.env` file in the project root. Refer to `DEVELOPMENT.md` for a detailed example structure. Key variables to include:

*   `GCP_PROJECT_ID="YOUR_GCP_PROJECT_ID_HERE"`
*   `LOG_LEVEL="DEBUG"` (or `INFO`)
*   `VERTEX_AI_REGION="us-central1"` (or your project's region)
*   `DEFAULT_LLM_MODEL_NAME="gemini-1.0-pro-001"` (or other preferred model)
*   `FIREBASE_SERVICE_ACCOUNT_JSON_PATH="/path/to/your/firebase-service-account-key.json"` (absolute path to your downloaded Firebase SA key)
    *   _Alternatively, set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable system-wide to this path._

## Backend Development

The backend is built with Python, FastAPI, and Poetry.

### Dependencies

Backend dependencies are managed by Poetry and listed in `pyproject.toml`. They are installed during the `./scripts/setup_dev_env.sh` script or via `make setup` (which runs `poetry install --no-root`).

Key backend libraries include: `fastapi`, `uvicorn`, `pydantic`, `google-cloud-firestore`, `google-cloud-aiplatform`, `firebase-admin`, `langgraph`.

### Running the Backend

Ensure your root `.env` file is correctly configured, especially `GCP_PROJECT_ID` and Firebase service account details.

To start the backend development server (FastAPI with Uvicorn):

```bash
make run_dev_server
```
Or, using Poetry directly:
```bash
poetry run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
The server will typically be available at `http://localhost:8000` and will auto-reload on code changes.

## Frontend Development

The frontend is a React application built with Vite and TypeScript.

### Dependencies (Assumed)

Frontend dependencies are managed with `npm` or `yarn` and would be listed in `frontend/package.json`. Since this file was not directly accessible during README generation, this list is based on common usage for the project's features and previous user prompts:

*   Core: `react`, `react-dom`
*   Build: `vite`, `@vitejs/plugin-react`, `typescript`
*   UI & Styling: `@mantine/core`, `@mantine/hooks`, `@mantine/form`, `@mantine/notifications`, `@mantine/dates`, `@tabler/icons-react`
*   Routing: `react-router-dom`
*   Validation: `zod`
*   Utilities: `uuid`, `@types/uuid`, `react-markdown`, `remark-gfm`, `dayjs`
*   Firebase: `firebase` (client-side SDK)

To install frontend dependencies, navigate to the `frontend` directory and run:
```bash
cd frontend
npm install # Or yarn install
cd ..
```

### Environment Variables (Frontend)

The frontend requires Firebase configuration to connect to your Firebase project. Create a `.env` file inside the `frontend` directory (`frontend/.env`):

```env
# frontend/.env

# Firebase Web App Configuration (copy from your Firebase project settings - Step 4 in Firebase Project Setup)
VITE_FIREBASE_API_KEY="YOUR_API_KEY"
VITE_FIREBASE_AUTH_DOMAIN="YOUR_AUTH_DOMAIN"
VITE_FIREBASE_PROJECT_ID="YOUR_PROJECT_ID"
VITE_FIREBASE_STORAGE_BUCKET="YOUR_STORAGE_BUCKET"
VITE_FIREBASE_MESSAGING_SENDER_ID="YOUR_MESSAGING_SENDER_ID"
VITE_FIREBASE_APP_ID="YOUR_APP_ID"

# URL for the backend API
VITE_API_BASE_URL="http://localhost:8000/api/v1"
```
**Note:** Variables in Vite need to be prefixed with `VITE_`.

### Running the Frontend

After installing dependencies and setting up `frontend/.env`:

```bash
cd frontend
npm run dev # Or yarn dev
cd ..
```
This will start the Vite development server, typically available at `http://localhost:5173` (or another port if 5173 is busy).

## Running the Full Application

To run the full application locally:
1.  Ensure your root `.env` and `frontend/.env` files are configured.
2.  Start the backend server (usually on `http://localhost:8000`).
3.  Start the frontend development server (usually on `http://localhost:5173`).
4.  Open your browser and navigate to the frontend URL (e.g., `http://localhost:5173`).

## Code Structure

*   `backend/`: Contains the Python FastAPI application.
    *   `app/`: Core backend logic (API endpoints, services, models).
    *   `tests/`: Backend tests.
*   `frontend/`: Contains the React/TypeScript frontend application.
    *   `src/`: Frontend source code (components, pages, services, contexts).
*   `scripts/`: Utility scripts for development and setup.
*   `terraform/`: Infrastructure as Code (Terraform) for provisioning GCP resources. See `DEVELOPMENT.MD` for more details on its usage and context.
*   `DEVELOPMENT.md`: Detailed development practices and guidelines.
*   `Makefile`: Shortcuts for common development tasks.
*   `pyproject.toml`: Backend dependency management with Poetry.
*   `README.md`: This file - project overview and setup.

## Available `make` Commands

The main `Makefile` provides several useful commands (run from the project root):

*   `make setup`: Install backend dependencies and pre-commit hooks.
*   `make lint`: Check code style and errors with Ruff.
*   `make format`: Format code with Ruff.
*   `make test`: Run backend tests.
*   `make run_dev_server`: Start the backend FastAPI development server.
*   `make build_docker`: Build the Docker image for the backend.
*   `make clean`: Remove build artifacts and cache.

Run `make help` to see all commands.

## Contributing

(Placeholder - Contribution guidelines will be added here later.)
=======
# Noah.Genesis: AI-Powered Nursing Assistant MVP

## 1. Project Overview

*   **Name:** Noah.Genesis (AI-Powered Nursing Assistant MVP for Noah.RN)
*   **Purpose:** An AI-assisted tool designed to support nurses in their daily workflows, streamline tasks, provide quick information access, and improve patient communication.
*   **Problem it Solves:** Addresses the challenges nurses face with information overload, time-consuming documentation, and the need for rapid, context-aware clinical information at the point of care. Noah.Genesis aims to reduce administrative burden, enhance decision-making support, and allow nurses to focus more on direct patient care.

## 2. Key Features & Functionalities

### AI & Backend Core
*   **AI Agent Core:** Utilizes LangGraph for building a stateful, multi-turn AI agent capable of complex interactions and tool usage.
*   **Patient-Friendly Summaries:** Generates easy-to-understand summaries from `PatientDataLog` entries for patients or their families.
*   **Nursing Note Drafting Assistance:** Assists nurses in drafting initial sections of nursing notes based on patient data and interactions.
*   **Shift Handoff Reports:** Provides concise summaries and key points from patient activity and AI interactions for effective shift handovers (simplified for MVP).
*   **Retrieval Augmented Generation (RAG):** Enables the agent to access and cite curated clinical information from a knowledge base (e.g., PDF documents in Google Cloud Storage) for evidence-based responses.
*   **Secure API:** FastAPI backend providing RESTful endpoints, secured using Firebase Authentication.
*   **HIPAA Compliance Considerations:** Design and data handling incorporate considerations for HIPAA technical safeguards (see `HIPAA_MVP_Checklist.md` and `SECURITY_AND_COMPLIANCE_PLAN.md`).
*   **Patient Data Management (Firestore):**
    *   `UserProfile`: Stores user-specific information and preferences.
    *   `PatientProfile`: FHIR-like model for patient demographic and clinical overview.
    *   `PatientDataLog`: Records patient-generated or nurse-inputted data points.
    *   `Observation`: FHIR-like model for specific patient observations.
    *   `MedicationStatement`: FHIR-like model for patient medication information.
    *   `InteractionHistory`: Logs conversations between users and the AI agent.
*   **AI Contextual Store (`ai_contextual_stores`):** Firestore collection to store summaries, patient preferences relevant to AI, and other contextual data to maintain continuity and personalize AI interactions.
*   **Conceptual Features (from `noah_*` design documents):**
    *   Plan of Care / To-Do List Management (future)
    *   Automated Event Capture (future)
    *   Structured Reporting Frameworks (future)

### Frontend
*   **User Interface:** A React-based Single Page Application (SPA) using TypeScript and Mantine UI for user interaction with the AI agent, data viewing, and other functionalities.

## 3. Architecture

*   **Overall Architecture:**
    *   **Frontend:** React SPA (TypeScript, Mantine UI) running in the user's browser.
    *   **Backend:** Python FastAPI application deployed as a serverless container on Google Cloud Run.
    *   **Database:** Google Cloud Firestore (NoSQL, serverless) for application data, patient records, and AI context.
    *   **AI/ML:** Google Vertex AI for Large Language Models (Gemini), Vector Search (for RAG), and Text Embedding Models.
*   **Backend Details:**
    *   **API Layer:** FastAPI routers define HTTP endpoints. Pydantic models for request/response validation.
    *   **Service Layer:** Business logic encapsulated in services (e.g., `FirestoreService`, `LLMService`, `RAGService`).
    *   **Data Models:** Pydantic models for API contracts and Firestore data structures (`firestore_models.py`, `api_models.py`).
    *   **Agent Logic:** LangGraph orchestrates AI interactions, tool usage, and state management.
*   **Frontend Details:**
    *   **Components:** Reusable UI elements built with React and Mantine UI.
    *   **Services:** Axios-based API client (`apiClient.ts`) for communicating with the backend; specific services for chat, auth, etc.
    *   **State Management:** React Context API for global state (e.g., authentication); component-level state for local UI needs.
*   **AI Components:**
    *   **LLMs:** Google Gemini models (e.g., `gemini-pro`) via Vertex AI for generative tasks, summarization, and chat.
    *   **Vector Search:** Vertex AI Vector Search (formerly Matching Engine) for efficient similarity search in the RAG pipeline.
    *   **Embedding Models:** Google Text Embedding Models (e.g., `textembedding-gecko`) via Vertex AI for creating vector representations of text for RAG.
*   **Data Flow (Example - RAG Query):**
    1.  User sends a query via the React frontend.
    2.  Frontend service calls the backend FastAPI `/chat` endpoint.
    3.  Authenticated request is processed by the AI Agent (LangGraph).
    4.  Agent identifies the need for RAG.
    5.  Query is embedded using Vertex AI Text Embedding Model.
    6.  Embedding is used to search relevant documents in Vertex AI Vector Search.
    7.  Retrieved document chunks are passed as context to the Gemini LLM.
    8.  LLM generates a response based on the query and context.
    9.  Response is sent back through FastAPI to the frontend and displayed to the user.

## 4. Technology Stack

*   **Backend:** Python (3.11+), FastAPI, Pydantic, Langchain, LangGraph.
*   **Frontend:** TypeScript, React (v18+), Vite, Mantine UI, Axios, React Router (v6).
*   **Database:** Google Cloud Firestore.
*   **AI/ML:** Google Vertex AI (Gemini LLMs, Vector Search, Text Embedding Models).
*   **Cloud Platform:** Google Cloud Platform (GCP)
    *   Cloud Run (for backend service hosting)
    *   Vertex AI (for LLMs, embeddings, vector search)
    *   Firestore (for database)
    *   Cloud Storage (for RAG document storage, other files)
    *   Secret Manager (for managing secrets)
    *   Cloud Build (for CI/CD, Docker image builds)
    *   Identity Platform (via Firebase for authentication)
*   **DevOps & Tooling:** Docker, Terraform (for Infrastructure as Code), Poetry (Python dependency management), Pre-commit hooks (Ruff, Black), ESLint, Prettier (frontend code quality).

## 5. Project Structure

```
Noah.Genesis/
├── backend/                    # Python FastAPI backend application
│   ├── app/                    # Core application code
│   │   ├── api/                # API endpoint routers (v1/)
│   │   │   ├── v1/
│   │   │   │   └── endpoints/  # Individual endpoint files (chat.py, etc.)
│   │   │   └── README.md       # API documentation overview
│   │   ├── agent/              # LangGraph agent logic, tools, memory, prompts
│   │   ├── core/               # Core settings, security, config
│   │   ├── models/             # Pydantic models (API, DB)
│   │   ├── services/           # Business logic (Firestore, LLM, RAG)
│   │   └── main.py             # FastAPI app instantiation
│   ├── tests/                  # Pytest tests for the backend (unit/, integration/)
│   ├── Dockerfile              # Dockerfile for backend service
│   └── cloudbuild.yaml         # Cloud Build configuration for backend
├── frontend/                   # React+TypeScript frontend application
│   ├── public/                 # Static assets
│   ├── src/                    # Main application source code
│   │   ├── assets/             # Static assets imported into components
│   │   ├── components/         # Reusable UI components
│   │   ├── contexts/           # React Context API providers
│   │   ├── hooks/              # Custom React hooks
│   │   ├── pages/              # Top-level view components
│   │   ├── services/           # API client and other services
│   │   ├── styles/             # Global styles, theme
│   │   ├── types/              # TypeScript type definitions
│   │   ├── App.tsx             # Main application component
│   │   └── main.tsx            # Application entry point
│   ├── index.html              # Main HTML entry point
│   ├── vite.config.ts          # Vite configuration
│   ├── tsconfig.json           # TypeScript configuration
│   └── README.md               # Frontend setup and details
├── terraform/                  # Terraform configurations for GCP infrastructure
├── scripts/                    # Utility and setup scripts (e.g., setup_dev_env.sh)
├── .env.example                # Example environment file
├── .gitignore
├── .pre-commit-config.yaml     # Pre-commit hook configurations
├── DEVELOPMENT.md              # Developer setup guide, coding standards
├── HIPAA_MVP_Checklist.md      # HIPAA safeguard considerations for MVP
├── SECURITY_AND_COMPLIANCE_PLAN.md # Firestore rules and IAM plan
├── Makefile                    # Make commands for common dev tasks
├── pyproject.toml              # Poetry dependency management and tool configs (Ruff, Black)
├── tasks.md                    # Ongoing development tasks and backlog
└── README.md                   # This file
```

## 6. Prerequisites

*   **Python:** Version 3.11+ (as specified in `pyproject.toml`).
*   **Poetry:** For Python dependency management in the backend.
*   **Node.js & npm/yarn:** For frontend development.
*   **Google Cloud SDK (`gcloud` CLI):** Installed and authenticated.
*   **GCP Project:** A Google Cloud Platform project with the following APIs enabled:
    *   Vertex AI API
    *   Cloud Firestore API
    *   Cloud Storage API
    *   Secret Manager API
    *   Cloud Build API
    *   Identity Platform (Firebase)
    *   (And others as required by Terraform configurations)
*   **Firebase Project:** A Firebase project linked to the GCP project for authentication.
*   **Terraform CLI:** For managing infrastructure.

## 7. Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd Noah.Genesis
    ```

2.  **Backend Setup:**
    *   Navigate to the `backend/` directory.
    *   Refer to `DEVELOPMENT.md` for detailed steps, which include:
        *   Installing Poetry: 
        *   Installing dependencies:
        *   Setting up environment variables: Create a `.env` file in the project root (see `.env.example` and `DEVELOPMENT.md`). Key variables include `GCP_PROJECT_ID`, `VERTEX_AI_REGION`, `FIREBASE_SERVICE_ACCOUNT_JSON_PATH` (if not using Application Default Credentials).
        *   GCP Authentication: `gcloud auth application-default login`.
    *   Pre-commit hooks: `poetry run pre-commit install` (run from project root).

3.  **Frontend Setup:**
    *   Navigate to the `frontend/` directory.
    *   Refer to `frontend/README.md` for detailed steps, which include:
        *   Installing dependencies: `npm install` (or `yarn install`).
        *   Setting up environment variables: Create a `.env` file in the `frontend/` directory for variables like `VITE_API_BASE_URL`.

4.  **Terraform Setup (Infrastructure):**
    *   Navigate to the `terraform/` directory.
    *   Initialize Terraform: `terraform init`.
    *   Review and apply configurations: `terraform plan` then `terraform apply`. (Ensure your `gcloud` CLI is authenticated with permissions to create resources).

## 8. Running the Application

*   **Backend (FastAPI):**
    *   From the project root:
        ```bash
        make run_dev_server
        ```
    *   Or, navigate to `backend/` and run:
        ```bash
        poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ```
    *   The backend API will typically be available at `http://localhost:8000`.

*   **Frontend (Vite Dev Server):**
    *   Navigate to the `frontend/` directory:
        ```bash
        npm run dev
        ```
    *   The frontend application will typically be available at `http://localhost:5173` (or another port specified by Vite).

## 9. Testing

*   **Backend (Pytest):**
    *   Unit and integration tests are located in `backend/tests/`.
    *   To run all backend tests from the project root:
        ```bash
        make test
        ```
    *   Or, navigate to `backend/` and run:
        ```bash
        poetry run pytest
        ```
*   **Frontend:**
    *   (Frontend testing setup using Jest and React Testing Library is planned as per `tasks.md`. Refer to `frontend/README.md` for future updates on running frontend tests.)

## 10. API Documentation

*   **Live OpenAPI Docs (Swagger UI):** Available at `/api/v1/docs` when the backend server is running.
*   **Live ReDoc:** Available at `/api/v1/redoc` when the backend server is running.
*   **Static Documentation:** Refer to `backend/app/api/README.md` for an overview of API design and endpoint details.

## 11. Deployment

*   **Backend (Cloud Run):**
    *   The backend FastAPI application is containerized using `backend/Dockerfile`.
    *   Deployment to Google Cloud Run is automated via Google Cloud Build, configured in `backend/cloudbuild.yaml`.
    *   Cloud Build is typically triggered by commits to a specific branch (e.g., `main` or `master`) in the connected Git repository.
    *   Environment variables for the Cloud Run service should be configured securely, often by linking to secrets stored in Google Cloud Secret Manager.
*   **Frontend (e.g., Firebase Hosting, Google Cloud Storage):**
    *   The frontend is a static build generated by `npm run build` (in `frontend/dist/`).
    *   This build can be deployed to various static hosting providers like Firebase Hosting or a GCS bucket configured for website hosting.
    *   (Deployment details for frontend to be further specified in `frontend/README.md` or a dedicated deployment guide).

## 12. Security and Compliance

*   **HIPAA Compliance:**
    *   The application has been designed with HIPAA technical safeguards in mind.
    *   Refer to `HIPAA_MVP_Checklist.md` for a detailed breakdown of implemented safeguards and considerations.
    *   `SECURITY_AND_COMPLIANCE_PLAN.md` outlines Firestore security rules and IAM policies.
*   **Authentication:**
    *   User authentication is handled by Firebase Authentication (via GCP Identity Platform). Backend APIs are secured, requiring valid Firebase ID tokens.
*   **Authorization:**
    *   Basic self-access rules are implemented (users can access/modify their own data).
    *   Firestore Security Rules provide server-side enforcement of data access policies (see `firestore.rules` and `SECURITY_AND_COMPLIANCE_PLAN.md`).
    *   Role-Based Access Control (RBAC) for more granular permissions (e.g., differentiating between 'nurse' and 'patient' roles for accessing specific data) is a key area for future development. Custom claims in Firebase can support RBAC.
*   **Data Encryption:**
    *   **At Rest:** Data stored in Firestore and Google Cloud Storage is automatically encrypted at rest by Google.
    *   **In Transit:** Communication with GCP services (Firestore, Vertex AI, etc.) and between the client and backend API is secured using HTTPS (TLS).

## 13. Contribution Guidelines

*   Refer to `DEVELOPMENT.md` for detailed information on:
    *   Setting up the development environment.
    *   Coding standards (linting with Ruff, formatting with Black/Ruff-formatter).
    *   Type hinting (mandatory for Python).
    *   Docstrings (Google Style Python Docstrings).
*   **Pre-commit Hooks:** Ensure pre-commit hooks are installed (`pre-commit install`) to automatically lint and format code before committing. These are configured in `.pre-commit-config.yaml`.
*   **Branching Strategy (General Recommendation):**
    *   Develop features in separate branches (e.g., `feature/my-new-feature`).
    *   Create Pull Requests (PRs) to merge features into the main development branch (e.g., `develop` or `main`).
    *   Ensure tests pass and code reviews are conducted before merging PRs.
*   **Issue Tracking:** Use the issue tracker associated with the repository (e.g., GitHub Issues) to report bugs, suggest features, and track tasks (see also `tasks.md`).

## 14. Roadmap & Future Plans

The Noah.Genesis MVP is the first step towards a more comprehensive AI nursing assistant. Key areas for future development include:

*   **Advanced AI Capabilities:**
    *   Enhanced RAG with more diverse knowledge sources and sophisticated retrieval.
    *   Proactive alerting and predictive insights (e.g., sepsis detection, fall risk).
    *   Full implementation of features outlined in `noah_future_expansion_roadmap/future_expansion_roadmap.md`, such as advanced systems assessment AI, "What-If" simulation sandbox.
*   **Full RBAC Implementation:** Granular roles and permissions for different user types.
*   **EMR Integration:** Bi-directional integration with Electronic Medical Record systems using standards like HL7 FHIR.
*   **Expanded Agent Toolset:** More tools for the LangGraph agent to interact with external systems and perform complex tasks.
*   **Enhanced UI/UX:** Richer data visualizations, more interactive components, and improved workflows based on user feedback.
*   **Comprehensive Testing:** Increased test coverage for both backend and frontend, including end-to-end tests.
*   **Observability:** Advanced monitoring, logging, and tracing for performance and reliability.

Refer to `tasks.md` and `noah_future_expansion_roadmap/future_expansion_roadmap.md` for more detailed future plans and ongoing development items.

## 15. License

This project is currently under a **Proprietary License**.
Please refer to the `license` field in the `pyproject.toml` file for more details.
For any questions regarding licensing, please contact the project maintainers.

---
*This README was last updated on 6/7/2025.*

