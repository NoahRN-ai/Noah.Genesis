# GCP Project & IAM Configuration Details (terraform/project_iam.tf)

This document provides details on the Google Cloud Project creation and the Identity and Access Management (IAM) configurations defined in `terraform/project_iam.tf` for Project Noah MVP V1.0.

## 1. GCP Project (`google_project.noah_mvp_project`)

*   **Purpose:** Establishes the foundational GCP project for all Noah.Genesis MVP resources.
*   **Key Configurations:**
    *   `project_id`: User-defined, globally unique ID (from `var.gcp_project_id`).
    *   `name`: User-defined display name (from `var.gcp_project_name`).
    *   `org_id`: Associates the project with the specified Google Cloud Organization (from `var.gcp_org_id`).
    *   `billing_account`: Links the project to the specified billing account (from `var.gcp_billing_account`).
*   **Enabled APIs (`google_project_service.project_apis`):**
    *   `cloudresourcemanager.googleapis.com`: For project management.
    *   `serviceusage.googleapis.com`: For managing service enablement.
    *   `iam.googleapis.com`: For IAM policy management.
    *   `run.googleapis.com`: For Cloud Run services (AI Agent Backend, WebApp Frontend).
    *   `aiplatform.googleapis.com`: For Vertex AI (LLMs, Embeddings, Vector Search).
    *   `firestore.googleapis.com`: For Firestore database.
    *   `storage-component.googleapis.com`: For Cloud Storage.
    *   `speech.googleapis.com`: For Cloud Speech-to-Text.
    *   `secretmanager.googleapis.com`: For Google Cloud Secret Manager.
    *   `logging.googleapis.com`: For Cloud Logging.
    *   `monitoring.googleapis.com`: For Cloud Monitoring.
    *   `cloudbilling.googleapis.com`: For billing linkage and management.
    *   `identitytoolkit.googleapis.com`: For GCP Identity Platform (user authentication).
    *   **Rationale:** APIs are enabled based on the services defined in `TA_Noah_MVP_v1.1` and anticipated foundational needs (logging, monitoring, secrets) for the MVP.

## 2. Service Accounts

Service accounts are created to provide specific identities for different application components, adhering to the principle of least privilege.

### 2.1. AI Agent Cloud Run Service Account (`google_service_account.sa_cloudrun_agent`)

*   **ID:** `sa-noah-cloudrun-agent`
*   **Display Name:** `Noah MVP AI Agent Cloud Run Service Account`
*   **Purpose:** Provides the identity for the backend AI agent application running on Google Cloud Run. This application will handle core logic, LLM interactions, RAG, and data persistence.
*   **Assigned Roles & Rationale:**
    *   `roles/aiplatform.user`: To allow the agent to interact with Vertex AI services (e.g., invoke LLM models like MedGemma/Gemini, generate embeddings, query Vector Search). Essential for AI capabilities.
    *   `roles/datastore.user`: To grant full read/write access to Firestore database (for `UserProfile`, `PatientDataLog`, `InteractionHistory`). Essential for data persistence.
    *   `roles/storage.objectViewer`: To allow reading objects from Cloud Storage buckets. Primarily for accessing curated knowledge documents for the RAG system.
    *   `roles/secretmanager.secretAccessor`: To securely access secrets (e.g., API keys, sensitive configurations) stored in Secret Manager. Critical for security.
    *   `roles/logging.logWriter`: To write application logs to Cloud Logging. Essential for observability and debugging.
    *   `roles/monitoring.metricWriter`: To publish custom metrics to Cloud Monitoring. Important for performance monitoring and alerting.
    *   `roles/cloudspeech.user`: To use the Google Cloud Speech-to-Text API for transcribing voice inputs (primarily from nurses as per `TA_Noah_MVP_v1.1`).

### 2.2. WebApp Cloud Run Service Account (`google_service_account.sa_cloudrun_webapp`)

*   **ID:** `sa-noah-cloudrun-webapp`
*   **Display Name:** `Noah MVP WebApp Cloud Run Service Account`
*   **Purpose:** Provides the identity for the frontend web application (React+TypeScript) if it's hosted on Google Cloud Run and requires an SA for its execution environment. The frontend primarily interacts with the backend via user-authenticated API calls.
*   **Assigned Roles & Rationale:**
    *   `roles/logging.logWriter`: To write any server-side logs (if applicable for the Cloud Run hosting environment) to Cloud Logging.
    *   `roles/monitoring.metricWriter`: To publish metrics related to the Cloud Run service instance to Cloud Monitoring.
    *   **Note:** This service account has minimal permissions as the frontend application (React) is expected to make authenticated calls to the backend AI Agent service using the end-user's identity (via Identity Platform), rather than the Cloud Run service's own identity for accessing GCP resources.

### 2.3. RAG Pipeline Service Account (`google_service_account.sa_rag_pipeline`)

*   **ID:** `sa-noah-rag-pipeline`
*   **Display Name:** `Noah MVP RAG Pipeline Service Account`
*   **Purpose:** Provides the identity for offline scripts/processes responsible for building and maintaining the Retrieval Augmented Generation (RAG) knowledge base. This includes loading documents, chunking text, generating embeddings, and populating the vector database.
*   **Assigned Roles & Rationale:**
    *   `roles/storage.objectViewer`: To read source documents (e.g., PDFs, markdown files containing clinical information) from a designated Cloud Storage bucket.
    *   `roles/aiplatform.user`: To utilize Vertex AI Embedding APIs for generating vector embeddings from text chunks.
    *   `roles/logging.logWriter`: To write logs from the pipeline scripts to Cloud Logging.
    *   **Note on Database Permissions:** Permissions to write to the vector database (e.g., Cloud SQL for PostgreSQL with pgvector, or Vertex AI Vector Search indexing) will be granted when those specific database resources are defined and configured in subsequent Terraform scripts (e.g., `database.tf`).

## 3. AEM Developer IAM Roles

Access for AI Engineering Module (AEM) developers/administrators is configured to allow management and development of the project.

*   **Target:** `var.aem_developer_group_email` (Google Group) and/or `var.aem_developer_user_email` (individual user).
*   **Assigned Roles & Rationale:**
    *   **Group (`var.aem_developer_group_email`):**
        *   `roles/editor`: Provides broad permissions to view and modify most project resources, suitable for a development team.
        *   `roles/resourcemanager.projectIamAdmin`: Allows members of the group to manage IAM policies within this project, facilitating self-service access management for the team.
    *   **Individual User (`var.aem_developer_user_email`):**
        *   `roles/owner`: (Example for a primary admin/user) Provides full control over the project, including billing and IAM. Alternatively, a combination of `roles/editor` and `roles/resourcemanager.projectIamAdmin` can provide strong administrative capabilities with slightly more restricted billing/org policy impact.

## 4. `dynamous.ai` Contributions & HIPAA Considerations

The IAM configuration for Project Noah MVP has been influenced by `dynamous.ai` principles with a strong focus on:

*   **Least Privilege:** Service accounts are granted only the permissions essential for their designated tasks, minimizing potential impact if a service account were compromised.
*   **Separation of Duties:** Different service accounts are used for distinct components (backend, webapp, RAG pipeline), preventing overly broad access.
*   **Security by Default:** Proactively enabling necessary APIs and providing placeholders for secure secret access aligns with secure software development practices.
*   **Auditability & Clarity:** Documenting the purpose and rationale for each service account and its permissions supports security reviews and compliance efforts (e.g., for HIPAA).
*   **HIPAA Alignment:**
    *   The entire setup assumes a **Business Associate Addendum (BAA) with Google Cloud is in place** for this project.
    *   The principle of least privilege directly supports HIPAA's technical safeguards regarding access control.
    *   Careful consideration of roles ensures that service accounts interacting with potential PHI (e.g., `sa-cloudrun-agent` accessing Firestore) have appropriate, but not excessive, permissions.
    *   Enabling APIs for logging and monitoring is crucial for audit trails, another HIPAA requirement.

This initial IAM setup provides a secure and functional foundation for the Project Noah MVP. Permissions will be further refined and scoped to specific resources as those resources are provisioned in subsequent tasks.
