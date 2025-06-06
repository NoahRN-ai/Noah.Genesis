terraform {
  required_version = ">= 1.12.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  # Credentials will be sourced from the environment
  # (e.g., gcloud auth application-default login, or GOOGLE_APPLICATION_CREDENTIALS)
}

# ------------------------------------------------------------------------------
# Project Creation
# ------------------------------------------------------------------------------
resource "google_project" "noah_mvp_project" {
  project_id      = var.gcp_project_id
  name            = var.gcp_project_name
  org_id          = var.gcp_org_id
  billing_account = var.gcp_billing_account
}

# ------------------------------------------------------------------------------
# Enable Necessary APIs
# ------------------------------------------------------------------------------
resource "google_project_service" "project_apis" {
  project = google_project.noah_mvp_project.project_id
  for_each = toset([
    "cloudresourcemanager.googleapis.com", # Project Management
    "serviceusage.googleapis.com",         # Service Management (enabling other APIs)
    "iam.googleapis.com",                  # IAM
    "run.googleapis.com",                  # Cloud Run
    "aiplatform.googleapis.com",           # Vertex AI (LLMs, Embeddings, Vector Search)
    "firestore.googleapis.com",            # Firestore
    "storage-component.googleapis.com",    # Cloud Storage
    "speech.googleapis.com",               # Cloud Speech-to-Text
    "secretmanager.googleapis.com",        # Secret Manager (for Task 0.3)
    "logging.googleapis.com",              # Cloud Logging (for Task 0.4)
    "monitoring.googleapis.com",           # Cloud Monitoring (for Task 0.4)
    "cloudbilling.googleapis.com",         # Billing (needed for project to be billable)
    "identitytoolkit.googleapis.com"       # Identity Platform (for user authentication)
  ])
  service                    = each.key
  disable_dependent_services = false
  disable_on_destroy         = false # Set to true if you want APIs disabled when project is destroyed via TF
}

# ------------------------------------------------------------------------------
# Service Accounts
# Reference: TA_Noah_MVP_v1.1 for service interaction patterns
# ------------------------------------------------------------------------------

# Service Account for the AI Agent Backend on Cloud Run
resource "google_service_account" "sa_cloudrun_agent" {
  project      = google_project.noah_mvp_project.project_id
  account_id   = "sa-noah-cloudrun-agent"
  display_name = "Noah MVP AI Agent Cloud Run Service Account"
  description  = "Identity for the AI Agent backend service running on Cloud Run."
}

# Service Account for the Web Application Frontend on Cloud Run
# This SA might have minimal GCP permissions if frontend primarily uses user auth token for backend calls.
resource "google_service_account" "sa_cloudrun_webapp" {
  project      = google_project.noah_mvp_project.project_id
  account_id   = "sa-noah-cloudrun-webapp"
  display_name = "Noah MVP WebApp Cloud Run Service Account"
  description  = "Identity for the Web Application frontend service running on Cloud Run."
}

# Service Account for RAG Pipeline scripts (data processing, embedding generation)
resource "google_service_account" "sa_rag_pipeline" {
  project      = google_project.noah_mvp_project.project_id
  account_id   = "sa-noah-rag-pipeline"
  display_name = "Noah MVP RAG Pipeline Service Account"
  description  = "Identity for scripts managing the RAG knowledge base ingestion and embedding."
}

# ------------------------------------------------------------------------------
# IAM Bindings for Service Accounts (Least Privilege)
# Roles are granted on the project. More granular, resource-specific IAM can be
# configured later once those resources (e.g., specific buckets, secrets) are defined.
# ------------------------------------------------------------------------------

# Permissions for sa-cloudrun-agent
resource "google_project_iam_member" "sa_cloudrun_agent_vertex_user" {
  project = google_project.noah_mvp_project.project_id
  role    = "roles/aiplatform.user" # To invoke Vertex AI LLMs, Embeddings, Vector Search
  member  = "serviceAccount:${google_service_account.sa_cloudrun_agent.email}"
}

resource "google_project_iam_member" "sa_cloudrun_agent_firestore_user" {
  project = google_project.noah_mvp_project.project_id
  role    = "roles/datastore.user" # To read/write from/to Firestore
  member  = "serviceAccount:${google_service_account.sa_cloudrun_agent.email}"
}

resource "google_project_iam_member" "sa_cloudrun_agent_storage_object_viewer" {
  project = google_project.noah_mvp_project.project_id
  role    = "roles/storage.objectViewer" # To read RAG documents from GCS
  member  = "serviceAccount:${google_service_account.sa_cloudrun_agent.email}"
}

resource "google_project_iam_member" "sa_cloudrun_agent_secret_accessor" {
  project = google_project.noah_mvp_project.project_id
  role    = "roles/secretmanager.secretAccessor" # To access secrets
  member  = "serviceAccount:${google_service_account.sa_cloudrun_agent.email}"
}

resource "google_project_iam_member" "sa_cloudrun_agent_log_writer" {
  project = google_project.noah_mvp_project.project_id
  role    = "roles/logging.logWriter" # To write logs
  member  = "serviceAccount:${google_service_account.sa_cloudrun_agent.email}"
}

resource "google_project_iam_member" "sa_cloudrun_agent_monitoring_writer" {
  project = google_project.noah_mvp_project.project_id
  role    = "roles/monitoring.metricWriter" # To write metrics
  member  = "serviceAccount:${google_service_account.sa_cloudrun_agent.email}"
}

resource "google_project_iam_member" "sa_cloudrun_agent_speech_user" {
  project = google_project.noah_mvp_project.project_id
  role    = "roles/cloudspeech.user" # To use Speech-to-Text API
  member  = "serviceAccount:${google_service_account.sa_cloudrun_agent.email}"
}

# Permissions for sa-cloudrun-webapp (Minimal)
resource "google_project_iam_member" "sa_cloudrun_webapp_log_writer" {
  project = google_project.noah_mvp_project.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.sa_cloudrun_webapp.email}"
}

resource "google_project_iam_member" "sa_cloudrun_webapp_monitoring_writer" {
  project = google_project.noah_mvp_project.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.sa_cloudrun_webapp.email}"
}

# Permissions for sa-rag-pipeline
resource "google_project_iam_member" "sa_rag_pipeline_storage_object_viewer" {
  project = google_project.noah_mvp_project.project_id
  role    = "roles/storage.objectViewer" # To read source RAG documents from GCS
  member  = "serviceAccount:${google_service_account.sa_rag_pipeline.email}"
}
# Note: If RAG pipeline also WRITES to GCS (e.g. processed chunks), add roles/storage.objectCreator or Admin

resource "google_project_iam_member" "sa_rag_pipeline_vertex_user" {
  project = google_project.noah_mvp_project.project_id
  role    = "roles/aiplatform.user" # To use Vertex AI Embedding API
  member  = "serviceAccount:${google_service_account.sa_rag_pipeline.email}"
}
# Note: DB permissions for sa-rag-pipeline (e.g. Cloud SQL user for PostgreSQL+pgvector)
# will need to be granted when the database resource is defined in a later task.

resource "google_project_iam_member" "sa_rag_pipeline_log_writer" {
  project = google_project.noah_mvp_project.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.sa_rag_pipeline.email}"
}

# ------------------------------------------------------------------------------
# IAM Bindings for AEM Developers/Admins
# ------------------------------------------------------------------------------
# Developer Group
resource "google_project_iam_member" "aem_developer_group_project_permissions" {
  count   = var.aem_developer_group_email != null ? 1 : 0
  project = google_project.noah_mvp_project.project_id
  role    = "roles/editor" # Provides broad development access.
  member  = "group:${var.aem_developer_group_email}"
}

resource "google_project_iam_member" "aem_developer_group_iam_admin" {
  count   = var.aem_developer_group_email != null ? 1 : 0
  project = google_project.noah_mvp_project.project_id
  role    = "roles/resourcemanager.projectIamAdmin" # Allows managing IAM policies for the project.
  member  = "group:${var.aem_developer_group_email}"
}

# Individual Developer User (example, can be primary admin)
resource "google_project_iam_member" "aem_developer_user_project_permissions" {
  count   = var.aem_developer_user_email != null ? 1 : 0
  project = google_project.noah_mvp_project.project_id
  role    = "roles/owner" # Or "roles/editor" + "roles/resourcemanager.projectIamAdmin" for finer control
  member  = "user:${var.aem_developer_user_email}"
}
