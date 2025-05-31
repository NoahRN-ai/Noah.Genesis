.PHONY: help lint format test run_dev_server build_docker clean setup

# Default Python interpreter for local tasks can be set via `poetry run`
PYTHON = poetry run python
POETRY = poetry

# Variables
APP_MODULE = backend.app.main:app
DOCKER_IMAGE_BACKEND = noah-mvp-backend:latest
DOCKERFILE_BACKEND = backend/Dockerfile

help:
	@echo "Available commands:"
	@echo "  setup          : Install dependencies and setup pre-commit hooks."
	@echo "  lint           : Check code for style and errors with Ruff."
	@echo "  format         : Format code with Ruff (using Black style)."
	@echo "  test           : Run backend tests with Pytest."
	@echo "  run_dev_server : Run the FastAPI backend development server with Uvicorn."
	@echo "  build_docker   : Build the Docker image for the backend application."
	@echo "  clean          : Remove build artifacts and cache."

setup:
	@echo "Installing dependencies with Poetry..."
	$(POETRY) install --no-root
	@echo "Installing pre-commit hooks..."
	$(POETRY) run pre-commit install
	@echo "Setup complete. Please ensure you have a .env file configured for local development."
	@echo "Run 'gcloud auth application-default login' if you haven't already."

lint:
	@echo "Running Ruff linter and type checker..."
	$(POETRY) run ruff check .
	$(POETRY) run ruff format --check .

format:
	@echo "Formatting code with Ruff..."
	$(POETRY) run ruff format .
	$(POETRY) run ruff check . --fix

test:
	@echo "Running backend tests with Pytest..."
	$(POETRY) run pytest backend/tests/

run_dev_server:
	@echo "Starting FastAPI backend development server on http://0.0.0.0:8000 ..."
	@echo "Ensure your .env file is configured."
	$(POETRY) run uvicorn $(APP_MODULE) --reload --host 0.0.0.0 --port 8000

build_docker:
	@echo "Building Docker image for backend: $(DOCKER_IMAGE_BACKEND)..."
	docker build -t $(DOCKER_IMAGE_BACKEND) -f $(DOCKERFILE_BACKEND) .

clean:
	@echo "Cleaning up build artifacts and cache..."
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info .venv
