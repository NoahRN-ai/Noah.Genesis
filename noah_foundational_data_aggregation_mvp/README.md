# Noah Foundational Data Aggregation MVP - File Descriptions

This directory contains the initial set of files for the Noah Foundational Data Aggregation MVP. The focus of this MVP is to establish the basic schemas, placeholder scripts for data handling, and conceptual designs for data flow.

## File Index

1.  **`firestore_patient_profile_schema.json`**
    *   **Purpose:** Defines the JSON schema for patient profile documents that would be stored in Firestore. This schema outlines the structure for essential patient demographic, medical, and administrative information.
    *   **Content:** Includes fields such as `patientId`, `name`, `dob`, `mrn`, `allergies`, `isolationPrecautions`, `codeStatus`, `admissionDate`, `principalProblem`, and `emergencyContact`.

2.  **`alloydb_schemas.sql`**
    *   **Purpose:** Contains SQL Data Definition Language (DDL) statements for setting up tables in an AlloyDB for PostgreSQL database. These tables are intended for storing core relational records and event logs.
    *   **Content:**
        *   `CoreRelationalRecords` table: Schema for storing records like physician orders or consult notes, linked to a patient. Includes `recordId`, `patientId`, `recordType`, `timestamp`, and `details` (JSONB).
        *   `EventLogs` table: Schema for logging various events related to a patient, such as vital sign changes, medication administrations, or manual nurse inputs. Includes `eventId`, `patientId`, `eventType`, `timestamp`, `value` (JSONB), and `source`.
        *   Includes definitions for primary keys, foreign key linkage (commented out, as actual patient table for FK is conceptual), and indexes for performance.

3.  **`manual_input_handler.py`**
    *   **Purpose:** A Python script providing placeholder functions for handling manual data inputs. These functions simulate interactions with Firestore and AlloyDB.
    *   **Content:**
        *   `add_patient_profile(data: dict)`: Simulates writing patient profile data to Firestore.
        *   `log_event(patient_id: str, event_type: str, value: dict)`: Simulates logging an event to the AlloyDB `EventLogs` table.
        *   `add_relational_record(patient_id: str, record_type: str, details: dict)`: Simulates adding a record to the AlloyDB `CoreRelationalRecords` table.
        *   Each function currently prints log messages indicating it was called and the data it received.
        *   Includes an `if __name__ == "__main__":` block with example usage.

4.  **`data_transformer.py`**
    *   **Purpose:** A Python script containing a placeholder function for data transformation logic. This script represents where future Extract, Transform, Load (ETL) processes would reside, potentially managed by a service like Cloud Data Fusion.
    *   **Content:**
        *   `transform_data_for_ai(raw_data: dict) -> dict`: A function that takes raw data as input and is intended to perform transformations to prepare it for AI/ML models or other analytical uses. Currently, it performs a very basic transformation (adds a timestamp and nests data).
        *   Includes an `if __name__ == "__main__":` block with example usage.

5.  **`pubsub_setup.md`**
    *   **Purpose:** A markdown document describing the conceptual setup for Google Cloud Pub/Sub topics. It outlines how Pub/Sub would be used for real-time event ingestion and alerting.
    *   **Content:**
        *   Details for a `patient-monitor-alerts` topic, including its purpose, typical producers/consumers, and an example JSON message format for alerts.
        *   Conceptual details for an `emr-fhir-updates` topic for future CDC-like integration.
        *   General considerations for Pub/Sub setup, such as permissions, dead-letter topics, and monitoring.

## Overall Goal

These files collectively lay the groundwork for building a more comprehensive data aggregation and processing system. They define the initial data structures and provide stubs for key data handling operations, allowing for iterative development and integration with actual cloud services in subsequent phases.
