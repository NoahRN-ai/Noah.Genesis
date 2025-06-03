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
  preferences: Record<string, any>; // Example: { summaryLength: 'concise', notifications: { email: true } }
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface UserProfileUpdatePayload {
  role?: UserRole | null; // Role might not be user-editable
  display_name?: string | null;
  preferences?: Record<string, any> | null;
}

// --- PatientDataLog API ---
// Updated to match the exact values from the backend `PatientDataLogDataType`
export enum PatientDataLogDataType {
  OBSERVATION = "observation",
  SYMPTOM_REPORT = "symptom_report",
  LLM_SUMMARY = "llm_summary",
  NURSING_NOTE_DRAFT = "nursing_note_draft",
  SHIFT_HANDOFF_DRAFT = "shift_handoff_draft",
  USER_DOCUMENT = "user_document",
  // Add other data types as they are defined in the backend enum
}

export interface PatientDataLogCreatePayload {
  // target_patient_user_id is a query param in the backend API /patient-data-logs/{target_patient_user_id}
  timestamp: string; // ISO datetime string of the event/observation
  data_type: PatientDataLogDataType;
  content: Record<string, any>; // Flexible content based on data_type
  source?: string | null; // e.g., "Manual Entry", "Device X", "Patient Self-Report"
}

export interface PatientDataLogData { // Data fetched from /patient-data-logs
  log_id: string;
  user_id: string; // Patient owner UID (the one for whom data is logged)
  created_by_user_id: string; // Submitter UID (who actually created the log)
  timestamp: string; // ISO datetime string for the event
  data_type: PatientDataLogDataType;
  content: Record<string, any>;
  source: string; // Defaulted if not provided
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
}

// No new specific *API data contract* types are strictly required for this chunk,
// but ensure existing ones are comprehensive enough for form bindings.

// Example of a more structured 'content' field for PatientDataLog for different types,
// if we wanted to type it strongly on the frontend (backend uses Dict[str, Any]).
// This is more for frontend form structure than a strict API contract if backend is flexible.
// For now, we'll handle flexible content in the form component directly.
/*
export interface ObservationContent {
  vitals_notes?: string;
  blood_pressure?: string;
  heart_rate?: number;
  temperature?: number;
  // ... other common vitals
}

export interface SymptomReportContent {
  description: string;
  severity?: 'mild' | 'moderate' | 'severe';
  onset_datetime?: string; // ISO
}
*/
