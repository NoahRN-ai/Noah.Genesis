# Noah AI Report - Section IX: Basic Handoff Summary (MVP)

This directory contains the MVP definition for data preparation, conceptual UI, and Text-to-Speech (TTS) placeholder logic for Section IX (Basic Handoff Summary). This version aims for deeper integration by attempting to use functionalities from other MVP agent scripts.

## File Index

1.  **`handoff_summary_generator.py`**
    *   **Purpose:** Simulates backend logic for generating handoff summary data, attempting to integrate with other agents.
    *   **Functionality:**
        *   **Integrated Agent/Data Stubs:**
            *   `get_patient_profile_stub(patient_id)`: Attempts to import and use mock patient profile data from `noah_patient_summary_agent_mvp.patient_summary_agent.MOCK_PATIENT_PROFILES`. Falls back to a local mock if import fails.
            *   `get_recent_events_stub(patient_id, shift_duration_hours)`: Attempts to import and use `get_mock_shift_events` from `noah_shift_events_log_display_mvp.events_log_data_prep` (which in turn tries to use the shared event store). Falls back to local mock events if import fails.
            *   `call_patient_summary_agent_for_handoff_stub(profile, events)`: Attempts to import and use `generate_summary_with_llm` and `query_vertex_ai_search` from `noah_patient_summary_agent_mvp.patient_summary_agent` to create a more deeply simulated AI shift summary. Falls back to simpler local summary logic if import fails.
        *   **Text-to-Speech Placeholder (`call_tts_service_stub`):** Remains a local stub that simulates a TTS call and returns a mock audio file reference.
        *   **Main Data Generation (`generate_handoff_data`):**
            *   Orchestrates calls to the (preferably imported) stubs for profile, events, and AI summary.
            *   Constructs text for TTS from the AI summary and manual inputs.
            *   Calls the local TTS stub.
            *   Returns a structured dictionary with all handoff data.
    *   **Example Usage:** The `if __name__ == "__main__":` block demonstrates calling `generate_handoff_data`. Print statements during execution will indicate if imported modules are being used or if it's operating with local fallbacks.

2.  **`section_ix_handoff_summary_ui.md`**
    *   **Purpose:** (No change from previous state for this subtask) A markdown file outlining a conceptual HTML-like structure for the Handoff Summary (Section IX) UI.
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
    *   It would then call a backend service (simulated by `generate_handoff_data`).
    *   `generate_handoff_data` now attempts to use functions/data from other agent scripts (patient summary, event log) to gather information before generating the handoff content and TTS audio reference.
    *   The UI is then updated with this new data.
  3.  The "Play Voice Handoff" button would use the `voice_handoff_audio_ref`.
  4.  "Finalize & Save Handoff" would persist the handoff state.

## Important Notes

*   **Simulations & Integrations:**
    *   This version of `handoff_summary_generator.py` attempts deeper integration by calling functions that would ideally reside in other specialized agent scripts.
    *   **Success of Imports:** The actual success of these cross-script imports and function calls depends heavily on the Python execution environment (e.g., `PYTHONPATH` setup). The script includes print statements to indicate success or failure of imports and uses local fallbacks if necessary. In a real project, this would be handled by a proper Python packaging and module structure.
*   **UI Blueprint:** The `section_ix_handoff_summary_ui.md` remains a conceptual guide.
*   **MVP Focus:** The focus is on demonstrating the *intended flow of information* between agents, even if the "calls" are simulated through Python imports in this MVP environment.
