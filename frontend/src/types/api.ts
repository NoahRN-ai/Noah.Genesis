```typescript
// Matches backend/app/models/api_models.py and firestore_models.py where appropriate

// --- General ---
export interface UserInfo { // This is what AuthContext will store about the Firebase User
  uid: string; // Firebase UID, crucial for linking to our backend UserProfile.user_id
  email?: string | null;
  displayName?: string | null;
  photoURL?: string | null;
  emailVerified: boolean;
  // Add other Firebase User properties if needed by the frontend directly
}

// --- Chat API ---
export interface ChatRequestPayload {
  user_query_text: string;
  user_voice_input_bytes?: string; // Base64 encoded string if sending bytes
  session_id?: string | null;
  mode?: string; // Add new mode field
}

export interface ChatResponsePayload {
  agent_response_text: string;
  session_id: string;
  interaction_id: string;
}

// --- History API ---
export interface ToolCallData {
  name: string;
  args: Record<string, any>;
  id: string;
}

export interface ToolResponseData {
  tool_call_id: string;
  name: string;
  content: any;
}

export interface InteractionOutputData {
  interaction_id: string;
  session_id: string;
  user_id: string; // This should map to Firebase UserInfo.uid
  timestamp: string; // ISO datetime string
  actor: 'user' | 'agent';
  message_content: string;
  tool_calls?: ToolCallData[] | null;
  tool_responses?: ToolResponseData[] | null;
}

export interface SessionHistoryResponsePayload {
  session_id: string;
  interactions: InteractionOutputData[];
}

// --- UserProfile API (from backend) ---
export type UserRole = 'nurse' | 'patient';

export interface UserProfileData { // Data fetched from /users/{uid}/profile
  user_id: string; // This is our backend's user_id, which should match Firebase UID
  role: UserRole;
  display_name?: string | null;
  preferences: Record<string, any>;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface UserProfileUpdatePayload {
  role?: UserRole | null; // Role might not be user-editable
  display_name?: string | null;
  preferences?: Record<string, any> | null;
}

// --- PatientDataLog API ---
export type PatientDataLogDataType =
  | "observation"
  | "symptom_report"
  | "llm_summary"
  | "nursing_note_draft"
  | "shift_handoff_draft"
  | "user_document";

export interface PatientDataLogCreatePayload {
  // target_patient_user_id is a query param in the backend API
  timestamp: string; // ISO datetime string
  data_type: PatientDataLogDataType;
  content: Record<string, any>;
  source?: string | null;
}

export interface PatientDataLogData { // Data fetched from /patient-data-logs
  log_id: string;
  user_id: string; // Patient owner UID
  created_by_user_id: string; // Submitter UID
  timestamp: string; // ISO datetime string for the event
  data_type: PatientDataLogDataType;
  content: Record<string, any>;
  source: string;
  created_at: string; // ISO datetime string for record creation
  updated_at: string; // ISO datetime string for record update
}

// --- For Chat Interface Component ---
// Used by ChatInterface component to structure message display
export interface DisplayMessage {
  id: string; // interaction_id from backend, or a client-generated ID for local user messages/system messages
  text: string;
  sender: 'user' | 'agent' | 'system'; // 'system' for status messages like 'typing' or client-side errors
  timestamp: Date | string; // Store as Date for easier client-side formatting, or string if directly from API
  isTyping?: boolean; // True if this is an "agent is typing" visual indicator, not a real message
  isError?: boolean; // Flag if this message represents an error to display differently
  tool_calls?: ToolCallData[] | null; // Store for potential future display if needed
  // If message content contains markdown, the ChatMessage component will handle rendering
}
```
