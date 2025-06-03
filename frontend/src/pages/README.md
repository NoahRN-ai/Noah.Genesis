# Frontend Pages Documentation

This document provides an overview of the key page components in the Noah-AI frontend application. Pages are typically responsible for orchestrating data flow between services and child components, and correspond to specific application routes.

## Core Application Pages

### `ChatPage.tsx`

-   **Purpose**: Serves as the central hub for user interaction with the AI agent. It facilitates real-time chat, displays relevant patient summaries, and provides access to log new patient data via a modal.
-   **Route Example**: `/chat` or `/` (as the main landing page post-login).
-   **Primary Child Components**:
    -   `ChatInterface.tsx`: Handles the direct chat message display and input.
    -   `PatientSummaryDisplay.tsx`: Shows patient-related summaries in a sidebar.
    -   `PatientDataLogModal.tsx`: A modal component that embeds `PatientDataForm.tsx` for logging new data.
-   **Data Flow Overview**:
    -   Manages the overall layout for the chat, summary display, and data logging access.
    -   `ChatInterface` handles its own state for messages and interaction with the chat service.
    -   The "Log Patient Data" button on this page triggers the `PatientDataLogModal`.
    -   Authentication state (`currentUser`) is checked to ensure the user is logged in.
    -   Initializes a `sessionId` for chat interactions.
    -   Potentially handles page-level errors or notifications.

### `LoginPage.tsx`

-   **Purpose**: Provides the interface for user authentication. It allows users to sign in to the application, typically using Firebase authentication.
-   **Route Example**: `/login`
-   **Primary Child Components**:
    -   Likely contains Mantine form components (`TextInput` for email/password, `Button` for submission) or a dedicated login form component if abstracted (e.g., `LoginForm.tsx` - not explicitly created yet, but typical).
    -   May display UI elements for "Sign in with Google" or other OAuth providers.
-   **Data Flow Overview**:
    -   Captures user credentials (email, password) or OAuth provider choice.
    -   Interacts with an authentication service (e.g., methods from `useAuth()` hook which wraps Firebase auth) to sign the user in.
    -   Handles loading states during the authentication process.
    -   Displays error messages if authentication fails.
    -   Redirects the user to a different page (e.g., `ChatPage`) upon successful authentication.
    -   Redirects already authenticated users away from the login page if they try to access it.

### `UserProfilePage.tsx`

-   **Purpose**: Allows users to view and edit their own profile information.
-   **Route Example**: `/profile/:userId` (e.g., `/profile/user123`)
-   **Primary Child Components**:
    -   `UserProfileForm.tsx`: The form component responsible for displaying and handling edits to user profile data.
-   **Data Flow Overview**:
    -   Extracts `userId` from the route parameters (currently mocked).
    -   Passes the `userId` to `UserProfileForm.tsx`.
    -   `UserProfileForm.tsx` then handles fetching the user's current profile data based on the `userId` and submitting any updates.
    -   The page itself is a container for the form, providing context like a page title.

### `PatientDataLogPage.tsx`

-   **Purpose**: Offers a dedicated, full-page interface for logging new patient data. This might be used when a more focused data entry experience is needed compared to the modal on `ChatPage`.
-   **Route Example**: `/patient-data/log` or `/patient/:patientId/log`
-   **Primary Child Components**:
    -   `PatientDataForm.tsx`: The core form used for inputting patient data.
-   **Data Flow Overview**:
    -   Acts as a container for the `PatientDataForm`.
    -   Passes a `patientId` (currently mocked as "patient-123") to the `PatientDataForm`.
    -   The `PatientDataForm` component manages its own state and submission logic.
    -   The page provides a clear title and focused environment for the data logging task.

## Utility Pages

### `NotFoundPage.tsx`

-   **Purpose**: Displays a user-friendly message when a user navigates to a route that does not exist within the application.
-   **Route Example**: Any route not explicitly defined (e.g., `/this-page-does-not-exist`).
-   **Primary Child Components**:
    -   Typically simple Mantine components like `Container`, `Title`, `Text`, and a `Button` to navigate back to a safe page (e.g., the homepage).
-   **Data Flow Overview**:
    -   This page is usually rendered by the routing setup when no other route matches. It's self-contained and doesn't typically involve complex data flows.
