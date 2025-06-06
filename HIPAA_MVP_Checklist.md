# Project Noah - HIPAA Compliance Checklist (MVP V1.0)

This document outlines key HIPAA technical safeguards and how they are addressed within the Project Noah MVP. It serves as a reference for compliance efforts and identifies areas for ongoing attention.

## 1. Access Control (45 CFR § 164.312(a))

*   **Unique User Identification (Required):**
    *   **Status/Notes:** Implemented. Uses Firebase Authentication, ensuring each user has a unique ID (`request.auth.uid`).
*   **Emergency Access Procedure (Addressable):**
    *   **Status/Notes:** Not explicitly defined for MVP. Assumed that direct Firestore/GCP console access by authorized administrators would be the emergency route. Formal procedure recommended for future.
*   **Automatic Logoff (Addressable):**
    *   **Status/Notes:** Primarily a client-side concern. Firebase ID tokens have an expiration time (typically 1 hour), requiring re-authentication, which provides a form of session timeout. Frontend should handle actual logoff upon token expiration.
*   **Encryption and Decryption (Addressable):**
    *   **Status/Notes:**
        *   **Data at Rest:** Firestore encrypts data at rest by default. GCS buckets also encrypt data at rest by default.
        *   **Data in Transit:** See Transmission Security.
        *   No application-level encryption/decryption of PHI implemented for MVP (relies on GCP's managed encryption).

## 2. Audit Controls (45 CFR § 164.312(b))

*   **Audit Trails (Required):**
    *   **Status/Notes:**
        *   **GCP Audit Logs:** Google Cloud Platform provides audit logs for Firestore, GCS, and other services, covering administrative actions and some data access events (configuration dependent).
        *   **Application-Level Audit Trails:**
            *   `PatientDataLog` (`created_at`, `updated_at`, `created_by_user_id`, `user_id`, `timestamp`, `source`) provides some audit capability for patient data entries.
            *   `InteractionHistory` (`timestamp`, `user_id`, `actor`, `session_id`) provides audit for conversations.
            *   `UserProfile`, `PatientProfile`, etc., have `created_at`, `updated_at`.
            *   Specific logging of unauthorized access attempts (e.g., in `patient_data.py`, `history.py`) provides targeted audit points.
        *   No centralized application-level audit log aggregator is implemented in MVP beyond what Firestore/models provide.

## 3. Integrity (45 CFR § 164.312(c))

*   **Mechanism to Authenticate Electronic Protected Health Information (ePHI) (Addressable):**
    *   **Status/Notes:**
        *   Data integrity relies on secure storage (Firestore/GCS) and controlled access.
        *   Timestamps (`created_at`, `updated_at`) help track data modifications.
        *   No explicit data signing or cryptographic checksums at the application level for MVP.

## 4. Person or Entity Authentication (Required)

*   **Authentication of Users (Required):**
    *   **Status/Notes:** Implemented. Uses Firebase Authentication to verify user identities via ID tokens before granting access to backend APIs. (See `core/security.py`).

## 5. Transmission Security (45 CFR § 164.312(e))

*   **Integrity Controls (Addressable):**
    *   **Status/Notes:** HTTPS (TLS) ensures data integrity during transmission to/from API endpoints.
*   **Encryption (Required):**
    *   **Status/Notes:** HTTPS (TLS) encrypts data in transit between clients/services and the backend API. Communication between backend services and GCP services (Firestore, GCS, Vertex AI) is also over secure channels managed by Google.

## 6. Business Associate Agreements (BAAs)

*   **Agreement with Cloud Provider (Google Cloud Platform):**
    *   **Status/Notes:** Required. Project Noah relies on GCP services (Firestore, GCS, Vertex AI, Cloud Run). A BAA with Google Cloud must be in place.
*   **Agreement with LLM Provider (Google Vertex AI):**
    *   **Status/Notes:** Required, as PHI is sent to Vertex AI for processing by LLMs. Covered by the GCP BAA.

## 7. Data Handling and Minimization

*   **PHI Logging:**
    *   **Status/Notes:**
        *   **Issue Found:** `llm_service.py` logs full request contents (PHI) at `DEBUG` level. **Action Required:** Remediate by masking or removing PHI from this log, or ensure DEBUG level is disabled in production.
        *   Potential for PHI leakage in generic exception logs if exception messages contain data. **Recommendation:** Review and consider custom exceptions or careful logging.
*   **API Authorization:**
    *   **Status/Notes:**
        *   Authentication is applied to all PHI-handling endpoints.
        *   Self-access authorization is mostly in place for MVP.
        *   **Critical Gap:** Commented-out self-access authorization in `POST /api/v1/endpoints/patient_data.py` MUST be activated.
        *   Full Role-Based Access Control (RBAC) for nurses/other roles is pending.
*   **Firestore Security Rules:**
    *   **Status/Notes:** Defined in `firestore.rules` to enforce data segregation and user-specific access. These rules are critical and require thorough testing (e.g., Firebase Emulator Suite).
*   **GCS Bucket Access:**
    *   **Status/Notes:**
        *   `RAG_GCS_BUCKET_NAME`: Access should be restricted to the backend service account (least privilege). PHI content depends on RAG source data – needs clarification.
        *   `USER_DOCUMENT` storage: Mechanism (and potential GCS usage) needs clarification and security review if GCS is used.

## 8. Policies and Procedures (Organizational Requirement - for context)

*   **Security Incident Procedures (Addressable):**
    *   **Status/Notes:** Beyond MVP code, but organizational procedures for responding to security incidents are required.
*   **Contingency Plan (Addressable):**
    *   **Status/Notes:** Data backup/restore for Firestore is managed by GCP. Application-level contingency plans are an organizational responsibility.

## Disclaimer

This checklist is for MVP V1.0 informational purposes and based on code/architecture review. It is not exhaustive legal advice. Continuous review and updates are necessary.
```
