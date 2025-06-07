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
