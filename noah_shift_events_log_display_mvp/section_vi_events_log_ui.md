# AI Report - Section VI: Shift Events Log (UI Blueprint)

This document outlines the conceptual UI structure for Section VI of the AI-generated shift report, focusing on the display and filtering of shift events.
Data for this section is prepared by `events_log_data_prep.py`.

```html
<!-- Conceptual HTML-like structure -->
<div class="section-vi-shift-events-log">
  <div class="header">
    <h4>Section VI: Shift Events Log</h4>
    <!-- Patient context (name, room) would typically be inherited -->
  </div>

  <div class="events-log-controls">
    <h5>Filter Events:</h5>
    <div class="filter-grid">
      <div class="filter-item">
        <label for="event-type-filter">Event Type:</label>
        <select id="event-type-filter">
          <option value="">All Types</option>
          <option value="vital_sign">Vital Sign</option>
          <option value="observation">Observation</option>
          <option value="intervention">Intervention</option>
          <option value="general_note">General Note</option>
          <option value="alert_notification">Alert Notification</option>
          <!-- Add other event types as needed -->
        </select>
      </div>

      <div class="filter-item">
        <label for="time-range-start-filter">From:</label>
        <input type="datetime-local" id="time-range-start-filter">
      </div>

      <div class="filter-item">
        <label for="time-range-end-filter">To:</label>
        <input type="datetime-local" id="time-range-end-filter">
      </div>

      <div class="filter-item">
        <button id="apply-filters-button" onclick="applyShiftEventsFilter()">Apply Filters</button>
        <button id="clear-filters-button" onclick="clearShiftEventsFilter()">Clear Filters</button>
      </div>
    </div>
  </div>

  <div class="events-log-display-area">
    <h5>Events:</h5>
    <ul id="shift-events-list">
      <!--
        Events will be dynamically populated here.
        Each event string is formatted by `format_event_for_display(event_data)`.
        Example list items:
      -->
      <li><span class="event-timestamp">[14:00]</span> <span class="event-type-tag alert">Alert Notification</span> [High] Critical Lab Value: Potassium 3.0 mEq/L (Low) (Type: CriticalLabValue)</li>
      <li><span class="event-timestamp">[13:30]</span> <span class="event-type-tag observation">Observation</span> Patient ambulated in hallway x2 with steady gait.</li>
      <li><span class="event-timestamp">[12:00]</span> <span class="event-type-tag vital-sign">Vital Sign</span> Temperature 37.1 Celsius</li>
      <!-- ... more event list items ... -->
    </ul>
    <div id="no-events-message" style="display:none;">
      <p>No events match the current filter criteria or no events recorded for this period.</p>
    </div>
  </div>
</div>

<!--
Conceptual JavaScript functionality:

function applyShiftEventsFilter() {
  // 1. Get filter values:
  const eventType = document.getElementById('event-type-filter').value;
  const startTime = document.getElementById('time-range-start-filter').value; // Needs conversion to ISO string if not already
  const endTime = document.getElementById('time-range-end-filter').value;   // Needs conversion to ISO string if not already

  // 2. Construct filter_criteria object:
  const filterCriteria = {};
  if (eventType) filterCriteria.event_type = eventType;
  if (startTime || endTime) {
    filterCriteria.time_range = {};
    if (startTime) filterCriteria.time_range.start = new Date(startTime).toISOString();
    if (endTime) filterCriteria.time_range.end = new Date(endTime).toISOString();
  }

  // 3. Call a function (simulated by events_log_data_prep.py's get_mock_shift_events)
  //    to fetch and filter events for the current patient_id using filterCriteria.
  //    const patientId = getCurrentPatientId(); // Assume this function exists
  //    const filteredEvents = get_mock_shift_events(patientId, filterCriteria); // This is a backend call in reality

  // 4. Update the UI:
  const eventsList = document.getElementById('shift-events-list');
  const noEventsMessage = document.getElementById('no-events-message');
  eventsList.innerHTML = ''; // Clear previous list

  if (filteredEvents && filteredEvents.length > 0) {
    noEventsMessage.style.display = 'none';
    filteredEvents.forEach(event => {
      const formattedEventString = format_event_for_display(event); // From events_log_data_prep.py
      const listItem = document.createElement('li');
      // Optional: Add classes for styling based on event_type for better visual distinction
      // Example: listItem.innerHTML = `<span class="event-timestamp">...</span> <span class="event-type-tag ${event.event_type}">...</span> ...`;
      listItem.textContent = formattedEventString;
      eventsList.appendChild(listItem);
    });
  } else {
    noEventsMessage.style.display = 'block';
  }
}

function clearShiftEventsFilter() {
  // 1. Reset filter input fields
  document.getElementById('event-type-filter').value = '';
  document.getElementById('time-range-start-filter').value = '';
  document.getElementById('time-range-end-filter').value = '';

  // 2. Call applyShiftEventsFilter() to reload all events (or a default set)
  applyShiftEventsFilter();
}

// Initial load:
// window.onload = () => {
//   applyShiftEventsFilter(); // Load with default filters (e.g., all events for the last X hours)
// };
-->
```
