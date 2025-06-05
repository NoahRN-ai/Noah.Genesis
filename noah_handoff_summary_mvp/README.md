# Noah AI Report - Section IX: Basic Handoff Summary (MVP)

This directory contains the MVP definition for data preparation, conceptual UI, and Text-to-Speech (TTS) placeholder logic for Section IX (Basic Handoff Summary) of the AI-Powered Shift Report. This section aims to provide a concise summary for shift handoff, combining AI-generated insights with manual inputs from the outgoing nurse, and offering a conceptual voice handoff feature.

## File Index

1.  **`handoff_summary_generator.py`**
    *   **Purpose:** This Python script simulates the backend logic for generating the data needed for a handoff summary.
    *   **Functionality:**
        *   **Agent/Data Stubs:**
            *   `get_patient_profile_stub(patient_id)`: Returns mock patient profile data.
            *   `get_recent_events_stub(patient_id, shift_duration_hours)`: Returns a list of mock patient events from the specified recent duration.
            *   `call_patient_summary_agent_for_handoff_stub(profile, events)`: Simulates a call to the Patient Summary Agent to generate a concise AI-driven summary of the shift based on profile and recent events.
        *   **Text-to-Speech Placeholder:**
            *   `call_tts_service_stub(text_to_speak, language_code, patient_id)`: Simulates a call to a TTS service. It prints the text that would be synthesized and returns a mock audio file reference (e.g., "handoff_audio_patient123.mp3").
        *   **Main Data Generation (`generate_handoff_data`):**
            *   Takes `patient_id`, `manual_top_priorities` (list of strings), and `manual_params_to_monitor` (list of strings) as input.
            *   Fetches patient profile and recent events using the stubs.
            *   Calls the AI summary agent stub to get a shift summary.
            *   Constructs text for TTS by combining the AI summary and key manual inputs.
            *   Calls the TTS service stub to get a mock audio reference.
            *   Returns a dictionary containing all handoff data: `patient_id`, `patient_name`, `room_no`, `generated_at`, `ai_generated_shift_summary`, `top_priorities_for_incoming_nurse`, `parameters_to_monitor_closely`, `voice_handoff_available`, and `voice_handoff_audio_ref`.
    *   **Example Usage:** The `if __name__ == "__main__":` block demonstrates how to call `generate_handoff_data` with sample manual inputs and prints the resulting structured handoff data.

2.  **`section_ix_handoff_summary_ui.md`**
    *   **Purpose:** A markdown file outlining a conceptual HTML-like structure for the Handoff Summary (Section IX) UI.
    *   **Content:**
        *   **Display Areas:**
            *   Placeholders to display patient identifiers (`patient_name`, `room_no`).
            *   An area to show the `ai_generated_shift_summary`.
            *   Sections to list the manually entered `top_priorities_for_incoming_nurse` and `parameters_to_monitor_closely`.
        *   **Input Areas (for the outgoing nurse):**
            *   Text areas for providing "Top Priorities for Incoming Nurse."
            *   Text areas for listing "Specific Parameters to Monitor Closely."
        *   **Voice Handoff Feature:**
            *   A conceptual "Play Voice Handoff" button, which would be enabled if `voice_handoff_available` is true.
            *   Indication of the `voice_handoff_audio_ref`.
        *   **Action Buttons:** "Generate/Refresh Handoff Data" and "Finalize & Save Handoff" buttons to simulate user actions.
        *   **Conceptual JavaScript:** Comments outline JavaScript functions for loading data, handling button clicks (generating handoff, playing audio, finalizing), and updating the UI.

## How the System Works (Conceptually)

1.  The outgoing nurse uses the UI (blueprint in `section_ix_handoff_summary_ui.md`) to review an AI-generated summary and input their key priorities and parameters to watch.
2.  When "Generate/Refresh Handoff Data" is clicked (conceptually):
    *   JavaScript would collect the manual inputs.
    *   It would then call a backend service (simulated by `generate_handoff_data` in `handoff_summary_generator.py`).
    *   This service fetches the latest patient data, generates a new AI summary, combines it with the manual inputs for TTS, calls the TTS service (all simulated by stubs), and returns the complete handoff data structure.
    *   The UI is then updated with this new data.
3.  The "Play Voice Handoff" button would use the `voice_handoff_audio_ref` to play the synthesized audio.
4.  "Finalize & Save Handoff" would persist the current state of the handoff report (AI summary, manual inputs, audio reference) for record-keeping or for the incoming nurse to access.

## Important Notes

*   **Simulations:** All data fetching, AI summary generation, and TTS calls are simulated by stub functions in `handoff_summary_generator.py`. No actual external services are invoked.
*   **UI Blueprint:** The `.md` file is **not** functional UI code. It's an HTML-like outline to guide UI development, using `{{ placeholder }}` syntax and conceptual JavaScript comments.
*   **MVP Focus:** This MVP defines the data flow, core components, and UI concept for a basic handoff summary. It aims to show how AI-generated content, manual nurse inputs, and a voice component could come together.
*   **Error Handling:** Basic error handling (e.g., for a non-existent patient) is demonstrated in the Python script.
