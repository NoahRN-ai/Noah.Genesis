# Strategy for Existing Models: UserProfile and PatientDataLog

This document outlines the relationship and go-forward strategy for the existing `UserProfile` and `PatientDataLog` models now that new FHIR-inspired models (`PatientProfile`, `Observation`, `MedicationStatement`) and their services are in place.

## 1. `UserProfile` Model (Collection: `user_profiles`)

*   **Original Purpose:** To store basic profile information for any registered user, differentiated by a `role` field (e.g., `UserRole.NURSE`, `UserRole.PATIENT`).

*   **New FHIR-inspired Model:** `PatientProfile` (Collection: `noah_mvp_patients`) has been introduced to store comprehensive demographic and administrative data for patients, aligned with FHIR standards. The `patient_id` for these documents is the Firebase Auth UID of the patient.

*   **Go-Forward Strategy for `UserProfile`:**
    *   **Primary Use for Non-Patient Roles:** `UserProfile` will continue to be the primary model for storing profile information for **nurse users** and any other future non-patient staff roles (e.g., administrators, doctors if added). The `user_id` for these documents will be the Firebase Auth UID of the staff member.
    *   **Patient Users:**
        *   The `PatientProfile` model is now the definitive source for all patient-specific demographic, administrative, and contact information.
        *   While a `UserProfile` document with `role: UserRole.PATIENT` might technically still exist (if patients were previously created this way or if they have app-specific preferences stored in `UserProfile.preferences` not covered by `PatientProfile`), new patient data and primary patient management should focus on the `PatientProfile` collection.
        *   For clarity and to avoid data duplication or confusion, creating new `UserProfile` entries for users with `role: UserRole.PATIENT` should be reconsidered. If a patient user needs application preferences, these could potentially be moved to `AIContextualStore.preferences` or a dedicated section within `PatientProfile` if appropriate. For MVP, we assume patient users primarily interact via their `PatientProfile`.

*   **Relationship:**
    *   A nurse's `UserProfile.user_id` may be referenced in `Observation.performer_user_id` or `MedicationStatement.informationSource_user_id`.
    *   A patient's identity is primarily managed via `PatientProfile.patient_id`.

## 2. `PatientDataLog` Model (Collection: `patient_data_logs`)

*   **Original Purpose:** To store various types of patient-related data logs, including observations, symptom reports, LLM summaries, etc., using a generic `content: Dict[str, Any]` field and a `PatientDataLogDataType` enum.

*   **New FHIR-inspired Models:** `Observation` and `MedicationStatement` models have been introduced, stored in dedicated subcollections (`noah_mvp_observations` and `noah_mvp_medication_statements`) under each patient's `PatientProfile` document.

*   **Go-Forward Strategy for `PatientDataLog`:**
    *   **No Longer for Observations/Medications:**
        *   The `PatientDataLog` model **MUST NOT** be used for storing new clinical observations or medication statements. The `PatientDataLogDataType.OBSERVATION` value should be considered deprecated for new entries.
        *   All new observation data must be stored using the `Observation` model in the `noah_mvp_patients/{patientId}/noah_mvp_observations` subcollection.
        *   All new medication statement data must be stored using the `MedicationStatement` model in the `noah_mvp_patients/{patientId}/noah_mvp_medication_statements` subcollection.
    *   **Continued Use for Other Data Types:**
        *   `PatientDataLog` **MAY CONTINUE** to be used for the other existing `PatientDataLogDataType` enum values that are not yet covered by specific FHIR-inspired models. This includes:
            *   `SYMPTOM_REPORT`
            *   `LLM_SUMMARY`
            *   `NURSING_NOTE_DRAFT`
            *   `SHIFT_HANDOFF_DRAFT`
            *   `USER_DOCUMENT` (e.g., text extracted from patient-uploaded documents)
        *   For these data types, the `content: Dict[str, Any]` field will continue to store the relevant payload.
    *   **Field Definitions:**
        *   `PatientDataLog.user_id`: This field refers to the `PatientProfile.patient_id` of the patient to whom the log entry pertains.
        *   `PatientDataLog.created_by_user_id`: This field refers to the `UserProfile.user_id` of the user (nurse or patient self-reporting) who created the log entry.

## 3. Recommendation for Future Structured Clinical Data

*   **Follow FHIR-Inspired Pattern:** It is strongly recommended that any new, distinct types of structured clinical or patient-related data follow the pattern established by `Observation` and `MedicationStatement`.
*   **Specific Models and Collections:** Instead of adding new enum values to `PatientDataLogDataType` and relying on its generic `content` field for complex structured data, prefer to:
    1.  Define new, specific Pydantic models (e.g., `AllergyIntolerance`, `Procedure`, `Condition`) inspired by relevant FHIR resources.
    2.  Create dedicated Firestore collections or subcollections for these new models (e.g., a `noah_mvp_allergy_intolerances` subcollection under `PatientProfile`).
    3.  Implement specific service functions for CRUD operations on these new models.
*   **Benefits of This Approach:**
    *   **Data Integrity:** Strong typing and clear schemas for each data type.
    *   **Queryability:** More efficient and targeted querying capabilities.
    *   **Scalability:** Better organization and management as the variety of data types grows.
    *   **Interoperability:** Easier alignment with healthcare data standards like FHIR.

This strategy aims to leverage the strengths of dedicated, structured models for core clinical entities while allowing `PatientDataLog` to serve as a flexible store for less structured or more generic log-type data until they warrant their own specific models.
