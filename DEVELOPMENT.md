# Project Noah MVP - Development Guide

Welcome to the Project Noah MVP development environment! This guide will help you set up your local environment, understand coding standards, and run common development tasks.

## 1. Prerequisites

*   **Git:** Ensure Git is installed on your system.
*   **Python:** Python 3.11 (as specified in `pyproject.toml`). Using a Python version manager like `pyenv` is recommended.
*   **Poetry:** Python dependency management and packaging tool.
*   **Google Cloud SDK (gcloud CLI):** For interacting with GCP.
*   **Docker (Optional):** For running local databases or other containerized services during development.
*   **Make (Optional but Recommended):** For using the `Makefile` to run common tasks.

## 2. Initial Setup

1.  **Clone the Repository:**
    ```bash
    git clone <YOUR_GITHUB_REPO_URL_FOR_Noah.Genesis>
    cd Noah.Genesis
    ```

2.  **Run the Setup Script:**
    The `scripts/setup_dev_env.sh` script automates several setup steps.
    ```bash
    chmod +x scripts/setup_dev_env.sh
    ./scripts/setup_dev_env.sh
    ```
    This script will:
    *   Check for Poetry and guide installation if missing.
    *   Install project dependencies using `poetry install --no-root`.
    *   Install pre-commit hooks using `poetry run pre-commit install`.
    *   Guide you on setting up local GCP authentication via `gcloud auth application-default login`.
    *   Provide optional commands for setting up local Dockerized PostgreSQL+pgvector.

3.  **Set up Local GCP Authentication:**
    If you haven't already during the script, run:
    ```bash
    gcloud auth application-default login
    ```
    Follow the prompts. This allows your local application to authenticate to GCP services using your user credentials.
    Then, configure your default project (replace `YOUR_GCP_PROJECT_ID_HERE` with the actual project ID after it's created by Terraform Task 0.1):
    ```bash
    gcloud config set project YOUR_GCP_PROJECT_ID_HERE
    ```

4.  **Create `.env` File for Local Configuration:**
    The application uses `python-dotenv` to load environment variables from a `.env` file in the project root during local development. This file is **not** committed to Git (it should be in `.gitignore`).

    Create a `.env` file in the project root (e.g., `Noah.Genesis/.env`) with necessary local configurations:
    ```env
    # .env Example
    GCP_PROJECT_ID="YOUR_GCP_PROJECT_ID_HERE" # Your actual GCP Project ID for dev/testing
    LOG_LEVEL="DEBUG"

    # For FastAPI backend (backend/app/main.py)
    # These might be specific to your Pydantic settings model

    # Example for local RAG PostgreSQL database (if using local Docker setup from setup_dev_env.sh)
    # RAG_DB_HOST="localhost"
    # RAG_DB_PORT="5433"
    # RAG_DB_NAME="noah_mvp_dev"
    # RAG_DB_USER="noah_user"
    # RAG_DB_PASSWORD="noah_password"

    # For Cloud SQL Connector (if connecting to Cloud SQL instance from local dev)
    # CLOUD_SQL_INSTANCE_CONNECTION_NAME="YOUR_PROJECT:YOUR_REGION:YOUR_INSTANCE_NAME"
    # RAG_DB_USER="your_cloud_sql_user" # Stored in Secret Manager for deployed app
    # RAG_DB_PASSWORD="your_cloud_sql_password" # Stored in Secret Manager for deployed app
    # RAG_DB_NAME="your_cloud_sql_db_name"

    # Vertex AI Configuration (usually handled by ADC, but region can be specified)
    VERTEX_AI_REGION="us-central1" # Or your project's region
    VERTEX_AI_LLM_MODEL_NAME="gemini-pro" # Or the specific MedGemma endpoint name

    # Add other environment-specific variables as needed
    ```
    **Important:** For deployed environments (like Cloud Run), these configurations will be set as service environment variables, often referencing values from Secret Manager.

## 3. Dependency Management with Poetry

*   **Install dependencies:** `poetry install` (also installs dev dependencies)
*   **Add a new dependency:** `poetry add <package_name>`
*   **Add a new dev dependency:** `poetry add --group dev <package_name>`
*   **Update dependencies:** `poetry update`
*   **Run commands within Poetry's virtual environment:** `poetry run <command>` (e.g., `poetry run python myscript.py`)

## 4. Common Development Tasks (Makefile)

The `Makefile` in the project root provides shortcuts for common tasks. Run `make help` to see all available commands.

*   **`make setup`**: Runs the initial dependency installation and pre-commit hook setup.
*   **`make lint`**: Checks the codebase for style issues and potential errors using Ruff.
*   **`make format`**: Formats all Python code using Ruff (which applies Black-compatible styling).
*   **`make test`**: Runs all backend unit and integration tests using Pytest (located in `backend/tests/`).
*   **`make run_dev_server`**: Starts the FastAPI backend development server using Uvicorn. The server will typically be available at `http://localhost:8000` and will auto-reload on code changes.
*   **`make build_docker`**: Builds the Docker image for the backend application using `backend/Dockerfile`.
*   **`make clean`**: Removes temporary build artifacts, caches, and virtual environment.

## 5. Coding Standards & Quality

*   **Linting & Formatting:** We use `Ruff` for both linting and formatting (configured to be Black-compatible). Pre-commit hooks are set up to automatically lint and format staged files before each commit. Ensure you run `make setup` or `poetry run pre-commit install` once to enable them.
*   **Type Hinting:** Python type hints are expected for all function and method signatures and variable declarations where appropriate.
*   **Docstrings:** All modules, classes, functions, and methods should have comprehensive Google Style Python docstrings.
*   **Workspace Rules:** The `noah_workspace_rules.json` file (in the project root) provides a conceptual set of rules and preferences that an AI IDE (like "Jules") might use for guidance. Please ensure this file is updated to reflect the definitive `coding-standards.md_vCurrent` and `project-structure.md_vCurrent` for the project.
*   **Modularity:** Code should be highly modular, with clear separation of concerns.

## 6. Testing

*   Tests are written using `Pytest`.
*   Backend tests are located in the `backend/tests/` directory, further organized into `unit/` and `integration/`.
*   Run tests using `make test` or `poetry run pytest backend/tests/`.
*   Aim for good test coverage, especially for critical business logic and API endpoints.

## 7. Project Structure Overview (Initial - Will Evolve)

```
Noah.Genesis/
├── backend/                    # Python FastAPI backend application
│   ├── app/                    # Core application code
│   │   ├── api/                # API endpoint routers
│   │   ├── agent/              # LangGraph agent logic, tools, memory
│   │   ├── models/             # Pydantic models (API, DB)
│   │   ├── services/           # Business logic services (LLM, RAG, DB)
│   │   └── main.py             # FastAPI app instantiation
│   ├── tests/                  # Pytest tests for the backend
│   │   ├── unit/
│   │   └── integration/
│   └── Dockerfile              # Dockerfile for backend service
├── frontend/                   # React+TypeScript frontend application (Phase 2)
│   ├── public/
│   ├── src/
│   └── ...
├── terraform/                  # Terraform configurations for GCP infrastructure
│   ├── project_iam.tf
│   ├── networking.tf
│   ├── secrets.tf
│   ├── monitoring_logging.tf
│   └── ... (other .tf and .md files)
├── scripts/                    # Utility and setup scripts
│   ├── setup_dev_env.sh
│   └── git_initial_commit.sh   # (To be generated in Task 4.3)
├── .env.example                # Example environment file (gitignored .env is used locally)
├── .gitignore
├── .pre-commit-config.yaml
├── DEVELOPMENT.md              # This file
├── Makefile
├── noah_workspace_rules.json   # Conceptual AI IDE workspace rules
├── pyproject.toml              # Poetry dependency management
└── README.md                   # Root project README
```

## 8. Environment Variables & Configuration

*   **Local:** Use a `.env` file in the project root. This is loaded by `python-dotenv`.
*   **Cloud (e.g., Cloud Run):** Environment variables are set directly in the service configuration, often populated from values stored securely in Google Cloud Secret Manager. Application code should be written to read configuration from environment variables regardless of the environment. Pydantic's `BaseSettings` can be very useful for this.

Happy coding!
