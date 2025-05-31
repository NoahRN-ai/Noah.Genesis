#!/bin/bash
#
# Script to set up the development environment for Project Noah MVP
#
# This script will:
# 1. Check for and guide Poetry installation.
# 2. Install project dependencies using Poetry.
# 3. Install pre-commit hooks.
# 4. Guide on GCP local authentication.
# 5. (Optional) Provide commands to pull Docker images for local databases.

set -e # Exit immediately if a command exits with a non-zero status.

echo "--- Starting Project Noah MVP Development Environment Setup ---"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Check/Install Poetry
echo ""
echo "Step 1: Checking for Poetry..."
if command_exists poetry; then
    echo "Poetry is already installed."
    poetry --version
else
    echo "Poetry not found."
    echo "Please install Poetry by following the instructions at: https://python-poetry.org/docs/#installation"
    echo "After installing Poetry, re-run this script."
    exit 1
fi

# 2. Install project dependencies
echo ""
echo "Step 2: Installing project dependencies using Poetry..."
poetry install --no-root
echo "Dependencies installed successfully."

# 3. Install pre-commit hooks
echo ""
echo "Step 3: Installing pre-commit hooks..."
poetry run pre-commit install
echo "Pre-commit hooks installed successfully."

# 4. GCP Local Authentication
echo ""
echo "Step 4: GCP Local Authentication"
echo "Please ensure you have the Google Cloud SDK (gcloud CLI) installed."
echo "If not, install it from: https://cloud.google.com/sdk/docs/install"
echo ""
echo "To authenticate for local development (Application Default Credentials):"
echo "Run the following command and follow the prompts:"
echo "  gcloud auth application-default login"
echo ""
echo "Make sure to select the GCP project (e.g., YOUR_GCP_PROJECT_ID_HERE once created) if prompted, or configure it via:"
echo "  gcloud config set project YOUR_GCP_PROJECT_ID_HERE"

# 5. (Optional) Local Docker Databases
echo ""
echo "Step 5: (Optional) Local Docker Databases for RAG development"
echo "For local development of the RAG pipeline (Task 1.4), you might want a local PostgreSQL instance with the pgvector extension."
echo "If you have Docker installed, you can use a pre-built image. Example using ankane/pgvector:"
echo ""
echo "  docker pull ankane/pgvector"
echo "  docker run --name noah-pgvector-dev -e POSTGRES_USER=noah_user -e POSTGRES_PASSWORD=noah_password -e POSTGRES_DB=noah_mvp_dev -p 5433:5432 -d ankane/pgvector"
echo ""
echo "  (Using port 5433 to avoid conflict if you have a local Postgres on 5432 already)"
echo "  Your local DATABASE_URL for .env might then be: postgresql+psycopg2://noah_user:noah_password@localhost:5433/noah_mvp_dev"
echo ""
echo "Alternatively, for Ollama (if exploring local LLMs for non-core tasks, not part of MVP spec):"
echo "  docker pull ollama/ollama"
echo "  docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama"
echo "  (Then pull models like 'docker exec ollama ollama pull llama2')"
echo "This is purely optional and not required for the core MVP which uses Vertex AI."

echo ""
echo "--- Development Environment Setup Script Finished ---"
echo "Next steps:"
echo "1. Ensure you have run 'gcloud auth application-default login'."
echo "2. Create a '.env' file in the project root for local environment variables (see DEVELOPMENT.md)."
echo "3. You can now use 'make' commands (e.g., 'make lint', 'make test', 'make run_dev_server')."
