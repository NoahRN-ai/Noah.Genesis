# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.7.1 # Or a recent stable version of Poetry
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VIRTUALENVS_CREATE=false # Disable virtualenv creation inside Docker by Poetry, manage globally
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install Poetry
RUN apt-get update && apt-get install -y --no-install-recommends curl     && curl -sSL https://install.python-poetry.org | python3 -     && apt-get purge -y --auto-remove curl     && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy only dependency definition files first to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install project dependencies using Poetry
# --no-root: do not install the project itself as editable, only its dependencies
# --no-dev: do not install development dependencies like pytest, ruff
RUN poetry install --no-interaction --no-ansi --no-dev --no-root

# Copy the rest of the backend application code into the /app directory
# We are building from the project root, so backend code is in ./backend
COPY ./backend /app/backend
# If other top-level directories are part of the backend package context (e.g. shared libs not in backend/)
# they would need to be copied too. For this project, all backend code is under ./backend.

# Expose the port the app runs on (Cloud Run sets this via PORT env var, usually 8080)
# This EXPOSE is for documentation; Cloud Run uses the PORT env var.
EXPOSE 8080

# Command to run the application using Uvicorn with Poetry
# Cloud Run provides the PORT environment variable.
# If PORT is not set, default to 8080.
# The working directory is /app, and main.py is in backend/app/main.py
# So the module path for uvicorn is backend.app.main:app
CMD ["poetry", "run", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8080}"]
