# ------------------------------------------------------------------------------
# Google Cloud Secret Manager Configuration for Project Noah MVP
#
# Note: The Secret Manager API (secretmanager.googleapis.com) is assumed to be
# enabled via project_iam.tf (Task 0.1).
#
# These definitions create secret "containers". The actual secret values
# MUST be added manually by engineers through the GCP Console or gcloud CLI
# after these resources are provisioned by Terraform.
# ------------------------------------------------------------------------------

# Secret for RAG System (PostgreSQL) Database User
resource "google_secret_manager_secret" "noah_rag_db_user" {
  project   = google_project.noah_mvp_project.project_id
  secret_id = "noah-rag-db-user"

  replication {
    automatic = true # Simple replication for MVP
  }

  labels = {
    "environment" = "mvp"
    "app"         = "noah-genesis"
    "purpose"     = "rag-db-credentials"
  }
}

# Secret for RAG System (PostgreSQL) Database Password
resource "google_secret_manager_secret" "noah_rag_db_password" {
  project   = google_project.noah_mvp_project.project_id
  secret_id = "noah-rag-db-password"

  replication {
    automatic = true
  }

  labels = {
    "environment" = "mvp"
    "app"         = "noah-genesis"
    "purpose"     = "rag-db-credentials"
  }
}

# Add an initial placeholder version to noah_rag_db_password.
# This ensures the secret has a version and can be readily accessed/tested.
# The actual value MUST be updated manually.
resource "google_secret_manager_secret_version" "noah_rag_db_password_initial_version" {
  secret      = google_secret_manager_secret.noah_rag_db_password.id
  secret_data = "SET_MANUALLY_IN_GCP_CONSOLE_OR_VIA_GCLOUD"
  # enabled     = true # Defaults to true
}

# Secret for a generic application configuration key (e.g., Fernet key for symmetric encryption)
resource "google_secret_manager_secret" "noah_app_generic_config_key" {
  project   = google_project.noah_mvp_project.project_id
  secret_id = "noah-app-generic-config-key"

  replication {
    automatic = true
  }

  labels = {
    "environment" = "mvp"
    "app"         = "noah-genesis"
    "purpose"     = "application-configuration"
  }
}

/*
# Optional: Placeholder for a third-party LLM API Key, if ever needed.
# For Vertex AI (MedGemma/Gemini), authentication is typically via Service Accounts.
resource "google_secret_manager_secret" "noah_llm_third_party_api_key" {
  project   = google_project.noah_mvp_project.project_id
  secret_id = "noah-llm-third-party-api-key"

  replication {
    automatic = true
  }

  labels = {
    "environment" = "mvp"
    "app"         = "noah-genesis"
    "purpose"     = "external-llm-api-key"
  }
}
*/

# ------------------------------------------------------------------------------
# IAM Permissions for Service Accounts to Access Secrets
# Grants the 'Secret Manager Secret Accessor' role, allowing to read secret values.
# ------------------------------------------------------------------------------

# sa-cloudrun-agent needs access to RAG DB credentials and generic app key
resource "google_secret_manager_secret_iam_member" "sa_cloudrun_agent_access_rag_db_user" {
  project   = google_secret_manager_secret.noah_rag_db_user.project
  secret_id = google_secret_manager_secret.noah_rag_db_user.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.sa_cloudrun_agent.email}"
}

resource "google_secret_manager_secret_iam_member" "sa_cloudrun_agent_access_rag_db_password" {
  project    = google_secret_manager_secret.noah_rag_db_password.project
  secret_id  = google_secret_manager_secret.noah_rag_db_password.secret_id
  role       = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.sa_cloudrun_agent.email}"
  depends_on = [google_secret_manager_secret_version.noah_rag_db_password_initial_version] # Ensure secret version exists before IAM
}

resource "google_secret_manager_secret_iam_member" "sa_cloudrun_agent_access_app_generic_key" {
  project   = google_secret_manager_secret.noah_app_generic_config_key.project
  secret_id = google_secret_manager_secret.noah_app_generic_config_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.sa_cloudrun_agent.email}"
}

/*
# Grant access to optional third-party LLM API key if it were active
resource "google_secret_manager_secret_iam_member" "sa_cloudrun_agent_access_llm_third_party_key" {
  project   = google_secret_manager_secret.noah_llm_third_party_api_key.project
  secret_id = google_secret_manager_secret.noah_llm_third_party_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.sa_cloudrun_agent.email}"
}
*/

# sa-rag-pipeline needs access to RAG DB credentials
resource "google_secret_manager_secret_iam_member" "sa_rag_pipeline_access_rag_db_user" {
  project   = google_secret_manager_secret.noah_rag_db_user.project
  secret_id = google_secret_manager_secret.noah_rag_db_user.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.sa_rag_pipeline.email}"
}

resource "google_secret_manager_secret_iam_member" "sa_rag_pipeline_access_rag_db_password" {
  project    = google_secret_manager_secret.noah_rag_db_password.project
  secret_id  = google_secret_manager_secret.noah_rag_db_password.secret_id
  role       = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.sa_rag_pipeline.email}"
  depends_on = [google_secret_manager_secret_version.noah_rag_db_password_initial_version] # Ensure secret version exists
}
