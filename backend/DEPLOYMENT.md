# Deploying the Project Noah MVP Backend

This document provides instructions for deploying the Project Noah MVP backend service using Google Cloud Build and Google Cloud Run, based on the `backend/cloudbuild.yaml` configuration.

## 1. Prerequisites

Before deploying, ensure the following prerequisites are met:

*   **Google Cloud Platform (GCP) Project:**
    *   A GCP project is set up with billing enabled.
    *   The following APIs are enabled:
        *   Cloud Build API
        *   Cloud Run API
        *   Artifact Registry API
        *   Secret Manager API
        *   Vertex AI API
        *   Firestore API
        *   IAM API
*   **IAM Permissions:**
    *   **Deployer Identity (User or Service Account running `gcloud builds submit`):**
        *   `Cloud Build Editor` role (or permissions to submit builds).
        *   `Service Account User` on the Cloud Build service account (if different from default).
    *   **Cloud Build Service Account (`service-<PROJECT_NUMBER>@gcp-sa-cloudbuild.iam.gserviceaccount.com`):**
        *   `Cloud Run Admin`: To deploy and manage Cloud Run services.
        *   `Service Account User`: To act as (set) the runtime service account for the Cloud Run service.
        *   `Artifact Registry Writer`: To push Docker images to Artifact Registry.
        *   `Secret Manager Secret Accessor`: To access secrets for environment variables.
    *   **Cloud Run Runtime Service Account (specified by `_SERVICE_ACCOUNT_EMAIL` in `cloudbuild.yaml`):**
        *   `Firestore User`: To read/write to Firestore.
        *   `Vertex AI User`: To interact with Vertex AI LLMs and Vector Search.
        *   `Storage Object Viewer`: If RAG GCS bucket contains non-public data.
        *   (If using ADC for Firebase Admin) Permissions to verify Firebase ID tokens and potentially access user claims. This might be covered by a role like `Firebase Admin SDK Administrator Service Agent` or more granular permissions.
*   **Terraform Outputs (Recommended):**
    *   If using Terraform to provision infrastructure (Secrets, Artifact Registry, Service Accounts, etc.), have the outputs available, as these will provide values for some of the build substitutions.
*   **`.gcloudignore` File:**
    *   Ensure a `.gcloudignore` file exists in the project root to prevent unnecessary files from being uploaded as build context (e.g., `.git/`, `node_modules/`, `frontend/build/`). This speeds up context upload. Example:
        ```
        .gcloudignore
        .git
        .gitignore
        node_modules
        frontend/node_modules
        frontend/dist
        __pycache__
        *.pyc
        *.log
        .DS_Store
        # Add other files/directories to ignore during context upload
        ```

## 2. Build Substitutions

The `cloudbuild.yaml` file uses substitutions for configuration. These must be provided when triggering the build.

| Substitution Key                  | Description                                                                                                | Example Value                                                                      | Source                                           |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------ |
| `_GCP_PROJECT_ID`                 | Your Google Cloud Project ID.                                                                              | `my-noah-project-12345`                                                            | GCP Project                                      |
| `_ARTIFACT_REGISTRY_REGION`       | Region for your Artifact Registry (e.g., `us-central1`).                                                   | `us-central1`                                                                      | Your choice, e.g., same as Cloud Run region      |
| `_ARTIFACT_REGISTRY_REPOSITORY`   | Name of your Artifact Registry repository.                                                                 | `noah-mvp-backend-repo`                                                            | Your choice (created via GCP Console or Terraform) |
| `_CLOUD_RUN_SERVICE_NAME`         | Name for your Cloud Run service.                                                                           | `noah-mvp-agent-service`                                                           | Your choice                                      |
| `_CLOUD_RUN_REGION`               | Region for your Cloud Run service (e.g., `us-central1`).                                                   | `us-central1`                                                                      | Your choice                                      |
| `_SERVICE_ACCOUNT_EMAIL`          | Email of the Service Account the Cloud Run service will run as.                                            | `sa-noah-cloudrun-agent@my-noah-project-12345.iam.gserviceaccount.com`            | Created via GCP Console or Terraform             |
| `_VPC_CONNECTOR_NAME` (Optional)  | Full name of VPC connector if Cloud Run needs to access private resources.                                 | `projects/my-noah-project-12345/locations/us-central1/connectors/my-vpc-connector` | Created via GCP Console or Terraform             |
| `_VPC_EGRESS_SETTING` (Optional)  | VPC egress setting (`all-traffic` or `private-ranges-only`).                                               | `private-ranges-only`                                                              | If using VPC Connector                           |

## 3. Deployment Steps

1.  **Navigate to the project root directory** (the directory containing this `backend` folder and the main `pyproject.toml`).
2.  **Submit the build to Google Cloud Build:**
    ```bash
    gcloud builds submit --config backend/cloudbuild.yaml \
      --substitutions=\
    _GCP_PROJECT_ID="YOUR_PROJECT_ID",\
    _ARTIFACT_REGISTRY_REGION="YOUR_AR_REGION",\
    _ARTIFACT_REGISTRY_REPOSITORY="YOUR_AR_REPO_NAME",\
    _CLOUD_RUN_SERVICE_NAME="noah-mvp-agent-service",\
    _CLOUD_RUN_REGION="YOUR_CR_REGION",\
    _SERVICE_ACCOUNT_EMAIL="YOUR_CR_RUNTIME_SA_EMAIL" \
      . # The final dot specifies the build context (project root)
    ```
    *   Replace placeholder values (e.g., `YOUR_PROJECT_ID`) with your actual configuration.
    *   The `COMMIT_SHA` is automatically used for Docker image tagging.

## 4. Environment Variables & Secrets

The Cloud Run service is configured with environment variables in `cloudbuild.yaml`. Sensitive values are sourced from Google Secret Manager.

*   **Direct Environment Variables:**
    *   `GCP_PROJECT_ID`: Set to the build substitution `_GCP_PROJECT_ID`.
    *   `VERTEX_AI_REGION`: Set to the build substitution `_CLOUD_RUN_REGION`.
    *   `DEFAULT_LLM_MODEL_NAME`: Example: `gemini-1.0-pro-001`.
    *   `LOG_LEVEL`: Example: `INFO`.
*   **Secrets from Secret Manager (via `--update-secrets`):**
    *   The `cloudbuild.yaml` references secrets like `RAG_GCS_BUCKET_NAME=noah-rag-gcs-bucket-name:latest`.
    *   Ensure secrets with these names (e.g., `noah-rag-gcs-bucket-name`) exist in Secret Manager in your GCP project.
    *   The value of these secrets should be the actual configuration data (e.g., the GCS bucket name string).
    *   The Cloud Build service account needs the "Secret Manager Secret Accessor" role on these secrets.

### Firebase Admin SDK Initialization Strategy

The application's `backend/app/core/security.py` initializes Firebase Admin SDK. Choose **one** of the following methods:

1.  **Recommended: Application Default Credentials (ADC)**
    *   Ensure the Cloud Run runtime Service Account (`_SERVICE_ACCOUNT_EMAIL`) has the necessary IAM permissions on your Firebase project to authenticate requests (e.g., verify ID tokens). This often involves roles like "Firebase Admin SDK Administrator Service Agent" or more granular permissions if preferred.
    *   **Do not** set the `FIREBASE_SERVICE_ACCOUNT_JSON_PATH` environment variable in `cloudbuild.yaml` (i.e., keep the related `--update-secrets` line commented out or remove it). The application will automatically use ADC.

2.  **Service Account Key File via Secret Manager:**
    *   If you must use a specific service account JSON key:
        1.  Store the **content** of your Firebase service account JSON key file as a secret in Secret Manager (e.g., named `noah-firebase-sa-json`).
        2.  In `cloudbuild.yaml`, uncomment and use the line:
            `--update-secrets=FIREBASE_SERVICE_ACCOUNT_JSON_PATH=noah-firebase-sa-json:latest`
        3.  **Important:** The `cloudbuild.yaml` deployment step will mount this secret as a file. The application needs to know the *path* to this file. The mounted path will be `/run/secrets/noah-firebase-sa-json`. So, if you use this method, the `FIREBASE_SERVICE_ACCOUNT_JSON_PATH` value passed to Cloud Run should literally be this path string.
            *   This means you would modify the `--update-secrets` line for `FIREBASE_SERVICE_ACCOUNT_JSON_PATH` to actually set an *environment variable* with this path, not mount the secret *as* the path.
            *   Example: `--set-env-vars=FIREBASE_SERVICE_ACCOUNT_JSON_PATH="/run/secrets/noah-firebase-sa-json" --update-secrets=noah-firebase-sa-json=noah-firebase-sa-json:latest` (This syntax for setting an env var whose value is a secret path might need careful handling in `cloudbuild.yaml` or be set directly on the Cloud Run service post-deploy if complex).
            *   Alternatively, modify `core/security.py` to directly read the content from the mounted secret file path if `FIREBASE_SERVICE_ACCOUNT_JSON_PATH_CONTENT` env var (containing the secret name) is set. Using ADC is generally simpler.

## 5. Security Considerations

*   **Cloud Run Authentication:**
    *   **CRITICAL:** The `cloudbuild.yaml` currently specifies `--allow-unauthenticated` for the Cloud Run service. For any application handling PHI, this is **NOT recommended, even for an MVP.**
    *   **Action Required:** Change this to `--no-allow-unauthenticated`.
    *   Configure IAM for the Cloud Run service to only allow invocations from authenticated principals (e.g., your frontend's service account, specific user groups, or other authorized backend services). Refer to GCP documentation for "Securing Cloud Run services".
*   **Least Privilege:** Ensure all service accounts (Cloud Build SA, Cloud Run Runtime SA) have only the minimum necessary permissions.

## 6. Post-Deployment Verification

1.  **Check Cloud Build Logs:** Ensure the build and deployment steps in Cloud Build complete successfully.
2.  **Get Cloud Run Service URL:**
    *   Find your service in the Google Cloud Console (Cloud Run section).
    *   Or use `gcloud run services describe YOUR_SERVICE_NAME --region YOUR_REGION --format 'value(status.url)'`.
3.  **Test API Endpoints:**
    *   Use a tool like `curl` or Postman to make test requests to your deployed API endpoints.
    *   Remember to provide a valid Firebase ID token in the `Authorization: Bearer <TOKEN>` header.
    *   Example (replace placeholders):
        ```bash
        TOKEN="YOUR_FIREBASE_ID_TOKEN"
        SERVICE_URL="YOUR_CLOUD_RUN_SERVICE_URL"
        curl -H "Authorization: Bearer $TOKEN" "$SERVICE_URL/api/v1/user_profiles/YOUR_USER_ID/profile"
        ```
4.  **Check Cloud Run Logs:** Monitor logs in Google Cloud Logging for your Cloud Run service to ensure it's running correctly and to troubleshoot any issues.

## 7. Updating the Service

To update the service with new code:
1.  Commit your changes to your Git repository.
2.  Re-run the `gcloud builds submit...` command. Cloud Build will use the latest `COMMIT_SHA` to tag the new Docker image and deploy a new revision to Cloud Run.
```
