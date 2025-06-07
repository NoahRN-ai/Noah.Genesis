# AI Report - Section IX: Handoff Summary (UI Blueprint)

This document outlines the conceptual UI structure for Section IX of the AI-Powered Shift Report, focusing on the Handoff Summary.
Data for this section is prepared by `handoff_summary_generator.py`.

```html
<!-- Conceptual HTML-like structure -->
<div class="section-ix-handoff-summary">
  <div class="header">
    <h4>Section IX: Handoff Summary for Patient: <span id="handoff-patient-name">{{ patient_name }}</span> (Room: <span id="handoff-room-no">{{ room_no }}</span>)</h4>
    <em id="handoff-generated-at">Generated: {{ generated_at_formatted }}</em>
  </div>

  <div class="handoff-content-grid">
    <!-- Column 1: AI Summary & Voice Handoff -->
    <div class="handoff-column">
      <h5>AI-Generated Shift Summary:</h5>
      <div id="ai-generated-summary-display" class="summary-box">
        <pre>{{ ai_generated_shift_summary }}</pre> <!-- Use <pre> for preserving newlines from the summary -->
      </div>

      <div id="voice-handoff-controls" class="voice-handoff-section">
        <h5>Voice Handoff:</h5>
        <button id="play-voice-handoff-button" onclick="playVoiceHandoff('{{ voice_handoff_audio_ref }}')" {{#unless voice_handoff_available}}disabled{{/unless}}>
          Play Voice Handoff
        </button>
        <span id="voice-handoff-status">
          {{#if voice_handoff_available}}
            (Audio available: {{ voice_handoff_audio_ref }})
          {{else}}
            (Voice handoff not generated or unavailable)
          {{/if}}
        </span>
        <!-- Conceptual audio player element -->
        <audio id="voice-handoff-player" style="display:none;"></audio>
      </div>
    </div>

    <!-- Column 2: Manual Inputs from Outgoing Nurse -->
    <div class="handoff-column">
      <h5>Outgoing Nurse Inputs:</h5>

      <div class="manual-input-group">
        <label for="top-priorities-input"><strong>Top Priorities for Incoming Nurse:</strong></label>
        <textarea id="top-priorities-input" rows="5" placeholder="Enter 2-3 key priorities..."></textarea>
        <!-- Display area for finalized priorities (if different from input) -->
        <div id="top-priorities-display" class="display-box">
          <ul>
            {{#each top_priorities_for_incoming_nurse}}
            <li>{{this}}</li>
            {{/each}}
          </ul>
        </div>
      </div>

      <div class="manual-input-group">
        <label for="params-to-monitor-input"><strong>Specific Parameters to Monitor Closely:</strong></label>
        <textarea id="params-to-monitor-input" rows="5" placeholder="List specific parameters and thresholds..."></textarea>
        <!-- Display area for finalized parameters -->
        <div id="params-to-monitor-display" class="display-box">
          <ul>
            {{#each parameters_to_monitor_closely}}
            <li>{{this}}</li>
            {{/each}}
          </ul>
        </div>
      </div>
    </div>
  </div>

  <div class="handoff-actions">
    <button id="generate-handoff-button" onclick="handleGenerateHandoff()">Generate/Refresh Handoff Data</button>
    <button id="finalize-handoff-button" onclick="handleFinalizeHandoff()">Finalize & Save Handoff</button>
    <!-- Finalize might save the manual inputs and the state of the handoff -->
  </div>
</div>

<!--
Data Mapping (from handoff_data dictionary):
- patient_name -> {{ patient_name }}
- room_no -> {{ room_no }}
- generated_at_formatted -> Formatted version of `generated_at`
- ai_generated_shift_summary -> {{ ai_generated_shift_summary }}
- voice_handoff_available -> Used to enable/disable Play button
- voice_handoff_audio_ref -> {{ voice_handoff_audio_ref }} (used by playVoiceHandoff function)
- top_priorities_for_incoming_nurse -> Loop to display list items (in display-box) & potentially pre-fill textarea
- parameters_to_monitor_closely -> Loop to display list items (in display-box) & potentially pre-fill textarea

Conceptual JavaScript functionality:

function loadHandoffData(patientId) {
  // 1. Get manual inputs from textareas (if any changes were made)
  const manualPriorities = document.getElementById('top-priorities-input').value.split('\n').filter(p => p.trim() !== '');
  const manualParams = document.getElementById('params-to-monitor-input').value.split('\n').filter(p => p.trim() !== '');

  // 2. Call backend (simulated by handoff_summary_generator.py's generate_handoff_data)
  //    const handoffData = generate_handoff_data(patientId, manualPriorities, manualParams);
  //    This would be an API call in a real app.

  // 3. Populate UI fields with handoffData:
  //    document.getElementById('handoff-patient-name').textContent = handoffData.patient_name;
  //    document.getElementById('handoff-room-no').textContent = handoffData.room_no;
  //    document.getElementById('ai-generated-summary-display').querySelector('pre').textContent = handoffData.ai_generated_shift_summary;
  //    ... and so on for other fields.
  //    Update the display lists for priorities and parameters.
  //    Enable/disable play button based on handoffData.voice_handoff_available.
  //    Store handoffData.voice_handoff_audio_ref for the play button.
}

function handleGenerateHandoff() {
  // const currentPatientId = getCurrentPatientId(); // Assume this function exists
  // loadHandoffData(currentPatientId);
  alert("Simulating: Handoff data (including AI summary and TTS audio ref) would be regenerated based on current inputs and fresh data.");
}

function playVoiceHandoff(audioRef) {
  if (!audioRef) {
    alert("No voice handoff audio reference available.");
    return;
  }
  // const audioPlayer = document.getElementById('voice-handoff-player');
  // audioPlayer.src = audioRef; // In a real app, this might be a URL to an MP3 file
  // audioPlayer.play();
  alert(`Simulating: Playing voice handoff audio from: ${audioRef}`);
}

function handleFinalizeHandoff() {
  // 1. Collect current data (AI summary, manual inputs, audio ref)
  // 2. Send this data to a backend endpoint to save/log the finalized handoff.
  alert("Simulating: Handoff finalized. Manual inputs and current summary state would be saved.");
}

// Initial load:
// window.onload = () => {
//   const currentPatientId = getCurrentPatientId();
//   loadHandoffData(currentPatientId);
// };
-->
```
