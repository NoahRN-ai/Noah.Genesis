# Firestore Indexing Strategy and Terraform Management

This document outlines the indexing strategy for the new Firestore collections based on current query patterns and discusses the role of Terraform in managing these indexes.

## 1. Review of New Collections and Query Patterns

The primary collections and associated query patterns relevant for indexing are:

*   **`noah_mvp_patients` Collection:**
    *   Accessed via `get_patient_profile(patient_id: str)`: This is a direct document lookup by ID, which is inherently efficient and uses Firestore's built-in index on document IDs.
    *   Accessed via `list_patient_profiles(limit: int, order_by: str = "created_at", descending: bool)`: This query involves ordering by a single field (`created_at`).

*   **`noah_mvp_observations` Subcollection (under `noah_mvp_patients/{patientId}`):**
    *   Accessed via `get_observation(patient_id: str, observation_id: str)`: Direct document lookup by ID within a subcollection.
    *   Accessed via `list_observations_for_patient(patient_id: str, limit: int, order_by: str = "effectiveDateTime", descending: bool)`: This query is performed on a subcollection, filtering implicitly by `patient_id` (due to path structure) and ordering by `effectiveDateTime`.

*   **`noah_mvp_medication_statements` Subcollection (under `noah_mvp_patients/{patientId}`):**
    *   Accessed via `get_medication_statement(patient_id: str, statement_id: str)`: Direct document lookup by ID within a subcollection.
    *   Accessed via `list_medication_statements_for_patient(patient_id: str, limit: int, order_by: str = "effectiveDateTime", descending: bool)`: Similar to observations, this queries a subcollection, ordering by `effectiveDateTime`.

*   **`ai_contextual_stores` Collection:**
    *   Accessed via `get_ai_contextual_store(patient_id: str)`: Direct document lookup by ID.
    *   Accessed via `create_or_replace_ai_contextual_store(patient_id: str, ...)`: Direct document write by ID.
    *   Accessed via `update_ai_contextual_store(patient_id: str, ...)`: Direct document update by ID.

## 2. Firestore Automatic Indexing

Firestore automatically creates single-field indexes for each field in a document and for each field in subcollections. These automatic indexes allow for:
*   Queries filtering on a single field (`where('field', '==', 'value')`).
*   Queries ordering by a single field (`orderBy('field')`).
*   Basic queries on subcollections (as Firestore treats subcollections independently regarding automatic indexing for their fields).

For all direct document lookups by ID (e.g., `get_patient_profile`, `get_observation`), Firestore's default behavior is highly efficient.

## 3. Potential Need for Composite Indexes

Based on the *current* service layer functions as defined:

*   `list_patient_profiles`: Orders by `created_at` (single field). Covered by automatic indexing.
*   `list_observations_for_patient`: This query is performed on a subcollection (`noah_mvp_observations`) and orders by `effectiveDateTime`. Since the query is scoped to a specific patient's subcollection, this effectively acts like a single-field order within that subcollection's documents. Covered by automatic indexing.
*   `list_medication_statements_for_patient`: Similar to observations, this orders by `effectiveDateTime` within a specific patient's subcollection. Covered by automatic indexing.

**Conclusion for current MVP queries:** The currently defined list operations are likely covered by Firestore's automatic single-field indexing capabilities because they involve ordering by a single field within the scope of a collection or subcollection.

**Future Query Changes Necessitating Composite Indexes:**

As the application evolves, more complex query patterns will likely emerge, requiring composite indexes. Examples:

*   **Filtering and Ordering on `noah_mvp_observations`:**
    *   "Find all observations for patient X with a specific `code.text` (e.g., 'Blood Pressure') and order them by `effectiveDateTime` descending."
        *   This would require a composite index on (`code.text` ASC, `effectiveDateTime` DESC) for the `noah_mvp_observations` collection.
    *   "Find all 'final' observations for patient X related to 'glucose' measurement, ordered by `issued` timestamp."
        *   Requires composite index on (`status` ASC, `code.text` ASC, `issued` DESC).

*   **Filtering by multiple fields in `noah_mvp_patients`:**
    *   "List all active male patients created in the last month."
        *   Requires composite index on (`active` ASC, `gender` ASC, `created_at` DESC).

*   **Range queries on one field and equality on another:**
    *   "Find observations for patient X where `valueQuantity.value` > 100 and `code.text` == 'Weight'."
        *   Requires composite index on (`code.text` ASC, `valueQuantity.value` ASC/DESC).

When such queries are attempted without a supporting composite index, Firestore will typically return an error message in the application logs and often provide a direct link in the Firebase Console to create the required index.

## 4. Terraform for Index Management

*   **Recommendation:** It is strongly recommended that all Firestore composite indexes be defined and managed programmatically using Infrastructure as Code, specifically Terraform.
*   **Benefits:**
    *   **Version Control:** Index definitions are stored in version control, tracking changes over time.
    *   **Reproducibility:** Ensures consistent index deployment across different environments (dev, staging, prod).
    *   **Automation:** Simplifies the process of setting up new environments or recovering existing ones.
    *   **Reviewability:** Index changes can be reviewed as part of code review processes.
*   **Implementation:**
    *   A dedicated file, such as `terraform/firestore_indexes.tf` (or a similar logical grouping within your Terraform configuration), should be used to define `google_firestore_index` resources.
    *   Example structure for a composite index in Terraform:
        ```terraform
        resource "google_firestore_index" "observations_code_time_idx" {
          project    = var.google_project_id
          database   = "(default)" # Or your specific database ID
          collection = "noah_mvp_observations" # Note: For subcollections, this is the subcollection name.

          fields {
            field_path = "code.text"
            order      = "ASCENDING"
          }
          fields {
            field_path = "effectiveDateTime"
            order      = "DESCENDING"
          }
          # For subcollection indexes, you need to specify query_scope
          query_scope = "COLLECTION_GROUP" # If you query across all patients' observations
          # Or if always queried under a specific patient (ancestor path):
          # query_scope = "COLLECTION" and ensure queries are not collection group queries.
          # For the current list_observations_for_patient, it's a COLLECTION scope query.
          # If future queries need to search observations across ALL patients (e.g. for analytics),
          # then COLLECTION_GROUP is appropriate for that index.
        }
        ```
        *Self-correction: For subcollection indexes like `noah_mvp_observations` when queried via `list_observations_for_patient` (which targets a specific patient's subcollection, not a collection group query), the `query_scope` would be `COLLECTION`. If collection group queries are introduced later (e.g., "find all observations with code X across all patients"), then a separate index with `COLLECTION_GROUP` scope would be needed.*

*   **Process:** When Firestore indicates a missing index (often via an error message with a creation link in the Firebase console), use the information from that link (fields, order, collection) to create the corresponding `google_firestore_index` resource in Terraform. Avoid creating indexes manually through the console for long-term manageability.

## 5. Monitoring and Performance

*   **Active Monitoring:** Continuously monitor query performance using Google Cloud Monitoring or Firestore performance dashboards.
*   **Error Logs:** Pay close attention to application logs for any Firestore-related errors, especially those indicating missing indexes (`FAILED_PRECONDITION: The query requires an index...`).
*   **Iterative Refinement:** As new features are added or query patterns change, revisit indexing needs. What is optimal for MVP might need adjustment as the application scales.

## 6. MVP Conclusion

For the **current MVP service functions as defined**, Firestore's automatic single-field indexing is likely sufficient. The `list_...` functions primarily order by a single field within a collection or a specific patient's subcollection, which automatic indexes support.

However, it is crucial to:
1.  **Be prepared to add composite indexes** as soon as query patterns become more complex (e.g., filtering on one field and ordering by another).
2.  **Establish the practice of managing indexes via Terraform from the outset**, even if no composite indexes are needed on day one. This sets up good infrastructure hygiene.
3.  **Test all query patterns thoroughly** in a development environment to catch any missing index errors early. Firestore will usually provide clear error messages if an index is needed.

Proactive planning for index management via Terraform will significantly benefit the project's scalability, maintainability, and operational stability in the long run.
