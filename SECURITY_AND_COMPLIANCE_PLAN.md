# Security and Compliance Plan: Firestore and IAM

This document outlines the security and compliance plan for the application, focusing on Firestore Security Rules and Identity and Access Management (IAM) considerations. This plan is designed with HIPAA compliance in mind, emphasizing patient data privacy and secure access.

## 1. General Principles for Firestore Security Rules

*   **Authentication Required:** All access to Firestore data requires the user to be authenticated via Firebase Authentication. Unauthenticated access is denied by default.
    ```
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
    ```
    *(Note: This is a baseline; specific collection rules will further restrict access.)*
*   **Default Deny:** No access is permitted to any data unless explicitly allowed by a security rule. If no rule matches a request, access is denied.
*   **Principle of Least Privilege:** Users and service accounts are granted only the minimum necessary permissions to perform their functions.

## 2. `noah_mvp_patients` Collection (`/noah_mvp_patients/{patientId}`)

This collection stores `PatientProfile` documents. The `{patientId}` is expected to be the same as the Firebase Auth `uid` for users with the 'patient' role.

### Helper Functions (Conceptual for Firestore Rules)

```
// Assumes custom claim 'role' is set on the Firebase Auth token
function isPatient(role) {
  return role == 'patient';
}

function isNurse(role) {
  return role == 'nurse';
}

// Basic validation for incoming PatientProfile data
function isValidPatientProfileData(data) {
  return data.keys().hasAll(['patient_id', 'active', 'gender', 'created_at', 'updated_at']) &&
         data.patient_id == request.auth.uid && // If patient is creating/updating own
         data.active is bool &&
         data.gender is string &&
         // Further checks for name, telecom, address structures if needed
         // data.birthDate is timestamp (or string if validated)
         data.created_at is timestamp &&
         data.updated_at is timestamp;
}
```

### Security Rules

```
match /noah_mvp_patients/{patientId} {
  // PATIENT Access
  allow read: if request.auth.uid == patientId && isPatient(request.auth.token.role);
  // Patient creation might be restricted to admin/nurse, or allowed on signup
  allow create: if request.auth.uid == patientId &&
                   isPatient(request.auth.token.role) &&
                   isValidPatientProfileData(request.resource.data);
  allow update: if request.auth.uid == patientId &&
                   isPatient(request.auth.token.role) &&
                   isValidPatientProfileData(request.resource.data); // Ensure patient_id is not changed
  allow delete: if false; // Patients cannot delete their profiles

  // NURSE Access
  allow read: if isNurse(request.auth.token.role);
  // Nurses can create profiles for new patients. patientId might not be request.auth.uid here.
  allow create: if isNurse(request.auth.token.role) &&
                   request.resource.data.patient_id == patientId && // Ensure doc ID matches internal ID
                   isValidPatientProfileData(request.resource.data); // Validate all required fields
  allow update: if isNurse(request.auth.token.role) &&
                   isValidPatientProfileData(request.resource.data); // Ensure patient_id is not changed
  // Nurse delete might be allowed under specific conditions or via backend admin functions
  // allow delete: if isNurse(request.auth.token.role) && <specific_conditions>;
}
```

## 3. `noah_mvp_observations` Subcollection (`/noah_mvp_patients/{patientId}/noah_mvp_observations/{observationId}`)

This subcollection stores `Observation` documents related to a specific patient.

### Helper Functions (Conceptual)

```
function isValidObservationData(data, patientId) {
  return data.keys().hasAll(['subject_patient_id', 'status', 'code', 'effectiveDateTime', 'created_at', 'updated_at']) &&
         data.subject_patient_id == patientId && // Critical link
         data.status is string && // Further enum validation if possible
         data.code is map && data.code.text is string &&
         data.effectiveDateTime is timestamp &&
         data.created_at is timestamp &&
         data.updated_at is timestamp;
         // Potentially check performer_user_id == request.auth.uid for nurses
}

function observationFieldsAreUpdatable(data, existingData) {
  // Example: Allow updating status and note, but not core data like code or effectiveDateTime once final.
  return data.keys().hasOnly(['status', 'note', 'updated_at']) ||
         (existingData.status != 'final' && existingData.status != 'amended');
}

function observationCanBeDeleted(existingData) {
  // Example: Only allow deletion if status is 'entered-in-error'
  return existingData.status == 'entered-in-error';
}
```

### Security Rules

```
match /noah_mvp_patients/{patientId}/noah_mvp_observations/{observationId} {
  // PATIENT Access
  allow read: if request.auth.uid == patientId && isPatient(request.auth.token.role);
  // Allow patient to create if self-reporting is enabled
  allow create: if request.auth.uid == patientId &&
                   isPatient(request.auth.token.role) &&
                   isValidObservationData(request.resource.data, patientId);
  // Limited update for patients
  allow update: if request.auth.uid == patientId &&
                   isPatient(request.auth.token.role) &&
                   observationFieldsAreUpdatable(request.resource.data, resource.data);
  allow delete: if false; // Patients generally cannot delete observations

  // NURSE Access
  allow read: if isNurse(request.auth.token.role);
  allow create: if isNurse(request.auth.token.role) &&
                   isValidObservationData(request.resource.data, patientId) &&
                   request.resource.data.performer_user_id.hasAny([request.auth.uid]); // Ensure nurse is a performer
  allow update: if isNurse(request.auth.token.role) &&
                   observationFieldsAreUpdatable(request.resource.data, resource.data);
  allow delete: if isNurse(request.auth.token.role) &&
                   observationCanBeDeleted(resource.data);
}
```

## 4. `noah_mvp_medication_statements` Subcollection (`/noah_mvp_patients/{patientId}/noah_mvp_medication_statements/{statementId}`)

This subcollection stores `MedicationStatement` documents. Rules are analogous to Observations.

### Helper Functions (Conceptual)
```
function isValidMedicationStatementData(data, patientId) {
  return data.keys().hasAll(['subject_patient_id', 'status', 'medicationCodeableConcept', 'created_at', 'updated_at']) &&
         data.subject_patient_id == patientId &&
         data.status is string &&
         data.medicationCodeableConcept is map && data.medicationCodeableConcept.text is string &&
         data.created_at is timestamp &&
         data.updated_at is timestamp;
         // Optionally check informationSource_user_id for nurses
}

function medicationStatementFieldsAreUpdatable(data, existingData) {
  // Example: Allow updating status, notes, or dosage instructions.
  return data.keys().hasOnly(['status', 'note', 'dosage_text', 'dosage_timing_code_text', 'updated_at']) ||
         existingData.status != 'completed'; // Cannot update completed statements easily
}

function medicationStatementCanBeDeleted(existingData) {
  return existingData.status == 'entered-in-error';
}
```

### Security Rules
```
match /noah_mvp_patients/{patientId}/noah_mvp_medication_statements/{statementId} {
  // PATIENT Access
  allow read: if request.auth.uid == patientId && isPatient(request.auth.token.role);
  allow create: if request.auth.uid == patientId &&
                   isPatient(request.auth.token.role) &&
                   isValidMedicationStatementData(request.resource.data, patientId);
  allow update: if request.auth.uid == patientId &&
                   isPatient(request.auth.token.role) &&
                   medicationStatementFieldsAreUpdatable(request.resource.data, resource.data);
  allow delete: if false;

  // NURSE Access
  allow read: if isNurse(request.auth.token.role);
  allow create: if isNurse(request.auth.token.role) &&
                   isValidMedicationStatementData(request.resource.data, patientId) &&
                   (request.resource.data.informationSource_user_id == null || request.resource.data.informationSource_user_id == request.auth.uid);
  allow update: if isNurse(request.auth.token.role) &&
                   medicationStatementFieldsAreUpdatable(request.resource.data, resource.data);
  allow delete: if isNurse(request.auth.token.role) &&
                   medicationStatementCanBeDeleted(resource.data);
}
```

## 5. `ai_contextual_stores` Collection (`/ai_contextual_stores/{patientId}`)

This collection stores `AIContextualStore` documents, keyed by `patientId`.

### Helper Functions (Conceptual)
```
function isValidAIContextualStoreData(data, patientId) {
  return data.patient_id == patientId &&
         data.keys().hasAll(['patient_id', 'created_at', 'updated_at']) && // last_summary etc are optional
         data.created_at is timestamp &&
         data.updated_at is timestamp;
}

// For MVP, nurses might not directly write here; AI processes via backend update this.
// If nurses can trigger actions that update this, specific rules or backend mediation is needed.
// function nurseCanUpdateAIContext(data) { return true; }
```

### Security Rules
```
match /ai_contextual_stores/{patientId} {
  // PATIENT Access (if patients can view/manage their AI settings/summaries directly)
  allow read: if request.auth.uid == patientId && isPatient(request.auth.token.role);
  // Patient write access might be limited to specific fields like 'preferences'
  allow write: if request.auth.uid == patientId &&
                  isPatient(request.auth.token.role) &&
                  isValidAIContextualStoreData(request.resource.data, patientId); // Or more granular field checks

  // NURSE Access
  allow read: if isNurse(request.auth.token.role);
  // Write access for nurses to AI store is complex.
  // For MVP, this is likely read-only for nurses directly via rules.
  // Updates would be performed by the backend service acting on behalf of AI processes or nurse-initiated actions.
  allow write: if false; // Or: if isNurse(request.auth.token.role) && nurseCanUpdateAIContext(request.resource.data);

  // BACKEND SERVICE (Admin/AI Process) - This is typically not done via UID based rules but IAM for service accounts.
  // If a specific function/process needs to write here, it would use admin SDK or a service account.
}
```
*Self-correction: The `write` permission combines `create` and `update`. For more granular control (e.g. patient can create but not arbitrarily update all fields, or vice-versa), separate `allow create` and `allow update` rules would be needed.*

## 6. Data Validation in Firestore Rules

Firestore Security Rules offer capabilities for basic data validation on write operations (`create`, `update`). This includes:
*   **Presence of fields:** `request.resource.data.keys().hasAll(['field1', 'field2'])`
*   **Field types:** `request.resource.data.fieldName is string` or `is bool`, `is number`, `is map`, `is list`, `is timestamp`.
*   **String constraints:** `request.resource.data.fieldName.size() < 100`.
*   **Value constraints:** `request.resource.data.age > 0`.
*   **Immutability of fields:** `request.resource.data.field == resource.data.field` (ensure a field is not changed on update).
*   **Relationship integrity:** Ensuring `subject_patient_id` in a subcollection item matches the parent document's ID (`patientId`).

This server-side validation is crucial as a first line of defense, complementing more complex validation performed by the backend application logic.

## 7. IAM Policies

*   **Backend Service Account:** The backend service (e.g., running on Cloud Run, App Engine, or GKE) must use a dedicated Google Cloud service account.
*   **Principle of Least Privilege:** This service account should be granted the **`Cloud Datastore User`** IAM role (which includes Firestore permissions) for the specific project. For even finer-grained control, custom IAM roles could be considered in the future, but `Cloud Datastore User` is a common starting point for full database access by the backend.
*   **Firebase Admin SDK:** The backend service will typically use the Firebase Admin SDK or Google Cloud Server Client Libraries to interact with Firestore. When initialized with a service account, these SDKs bypass Firestore security rules and operate with the permissions granted to the service account via IAM. This is necessary for administrative actions, complex data transformations, and AI-driven updates that don't fit user-centric security rules.
*   **No End-User Credentials on Backend:** The backend service should never handle or store end-user credentials. It relies on Firebase Authentication to verify user identity (via ID tokens passed from the client) and then makes authorization decisions or applies its own logic.

## 8. Audit Logging

*   **Google Cloud Audit Logs:** Firestore interactions (both data access and admin activity) are logged in Google Cloud Audit Logs. These logs are essential for:
    *   Security monitoring and incident response.
    *   Compliance with regulations like HIPAA, providing an audit trail of who accessed or modified Protected Health Information (PHI).
*   **Configuration:** Ensure that Data Access audit logs for Cloud Firestore API are enabled for the project.
*   **Monitoring:** Regularly review and monitor these logs for suspicious activity or unauthorized access attempts. Set up alerts for critical security events.

## 9. User Roles in Custom Claims

*   **Firebase Custom Claims:** User roles (e.g., 'patient', 'nurse') are critical for the security rules defined above. These roles are assumed to be set as custom claims on the user's Firebase Authentication ID token.
*   **Management of Custom Claims:** Custom claims must be managed securely by the backend. They should be set:
    *   When a user account is created (e.g., during an admin-driven user registration process).
    *   When a user's role changes (e.g., if an admin promotes or changes a user's role).
    *   This is typically done using the Firebase Admin SDK.
*   **Token Verification:** The backend service should always verify the ID token sent by the client to ensure its integrity and extract custom claims reliably.

This plan provides a foundational security posture. It should be reviewed and updated regularly as the application evolves and new security threats emerge.
