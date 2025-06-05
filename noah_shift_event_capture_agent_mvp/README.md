# Noah Shift Event Capture Agent (MVP)

This directory contains the MVP implementation for the Noah Shift Event Capture Agent. This agent is responsible for logging various types of events that occur during a medical shift, such as vital signs, interventions, and observations (including those from simulated voice input).

## File Index

1.  **`shift_event_capture.py`**
    *   **Purpose:** The main Python script for capturing and processing shift events.
    *   **Content:**
        *   **Event Schema Handling:**
            *   `load_event_schemas()`: Loads event definitions from `event_schemas.json`.
            *   `validate_event_details()`: Performs basic validation of event data against the loaded schemas (checks for required keys).
        *   **Database Interaction Placeholder:**
            *   `store_event_in_alloydb(event_data: dict)`: Simulates writing event data to an AlloyDB `EventLogs` table. It currently prints the structured event data that would be sent to the database, including a generated `eventId` and ensuring the data is formatted into a `value` JSON blob.
        *   **Speech-to-Text Placeholder:**
            *   `transcribe_voice_input(mock_audio_blob: str)`: Simulates a call to a Speech-to-Text service, returning mock transcribed text based on keywords in the input string.
        *   **Core Event Logging:**
            *   `log_event(patient_id: str, event_type: str, event_details: dict, ...)`: A central function that adds a UTC timestamp, patient ID, and event type to the event details. It can validate the event against its schema and then calls the database storage placeholder. It also structures the data for storage, placing the original `event_details` into a `details` field and determining a `source` for the log.
        *   **Helper Logging Functions:**
            *   `log_vital_sign(...)`: For logging vital signs like heart rate, blood pressure.
            *   `log_intervention(...)`: For logging actions like medication administration or procedures.
            *   `log_observation(...)`: For logging textual observations.
            *   `log_general_note(...)`: For logging general text notes.
            *   `log_general_note_from_voice(...)`: Simulates capturing a note via voice by calling `transcribe_voice_input` and then logging the result.
            *   `log_alert_notification(...)`: For logging system or patient-specific alerts.
        *   **Example Usage:** The `if __name__ == "__main__":` block demonstrates how to use each logging function.

2.  **`event_schemas.json`**
    *   **Purpose:** A JSON file that defines the expected structure for different event types.
    *   **Content:** Contains schemas for `vital_sign`, `intervention`, `observation`, `general_note`, and `alert_notification`. Each schema specifies required keys and describes the expected fields. This file is loaded by `shift_event_capture.py` to perform basic validation.

## How to Run the Script

1.  **Navigate to the directory:**
    Open your terminal and change to the `noah_shift_event_capture_agent_mvp` directory.
    ```bash
    cd path/to/noah_shift_event_capture_agent_mvp
    ```

2.  **Run the Python script:**
    ```bash
    python shift_event_capture.py
    ```
    The script will execute the example usage defined in its `if __name__ == "__main__":` block. You will see output in the console showing:
    *   Initialization messages (like schema loading).
    *   The details of each logged event.
    *   The simulated database write operations (JSON blobs representing what would be stored in AlloyDB).
    *   Simulated Speech-to-Text transcriptions.

## Event Structure and Handling

*   **Core Event Object:** Each event logged by the system is structured as a dictionary containing:
    *   `timestamp`: An ISO 8601 formatted UTC timestamp, automatically added when the event is logged.
    *   `patient_id`: The ID of the patient related to the event (can be `None` for system-wide alerts).
    *   `event_type`: A string categorizing the event (e.g., "vital_sign", "intervention").
    *   `details`: A nested dictionary containing the specific information for that event type (e.g., for a vital sign, this would include `sign_name`, `value`, `unit`).
    *   `source`: Indicates the origin of the event data (e.g., "ClinicalDevice_ManualEntry", "voice_transcription_note", "LabInformationSystem").

*   **Schema Validation:** The `event_schemas.json` file provides a way to define expected fields for each `event_type`. The `validate_event_details` function currently checks if all `required_keys` specified in the schema are present in the `event_details`. This is a basic validation and can be extended.

*   **Database Simulation:** The `store_event_in_alloydb` function simulates how an event would be stored. It creates a structure compatible with a hypothetical `EventLogs` table (as might be defined in `alloydb_schemas.sql` from previous work), including generating a unique `eventId` and packaging most of the event-specific data into a JSON `value` field.

## Important Notes

*   **Simulations:**
    *   **Speech-to-Text:** The `transcribe_voice_input` function is a placeholder. It does **not** call any actual Speech-to-Text service; it returns predefined text based on simple string matching in the mock audio blob identifier.
    *   **AlloyDB Interaction:** The `store_event_in_alloydb` function is also a placeholder. It does **not** connect to or write to any actual database; it prints the data that would theoretically be persisted.
*   **UUID for Event ID:** Each event intended for the database gets a unique `eventId` generated using `uuid.uuid4()`.
*   **Extensibility:** The system is designed to be extensible. New event types can be added by:
    1.  Defining their schema in `event_schemas.json`.
    2.  Optionally, creating new helper functions in `shift_event_capture.py` for easier logging of the new event type.
