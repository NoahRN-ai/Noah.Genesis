# Conceptual Pub/Sub Setup for Noah Foundational Data Aggregation MVP

This document outlines the conceptual setup for Google Cloud Pub/Sub, which would be used for real-time event ingestion and alerting within the Noah system. Actual provisioning of these resources would typically be done via the Google Cloud Console, `gcloud` CLI, or Infrastructure as Code tools (e.g., Terraform).

## Pub/Sub Topics

### 1. `patient-monitor-alerts`

*   **Purpose:** This topic is designed to receive real-time alerts generated from (simulated) patient monitoring devices or systems. Examples include alerts for vital sign threshold breaches (e.g., high heart rate, low oxygen saturation), critical lab results, or device malfunctions.
*   **Producers:** Simulated bedside monitors, EMR event streams, or other clinical systems capable of detecting and publishing urgent events.
*   **Consumers:** Alerting services, dashboards, data logging systems (e.g., writing to AlloyDB `EventLogs`), or an event-driven processing pipeline that might trigger further actions.
*   **Example Message Format (JSON):**
    ```json
    {
      "alertId": "ALERT_UUID_HERE", // Unique identifier for the alert
      "patientId": "PATIENT_MRN_OR_INTERNAL_ID",
      "alertType": "VITAL_SIGN_THRESHOLD_BREACH", // E.g., HIGH_HEART_RATE, LOW_SPO2, CRITICAL_GLUCOSE
      "priority": "HIGH", // E.g., HIGH, MEDIUM, LOW
      "timestamp": "YYYY-MM-DDTHH:mm:ss.sssZ", // ISO 8601 timestamp
      "sourceDevice": "BedsideMonitor_Room302_BedA",
      "metric": {
        "name": "HeartRate", // Or "SpO2", "BloodPressureSystolic", "Glucose"
        "value": "135", // Can be string or number
        "unit": "bpm",
        "threshold": ">120"
      },
      "message": "Heart rate is 135 bpm, exceeding threshold of >120 bpm.",
      "ward": "ICU", // Optional: ward or location information
      "room": "302A" // Optional
    }
    ```

### 2. `emr-fhir-updates` (Optional - for future CDC-like integration)

*   **Purpose:** If a more direct CDC-like mechanism from an EMR (beyond simple FHIR polling) is envisioned, this topic could be used to stream granular FHIR resource updates. For example, every time a Patient resource, Observation, or Condition is created or updated in the EMR, a message is published here.
*   **Producers:** A Datastream-like service or a custom EMR integration that captures changes and publishes them.
*   **Consumers:** A data ingestion service that processes these updates and replicates them to Firestore (for patient profiles) and AlloyDB (for relevant event logs or relational records).
*   **Example Message Format (JSON - FHIR Resource centric):**
    ```json
    {
      "updateId": "CDC_UPDATE_UUID",
      "resourceType": "Patient", // Or "Observation", "Condition", etc.
      "resourceId": "FHIR_RESOURCE_ID", // The ID of the FHIR resource
      "operation": "UPDATE", // Or "CREATE", "DELETE"
      "timestamp": "YYYY-MM-DDTHH:mm:ss.sssZ",
      "payload": {
        // The actual FHIR resource or the delta
        "resourceType": "Patient",
        "id": "FHIR_RESOURCE_ID",
        "name": [{"family": "Doe", "given": ["John"]}],
        // ... other FHIR patient fields
      }
    }
    ```

## General Considerations

*   **Permissions:** Ensure that service accounts used by publishing and subscribing applications have the necessary IAM roles (e.g., `roles/pubsub.publisher` for producers, `roles/pubsub.subscriber` for consumers).
*   **Dead-letter Topics (DLQs):** For robust error handling, each subscription should be configured with a dead-letter topic to capture messages that cannot be processed successfully.
*   **Schemas (Optional but Recommended):** For topics with structured data like JSON, consider using Pub/Sub schema validation to ensure data integrity.
*   **Monitoring & Logging:** Utilize Cloud Monitoring and Cloud Logging to track Pub/Sub topic performance, message rates, and any errors in publishing or subscription.

This conceptual setup provides a basis for building real-time data flows within the Noah ecosystem. The specifics of implementation will depend on the exact requirements of the data sources and consuming applications.
