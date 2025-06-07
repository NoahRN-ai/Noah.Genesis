# Frontend Components (`frontend/src/components/`)

This directory contains reusable React components for the Project Noah MVP frontend.

## Core Interaction Components

### 1. `ChatInterface.tsx`

*   **Purpose:** Provides the main user interface for real-time chat interactions with the Noah.AI agent.
*   **Key Features & UX (`dynamous.ai` Contributions):**
    *   **Message Display:**
        *   Renders a scrollable list of messages (`DisplayMessage[]`).
        *   Visually differentiates between 'user', 'agent', and 'system' messages using distinct styling (alignment, background colors from `noahTheme`, avatar placeholders). Achieves clarity and intuitive turn-taking recognition.
        *   Displays human-readable timestamps for each message using `date-fns`.
        *   Supports basic Markdown rendering for agent messages (bold, italics, lists, code blocks) via `react-markdown` and `remark-gfm` for enhanced readability of potentially complex AI responses.
        *   Includes an "agent is typing" visual indicator (`isTyping` flag in `DisplayMessage`) for better user feedback during agent processing.
        *   [Visual Placeholder: User message bubble - right-aligned, primary color. Agent message bubble - left-aligned, neutral professional color. System message bubble - centered, subtle.]
    *   **Text Input Area:**
        *   Uses a Mantine `Textarea` component that `autosize`s for comfortable multi-line input.
        *   Includes a clear "Send" `ActionIcon` (`IconSend`).
        *   Supports keyboard submission: `Enter` to send, `Shift+Enter` for a new line within the textarea.
        *   Contains a placeholder `ActionIcon` for "Voice Input" (`IconMicrophone`), signaling future capability as per MVP feature set while keeping current implementation focused.
    *   **Agent Status & Error Handling:**
        *   System messages can be used to display errors directly in the chat flow (e.g., if an API call fails).
        *   Uses Mantine `Notifications` for more global or persistent error/success feedback from form submissions or critical API failures.
        *   Loading state (`isSending`) disables input and changes Send button appearance to provide clear feedback.
*   **State Management:** Primarily uses local React state (`useState`) for `messages`, `inputValue`, `isSending`, `currentSessionId`.
*   **Interactions & Services:**
    *   On message send, it optimistically updates the UI with the user's message.
    *   Calls `sendChatMessage` from `chatApiService.ts` to send the user's query and current `session_id` to the backend.
    *   Updates the UI with the agent's response or any error received.
    *   Initializes with a `currentUserId` and an `initialSessionId` passed from the parent page (`ChatPage`). Session ID is managed and passed with subsequent API calls.
*   **`dynamous.ai` UX Patterns Applied:**
    *   **Standard Chat Layout:** Familiar message list + input bar.
    *   **Clear Affordances:** Obvious send button, typing indicator.
    *   **Responsive Feedback:** Optimistic UI updates, loading states.
    *   **Markdown for Readability:** Enhances presentation of agent's text.
    *   **Minimalist Design:** Leverages Mantine for a clean, uncluttered, professional aesthetic suitable for clinical context.

### 2. `UserProfileForm.tsx`

*   **Purpose:** Provides a form for users to view and update their profile information (display name, preferences).
*   **Key Features & UX (`dynamous.ai` Contributions):**
    *   Uses Mantine `useForm` with Zod schema (`userProfileFormSchema`) for robust validation.
    *   Displays `user_id`, `email`, and `role` as read-only fields for informational purposes.
    *   Allows editing of `displayName`.
    *   Implements MVP preferences using Mantine `Select` (e.g., "LLM Summary Length") and `Switch` (e.g., "Enable Email Notifications"), providing a user-friendly alternative to raw JSON editing for preferences. This pattern simplifies preference management for non-technical users.
    *   Handles form submission, calling `updateUserProfile` from `userProfileApiService.ts`.
    *   Displays loading states and provides clear success/error feedback using Mantine `Notifications` and inline `Alerts`.
    *   Editability is controlled by an `isOwnProfile` prop.
*   **Props:**
    *   `initialProfileData: UserProfileData | null`
    *   `onProfileUpdate?: (updatedProfile: UserProfileData) => void`
    *   `isLoadingData: boolean`
    *   `isOwnProfile: boolean`
*   **Interactions & Services:** Fetches initial data via parent page, submits updates using `userProfileApiService.ts`.

### 3. `PatientDataForm.tsx`

*   **Purpose:** Provides a form (intended for use in a Modal or dedicated page) for users (patients or nurses) to log patient-specific data.
*   **Key Features & UX (`dynamous.ai` Contributions):**
    *   Uses Mantine `useForm` for validation (inline validation function).
    *   Includes Mantine `DateTimePicker` for event `timestamp`, `Select` for `data_type` (from `PatientDataLogDataType` enum), and `TextInput` for `source`.
    *   **Conditional Content Fields:** Dynamically shows relevant input fields based on the selected `data_type`. This is a key `dynamous.ai` UX recommendation to reduce cognitive load and tailor the form to the specific logging task (e.g., shows "Observation Notes" Textarea if `data_type` is "OBSERVATION", or "Symptom Description" and "Severity" Select if "SYMPTOM_REPORT"). Also supports `LLM_SUMMARY`, `USER_DOCUMENT`, `NURSING_NOTE_DRAFT`, `SHIFT_HANDOFF_DRAFT`.
    *   Handles form submission, constructing the `content` object appropriately, and calling `submitPatientDataLog` from `patientDataApiService.ts`.
    *   Provides clear loading states and success/error feedback via Mantine `Notifications`.
*   **Props:**
    *   `targetPatientUserId: string` (UID of the patient the log is for)
    *   `onSubmitSuccess?: () => void` (e.g., to close a modal)
    *   `onCancel?: () => void`
*   **Interactions & Services:** Submits data using `patientDataApiService.ts`.

### 4. `PatientSummaryDisplay.tsx` (UI Placeholder)

*   **Purpose:** A designated UI section to display patient summaries generated by Noah.AI (backend Task 3.3).
*   **Key Features (MVP Placeholder - Task 2.2):**
    *   Displays passed `summaryContent`, `isLoading`, or `error` states.
    *   Includes a placeholder for a refresh/regenerate action (via `onRefresh` prop, though not actively used in current ChatPage example).
    *   Styled using Mantine `Paper` and `Text` for clear readability.
    *   Shows appropriate messages for loading, error, or no content states.
    *   [Visual Placeholder: A titled section, possibly within an Accordion on ChatPage, showing formatted text of the AI-generated summary, or a message indicating "No summary available" or "Loading summary..."]
*   **Props:**
    *   `summaryContent?: string | null`
    *   `isLoading?: boolean`
    *   `error?: string | null`
    *   `onRefresh?: () => void`
*   **Interactions & Services:** For Task 2.2, it only displays props. Actual data fetching/triggering logic will be implemented by its parent component (e.g., `ChatPage`) in conjunction with backend services from Phase 3.

### 5. `PatientDataLogModal.tsx`

*   **Purpose:** Provides a reusable Mantine `Modal` wrapper for the `PatientDataForm.tsx` component.
*   **Key Features:**
    *   Accepts `opened`, `onClose`, and `patientId` props.
    *   Renders the `PatientDataForm` within the modal, passing the `patientId` and wiring up `onSubmitSuccess` and `onCancel` to close the modal.
    *   Provides a consistent title and styling for the data logging modal.
*   **Props:**
    *   `opened: boolean`
    *   `onClose: () => void`
    *   `patientId: string`
*   **Interactions & Services:** Facilitates the use of `PatientDataForm` in a modal context. Relies on `PatientDataForm` for actual data submission.

## Common Utility Components

### 1. `Layout.tsx` (actually `AppLayout.tsx` in `components/common/Layout.tsx`)

*   **Purpose:** Provides the main application shell using Mantine `AppShell`.
*   **Key Features:**
    *   Includes a responsive Header with the application title/logo placeholder and conditional Sign In/User actions.
    *   Includes a responsive Navbar (for authenticated users) with navigation links (`NavLink`) to key pages (Chat, Profile) and a Sign Out button.
    *   Manages the mobile navigation burger menu state (`opened`).
    *   Integrates a color scheme toggle (Light/Dark mode) using `useMantineColorScheme`.
    *   Provides a consistent layout structure for all authenticated pages.
    *   **Patient Data Logging Modal Integration:**
        *   Includes a `NavLink` in the Navbar ("Log Patient Data") that triggers a Mantine `Modal`.
        *   The Modal embeds the `PatientDataForm` component, allowing users to log data from anywhere in the app.
        *   Uses `useDisclosure` hook for managing modal state.
        *   Displays user's email and UID in the Navbar footer.
*   **Props:** `children: React.ReactNode`

### 2. `ProtectedRoute.tsx` (`components/common/ProtectedRoute.tsx`)

*   **Purpose:** A route wrapper component that checks user authentication status via `AuthContext` (`useAuth` hook).
*   **Key Features:**
    *   If the user is authenticated (`currentUser` exists and `isInitialized` is true), it renders the child routes (`<Outlet />`).
    *   If the user is not authenticated after initialization, it redirects to the `/login` page, preserving the originally intended location for redirection after login.
    *   Displays a global loading indicator (`Loader`) while the authentication state is being initialized (`authLoading` or `!isInitialized`).

This structure and component set provides a foundation for a user-friendly and functional MVP frontend. The `dynamous.ai` emphasis on clear UX patterns, Mantine UI's strengths, and adherence to Logos Accord principles (clarity, conciseness) are integrated into their design.
