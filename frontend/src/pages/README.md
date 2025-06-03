# Frontend Pages (`frontend/src/pages/`)

This directory contains the top-level React components that correspond to different views or routes in the Project Noah MVP application. Pages typically orchestrate data fetching for their view and compose various UI components.

## Core Application Pages

### 1. `LoginPage.tsx`

*   **Route:** `/login`
*   **Purpose:** Provides the interface for user authentication (Sign In) and new user registration (Sign Up).
*   **Key Features & UX (`dynamous.ai` Contributions):**
    *   Uses Mantine UI components (`Paper`, `TextInput`, `PasswordInput`, `Button`, `Alert`, `LoadingOverlay`) for a clean and professional form.
    *   Supports both Email/Password authentication and "Sign in with Google" using Firebase Authentication.
    *   Employs Mantine `useForm` with Zod for robust client-side validation of email and password fields.
    *   Clearly distinguishes between Sign In and Sign Up modes, with an easy toggle (`Anchor` link).
    *   Displays informative error messages for invalid input or authentication failures using Mantine `Alert` and `Notifications`.
    *   Shows loading states during authentication attempts.
    *   Redirects authenticated users away from the login page (e.g., to `/chat`).
    *   [Visual Placeholder: A centered form with application logo/name, input fields for email/password, toggle for Sign Up including confirm password and display name, and a prominent "Sign in with Google" button.]
*   **Primary Child Components:** None (directly uses Mantine components).
*   **Data Flow & Services:**
    *   Interacts with `firebaseService.ts` for `signInWithEmailAndPassword`, `createUserWithEmailAndPassword`, and `signInWithPopup` (Google).
    *   Uses `AuthContext` (via `useAuth` hook) to check current authentication state and trigger updates upon successful login/registration.

### 2. `ChatPage.tsx`

*   **Route:** `/chat` (and default `/` for authenticated users), also `/chat/:sessionId`
*   **Purpose:** The main page for users to interact with the Noah.AI agent. Displays AI-generated summaries and allows quick data logging.
*   **Key Features:**
    *   Primarily houses the `ChatInterface.tsx` component, passing necessary props like `currentUserId` and `initialSessionId`.
    *   Manages `sessionId` state, either from URL parameter (`:sessionId`) or by generating a new one (`uuidv4`).
    *   Integrates a `PatientSummaryDisplay.tsx` component within an `Accordion` section. Includes placeholder logic (`handleFetchPatientSummary`) to simulate fetching and displaying summary content, along with loading and error states.
    *   Provides a "Log Patient Data" button that opens a `PatientDataLogModal` for quick data entry without leaving the chat context.
    *   The layout uses Mantine `Accordion` to organize chat, summaries, and potentially other tools.
*   **Primary Child Components:** `ChatInterface.tsx`, `PatientSummaryDisplay.tsx`, `PatientDataLogModal.tsx`.
*   **Data Flow & Services:**
    *   Relies on `ChatInterface.tsx` to handle chat message API calls via `chatApiService.ts`.
    *   Uses `AuthContext` to ensure user is authenticated.
    *   Placeholder summary interaction (no actual API calls for summary in Task 2.2).
    *   Modal interaction for `PatientDataForm` via `PatientDataLogModal`.

### 3. `UserProfilePage.tsx`

*   **Route:** `/profile/:userId` (e.g., `/profile/me` or `/profile/<firebase_uid>`)
*   **Purpose:** Allows users to view and (if their own profile) edit their profile information.
*   **Key Features:**
    *   Fetches user profile data based on the `userId` route parameter (resolving 'me' to current user's UID) using `getUserProfile` from `userProfileApiService.ts`.
    *   Displays user profile information using the `UserProfileForm.tsx` component.
    *   Manages loading and error states during data fetching, providing feedback via `Alerts` and `Notifications`.
    *   Uses Mantine `Breadcrumbs` for navigation context and `ThemeIcon` for visual appeal.
*   **Primary Child Components:** `UserProfileForm.tsx`.
*   **Data Flow & Services:**
    *   Uses `AuthContext` for current user details.
    *   Fetches data using `getUserProfile` from `userProfileApiService.ts`.
    *   Updates are handled by `UserProfileForm` which calls `updateUserProfile` from `userProfileApiService.ts`.

### 4. `PatientDataLogPage.tsx`

*   **Route:** `/patient-data/log` (Example, final route TBD)
*   **Purpose:** Provides a dedicated page for users to submit patient data logs. This offers an alternative to logging data via the modal available in the main layout or `ChatPage`.
*   **Key Features:**
    *   Embeds the `PatientDataForm.tsx` component.
    *   The page context would ideally determine `targetPatientUserId` (e.g., for a patient, it's their own UID; for a nurse, it might involve selecting a patient from a list, though for MVP, it defaults to the current user's UID passed to the form).
    *   Styled with Mantine `Container`, `Paper`, `Title` for a clear and focused presentation.
*   **Primary Child Components:** `PatientDataForm.tsx`.
*   **Data Flow & Services:**
    *   Relies on `PatientDataForm.tsx` to handle form state and submission using `patientDataApiService.ts`.
    *   Uses `AuthContext` to identify the logged-in user (who is creating the log entry - `created_by_user_id`).

## Utility Pages

### 1. `SettingsPage.tsx` (Placeholder)

*   **Route:** `/settings`
*   **Purpose:** A placeholder for future application settings.
*   **Features (MVP):** Displays a simple message indicating its placeholder status. (Assumed to exist from previous tasks or to be created simply).

### 2. `NotFoundPage.tsx` (Placeholder)

*   **Route:** `*` (fallback for any undefined routes)
*   **Purpose:** Provides a user-friendly "404 Page Not Found" message.
*   **Features:** Displays an error message and a button/link to navigate back to the home page. Styled with Mantine components for a consistent look. (Assumed to exist or be created simply).

This page structure provides the necessary views for the core MVP functionality, focusing on clear navigation and encapsulation of features within their respective pages.
