# GCP Secret Manager Configuration Details (terraform/secrets.tf)

This document outlines the secrets provisioned in Google Cloud Secret Manager for Project Noah MVP V1.0, as defined in `terraform/secrets.tf`. The primary purpose is to securely store and manage sensitive information like database credentials and API keys.

## 1. Overview

Google Cloud Secret Manager provides a centralized and secure way to store API keys, passwords, certificates, and other sensitive data. Terraform is used to create the secret "containers" (placeholders). **Actual secret values are NOT stored in Terraform configuration and MUST be added manually by authorized engineers directly into Secret Manager after these resources are created.**

The Secret Manager API (`secretmanager.googleapis.com`) is enabled as part of the project setup in `project_iam.tf`.

## 2. Defined Secrets Placeholders

The following secrets are provisioned as placeholders:

### 2.1. `noah-rag-db-user`
*   **Terraform Resource:** `google_secret_manager_secret.noah_rag_db_user`
*   **Purpose:** Stores the username for connecting to the RAG system's Cloud SQL for PostgreSQL database (as anticipated in Task 1.4).
*   **Accessed By:**
    *   `sa-cloudrun-agent` (Service Account for AI Agent Backend): If the agent directly queries the RAG DB or uses components that do.
    *   `sa-rag-pipeline` (Service Account for RAG Pipeline Scripts): For writing embeddings and text chunks to the database.
*   **Manual Action:** After Terraform apply, set the actual database username for the RAG PostgreSQL instance in this secret.

### 2.2. `noah-rag-db-password`
*   **Terraform Resource:** `google_secret_manager_secret.noah_rag_db_password`
*   **Initial Placeholder Version:** An initial version with the value "SET_MANUALLY_IN_GCP_CONSOLE_OR_VIA_GCLOUD" is created by Terraform. This MUST be replaced with the actual strong password.
*   **Purpose:** Stores the password for the `noah-rag-db-user` for connecting to the RAG system's Cloud SQL for PostgreSQL database.
*   **Accessed By:**
    *   `sa-cloudrun-agent`
    *   `sa-rag-pipeline`
*   **Manual Action:** After Terraform apply, **immediately update the secret version with the actual strong database password** for the RAG PostgreSQL instance.

### 2.3. `noah-app-generic-config-key`
*   **Terraform Resource:** `google_secret_manager_secret.noah_app_generic_config_key`
*   **Purpose:** A general-purpose secret for application-level configuration that is sensitive but not an external API key or DB credential. Example uses could include a Fernet key for symmetric encryption of certain application data, or a pepper/salt value for hashing if needed.
*   **Accessed By:**
    *   `sa-cloudrun-agent` (if the backend application requires it).
*   **Manual Action:** After Terraform apply, set the actual configuration key value in this secret.

### 2.4. (Optional/Commented Out) `noah-llm-third-party-api-key`
*   **Terraform Resource:** `google_secret_manager_secret.noah_llm_third_party_api_key` (currently commented out in `secrets.tf`)
*   **Purpose:** This was a placeholder in case any third-party LLM services (requiring an API key) were to be used alongside Vertex AI. Project Noah MVP V1.0, as per `TA_Noah_MVP_v1.1` and `STER_MVP_v1_LLM_Assessment v0.1`, primarily uses Google MedGemma or Gemini via Vertex AI, which rely on service account authentication. This secret is therefore not strictly necessary for the current MVP scope.
*   **Accessed By (if active):** `sa-cloudrun-agent`.
*   **Manual Action (if active):** Set the actual third-party API key.

## 3. IAM Permissions for Secret Access

Service accounts are granted the `roles/secretmanager.secretAccessor` IAM role on specific secrets. This role allows them to read the value of the secret but not to modify the secret itself or its IAM policy.

*   **`sa-cloudrun-agent` can access:**
    *   `noah-rag-db-user`
    *   `noah-rag-db-password`
    *   `noah-app-generic-config-key`
*   **`sa-rag-pipeline` can access:**
    *   `noah-rag-db-user`
    *   `noah-rag-db-password`

This adheres to the principle of least privilege, ensuring components can only access the secrets they specifically require.

## 4. CRITICAL: LLMs and Secrets Interaction

**Under no circumstances should Large Language Models (LLMs) or AI Agents be designed to interact directly with secrets stored in Secret Manager or have raw secret values passed into their prompts, configurations, or operational context.**

*   **Human Management:** Secrets are sensitive credentials managed by human engineers.
*   **Secure Access Pattern:** Application code (running under an authorized service account like `sa-cloudrun-agent`) should fetch secret values from Secret Manager at runtime *as needed*. These fetched values should then be used by the application logic to configure clients or authenticate to other services.
*   **No LLM Exposure:** Secret values should **never** be included in prompts sent to LLMs, nor should LLMs be given tools or functions that would allow them to retrieve arbitrary secrets. This is a critical security boundary to prevent accidental exposure or misuse of sensitive credentials.

## 5. `dynamous.ai` Contributions to Secrets Management

*   **Secure by Design:** The approach emphasizes creating placeholders via IaC and mandating manual, secure injection of actual secret values, preventing sensitive data from being stored in version control.
*   **Least Privilege Access:** IAM permissions for secrets are granted on a per-secret, per-service-account basis.
*   **Clarity of Purpose:** Naming conventions and labels for secrets are designed for clarity.
*   **Explicit Warning on LLM Interaction:** Strong guidance on preventing direct LLM interaction with secrets is a key security contribution for AI-driven applications.
*   **Anticipation of Needs:** Provisioning secrets for database credentials based on upcoming RAG system requirements (Task 1.4).
