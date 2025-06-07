# Frontend Deployment Guide (Project Noah MVP)

This guide outlines the steps to build and deploy the Project Noah MVP frontend application (React + Vite) to Firebase Hosting. It covers manual deployment for testing and automated deployment using Google Cloud Build for CI/CD.

## 1. Prerequisites

Before you begin, ensure you have the following:

* **Firebase Project:** A Firebase project linked to your Google Cloud Project. If you haven't created one, do so via the [Firebase Console](https://console.firebase.google.com/).
* **Node.js and Package Manager:** Node.js (version specified in `cloudbuild.yaml`, e.g., 20) and `pnpm` (or your project's chosen package manager like npm/yarn) installed locally.
* **Firebase CLI:** The Firebase Command Line Interface installed globally. If not, install it:
    ```bash
    npm install -g firebase-tools
    ```
* **Google Cloud SDK (gcloud CLI):** Installed and configured for interacting with your Google Cloud project.
* **Source Code:** The `frontend/` directory of the Project Noah MVP repository.

## 2. Initial Firebase Setup (One-Time Manual Configuration)

These steps link your local frontend project to your Firebase project.

1.  **Login to Firebase CLI:**
    Open your terminal and run:
    ```bash
    firebase login
    ```
    Follow the prompts to authenticate with the Google account associated with your Firebase project.

2.  **Initialize Firebase Hosting:**
    Navigate to the `frontend/` directory in your project:
    ```bash
    cd path/to/your/Noah.Genesis/frontend
    ```
    Run the Firebase initialization command for hosting:
    ```bash
    firebase init hosting
    ```
    During the setup:
    * **Select Project:** Choose "Use an existing project" and select your Project Noah Firebase project.
    * **Public Directory:** When prompted "What do you want to use as your public directory?", enter `dist`. (Vite builds static assets to this folder).
    * **Single-Page App:** When asked "Configure as a single-page app (rewrite all urls to /index.html)?", answer `Yes` (or `y`). This is crucial for React Router.
    * **Set up GitHub Action:** For "Set up automatic builds and deploys with GitHub?", choose `No`. We will use Google Cloud Build.

    This process creates/updates `firebase.json` (hosting configuration) and `.firebaserc` (project alias) in your `frontend/` directory.

## 3. Configure Environment Variables for Vite Build

Your React application uses Vite environment variables (prefixed with `VITE_`) for configuration (e.g., Firebase SDK keys, API backend URL).

* **Local Development (`.env.local`):**
    Create a `.env.local` file in your `frontend/` directory (this file **must be in `.gitignore`** and not committed to the repository):
    ```env
    # frontend/.env.local (DO NOT COMMIT - For local development only)
    VITE_FIREBASE_API_KEY="your_local_firebase_web_api_key"
    VITE_FIREBASE_AUTH_DOMAIN="your-local-project-id.firebaseapp.com"
    VITE_FIREBASE_PROJECT_ID="your-local-project-id"
    VITE_FIREBASE_STORAGE_BUCKET="your-local-project-id.appspot.com"
    VITE_FIREBASE_MESSAGING_SENDER_ID="your-local-sender-id"
    VITE_FIREBASE_APP_ID="your-local-app-id"
    VITE_API_BASE_URL="http://localhost:8000/api/v1" # URL for your local backend server
    ```
    Retrieve your Firebase Web SDK configuration values from the Firebase Console: Project settings > General > Your apps > Select your web app > SDK setup and configuration.

* **Production Build (via Cloud Build):**
    For automated production builds, these `VITE_` variables **must be supplied to the `cloudbuild.yaml` build step**. This is typically done using Cloud Build trigger substitutions.
    * The `VITE_API_BASE_URL` must point to your **deployed production backend service URL** (e.g., your Cloud Run service URL).
    * Firebase SDK keys should correspond to your **production Firebase app**.
    Refer to the `cloudbuild.yaml` substitutions section and the Cloud Build Trigger setup instructions below.

## 4. Manual Build & Deploy (for Local Testing and Ad-hoc Deploys)

1.  **Install Dependencies (if not already done):**
    In the `frontend/` directory:
    ```bash
    pnpm install --frozen-lockfile
    ```

2.  **Build the Application for Production:**
    ```bash
    pnpm run build
    ```
    This command compiles your React app and outputs static assets to the `frontend/dist/` directory.

3.  **Deploy to Firebase Hosting Manually:**
    ```bash
    firebase deploy --only hosting -P YOUR_FIREBASE_PROJECT_ID
    ```
    Replace `YOUR_FIREBASE_PROJECT_ID` with your actual Firebase Project ID (or an alias defined in `.firebaserc`). The Firebase CLI will output the URL of your deployed site.

## 5. Automated Deployment with Google Cloud Build (CI/CD)

The `frontend/cloudbuild.yaml` script enables automated builds and deployments to Firebase Hosting when code is pushed to your repository's main branch.

### 5.1. Create and Store Firebase CI Token (One-Time Setup)

Cloud Build needs a Firebase Continuous Integration (CI) token to authenticate for deployments.

1.  **Generate Firebase CI Token:**
    In your local terminal, run:
    ```bash
    firebase login:ci
    ```
    This command will open a browser window. Authenticate with your Google account. After successful authentication, a **token will be printed to your terminal**. Copy this token securely.

2.  **Store the Token in GCP Secret Manager:**
    * In the Google Cloud Console, navigate to **Security > Secret Manager**.
    * Enable the Secret Manager API if it's not already enabled.
    * Click **"Create Secret"**.
        * **Name / Secret ID:** Enter `firebase-deploy-token` (this should match `_FIREBASE_TOKEN_SECRET_ID` in `cloudbuild.yaml`).
        * **Secret value:** Paste the Firebase CI token you copied.
        * **Replication policy:** Leave as "Automatic" unless you have specific regional needs.
    * Click **"Create secret"**.

3.  **Grant Cloud Build Service Account Access to the Secret:**
    Your Cloud Build service account needs permission to access this secret.
    * The Cloud Build service account email format is typically: `[PROJECT_NUMBER]@cloudbuild.gserviceaccount.com`. Find your `PROJECT_NUMBER` in the GCP Console (Dashboard or IAM settings).
    * In Secret Manager, select the `firebase-deploy-token` secret you created.
    * Go to the **"Permissions"** tab (you might need to click "Show info panel" if it's hidden).
    * Click **"Add Principal"**.
        * **New principals:** Enter the full email address of your Cloud Build service account.
        * **Role:** Assign the role **"Secret Manager Secret Accessor"** (`roles/secretmanager.secretAccessor`).
    * Click **"Save"**.

### 5.2. Understanding `frontend/cloudbuild.yaml`

The `frontend/cloudbuild.yaml` script (generated by Jules) automates the following:
1.  Sets up a Node.js environment with `pnpm` and `firebase-tools`.
2.  Installs frontend dependencies using `pnpm install --frozen-lockfile`.
3.  Builds the Vite application using `pnpm run build`. (Vite `VITE_` environment variables are injected at this stage from Cloud Build substitutions).
4.  Retrieves the Firebase deployment token securely from Secret Manager.
5.  Deploys the contents of `frontend/dist/` to Firebase Hosting.

### 5.3. Set Up Google Cloud Build Trigger

Create a trigger to automatically run the `cloudbuild.yaml` pipeline.

1.  In the Google Cloud Console, navigate to **Cloud Build > Triggers**.
2.  Click **"Create trigger"**.
3.  **Name:** e.g., `deploy-frontend-main`
4.  **Description:** (Optional) e.g., "Deploy frontend to Firebase Hosting on push to main branch"
5.  **Event:** Select "Push to a branch".
6.  **Source Repository:**
    * Select your source code repository (e.g., GitHub). If you haven't connected it yet, click "Connect new repository" and follow the instructions.
    * Choose your Project Noah repository.
7.  **Branch (regex):** Enter `^main$` (or your primary deployment branch name, e.g., `^master$`).
8.  **Configuration:**
    * **Type:** Cloud Build configuration file (yaml or json).
    * **Location:** Repository.
    * **Cloud Build configuration file location:** `frontend/cloudbuild.yaml` (ensure this path is correct relative to your repository root).
9.  **Advanced (Substitution variables):** This is a **CRITICAL** step.
    * Click **"Add variable"** for each substitution required by `cloudbuild.yaml`.
    * Default substitutions like `_GCP_PROJECT_ID` and `_FIREBASE_PROJECT_ID` might be pre-filled or inferred, but verify them.
    * `_FIREBASE_TOKEN_SECRET_ID`: (Default in YAML is `firebase-deploy-token`).
    * `_FIREBASE_TOKEN_SECRET_VERSION`: (Default in YAML is `latest`).
    * `_NODE_VERSION`: (Default in YAML is `20`).
    * **Vite Environment Variables:** Add all necessary `VITE_` variables required for your production build. **These will override any `.env` files during the Cloud Build process.**
        * `_VITE_API_BASE_URL`: Set this to your **deployed production backend URL**.
        * `_VITE_FIREBASE_API_KEY`: Your production Firebase API Key.
        * `_VITE_FIREBASE_AUTH_DOMAIN`: Your production Firebase Auth Domain.
        * `_VITE_FIREBASE_PROJECT_ID_CONFIG`: Your production Firebase Project ID (for the app config).
        * `_VITE_FIREBASE_STORAGE_BUCKET`: Your production Firebase Storage Bucket.
        * `_VITE_FIREBASE_MESSAGING_SENDER_ID`: Your production Firebase Messaging Sender ID.
        * `_VITE_FIREBASE_APP_ID`: Your production Firebase App ID.
10. Click **"Create"**.

Now, every push to the specified branch (e.g., `main`) will trigger this Cloud Build pipeline, automatically building and deploying your frontend to Firebase Hosting.

## 6. Custom Domain (Post-MVP Enhancement)

After your application is deployed and thoroughly tested:

1.  Go to the **Firebase Console**.
2.  Navigate to **Hosting** in the left sidebar.
3.  Click **"Add custom domain"**.
4.  Follow the on-screen instructions to:
    * Enter your desired custom domain (e.g., `app.noah-genesis.com`).
    * Verify domain ownership by adding TXT records to your domain's DNS settings.
    * Update your domain's A records (and optionally AAAA records) to point to Firebase Hosting IPs.

Firebase Hosting will automatically provision and renew SSL certificates for your custom domain, providing HTTPS by default.

---

This comprehensive setup ensures a robust, secure, and automated deployment pipeline for the Project Noah MVP frontend, leveraging Firebase Hosting's speed and simplicity with Google Cloud Build's CI/CD capabilities.
