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
            *   `store_event_in_alloydb(event_data: dict)`: This function now simulates writing event data to a global Python dictionary named `SHARED_MOCK_EVENTS_DB` (keyed by `patient_id`). This shared store is intended to be accessible by other agent scripts (e.g., the events log display agent) for integrated MVP demonstration. It also prints the event data being "stored".
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
    *   The simulated database write operations (now to `SHARED_MOCK_EVENTS_DB`).
    *   Simulated Speech-to-Text transcriptions.

## Event Structure and Handling

*   **Core Event Object (as stored in `SHARED_MOCK_EVENTS_DB`):** Each event is structured as a dictionary:
    *   `event_id`: A unique UUID for the event.
    *   `timestamp`: An ISO 8601 formatted UTC timestamp.
    *   `patient_id`: The ID of the patient related to the event. System-wide alerts might use a special key like `_system_alerts`.
    *   `event_type`: A string categorizing the event (e.g., "vital_sign", "intervention").
    *   `details`: A nested dictionary containing the specific information for that event type.
    *   `source`: Indicates the origin of the event data.

*   **Schema Validation:** The `event_schemas.json` file provides a way to define expected fields for each `event_type`. The `validate_event_details` function currently checks if all `required_keys` specified in the schema are present in the `event_details`.

*   **Shared Mock Database (`SHARED_MOCK_EVENTS_DB`):**
    *   The `store_event_in_alloydb` function now primarily writes events to the `SHARED_MOCK_EVENTS_DB` dictionary, which is defined globally in this script.
    *   This change is intended to allow other MVP scripts (like `events_log_data_prep.py` from the Shift Events Log Display MVP) to access and display events captured by this agent, simulating a shared data layer for the purpose of MVP integration.
    *   The structure of events stored includes `event_id`, `timestamp`, `patient_id`, `event_type`, `details`, and `source`.

## Important Notes

*   **Simulations:**
    *   **Speech-to-Text:** The `transcribe_voice_input` function remains a placeholder.
    *   **Database Interaction:** The `store_event_in_alloydb` function now writes to the in-memory `SHARED_MOCK_EVENTS_DB`. It does **not** connect to or write to any actual persistent database. This shared dictionary is for MVP demonstration of inter-agent data flow.
*   **Cross-Script Data Sharing:** For `SHARED_MOCK_EVENTS_DB` to be truly shared during execution, scripts from other MVP directories would need to import it. This can be complex depending on the Python execution environment and path configurations. The `events_log_data_prep.py` script attempts this import with fallbacks.
*   **UUID for Event ID:** Each event stored in `SHARED_MOCK_EVENTS_DB` gets a unique `event_id` generated using `uuid.uuid4()`.
*   **Extensibility:** The system is designed to be extensible. New event types can be added by:
    1.  Defining their schema in `event_schemas.json`.
    2.  Optionally, creating new helper functions in `shift_event_capture.py` for easier logging of the new event type.
