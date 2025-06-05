# AI Report - Section VII: Plan of Care & To-Do List (UI Blueprint)

This document outlines the conceptual UI structure for Section VII of the AI-generated shift report.
It focuses on a basic to-do list functionality. Data management is simulated by `todo_list_manager.py`.

```html
<!-- Conceptual HTML-like structure -->
<div class="section-vii-plan-of-care-todo">
  <div class="header">
    <h4>Section VII: Plan of Care & To-Do List</h4>
    <!-- Patient context (name, room) would typically be inherited or selected -->
    <!-- For MVP, this might be a general unit to-do list or a specific patient's list -->
  </div>

  <div class="todo-input-area">
    <h5>Add New Task:</h5>
    <div class="input-grid">
      <div class="input-item description">
        <label for="task-description-input">Task Description:</label>
        <input type="text" id="task-description-input" placeholder="Enter task details...">
      </div>
      <div class="input-item priority">
        <label for="task-priority-input">Priority:</label>
        <select id="task-priority-input">
          <option value="Medium">Medium</option>
          <option value="Urgent">Urgent</option>
          <option value="High">High</option>
          <option value="Low">Low</option>
        </select>
      </div>
      <div class="input-item patient-assignment">
        <label for="task-patient-id-input">Assign to Patient (Optional):</label>
        <input type="text" id="task-patient-id-input" placeholder="e.g., PatientA_Room301 or general_unit">
      </div>
      <div class="input-item add-button">
        <button id="add-task-button" onclick="handleAddTask()">Add Task</button>
      </div>
    </div>
  </div>

  <div class="todo-display-area">
    <h5>Current Tasks:</h5>
    <div class="task-filters">
        <label for="task-patient-filter">Filter by Patient ID:</label>
        <input type="text" id="task-patient-filter-input" placeholder="Enter Patient ID to filter">
        <button onclick="handleFilterTasks()">Filter Tasks</button>
        <button onclick="handleClearPatientFilter()">Show All Tasks</button>
    </div>
    <ul id="tasks-list">
      <!--
        Tasks will be dynamically populated here.
        Each task is an object from MOCK_TASKS_DB (managed by todo_list_manager.py).
        Example list item structure:
      -->
      <li class="task-item status-pending priority-high">
        <input type="checkbox" id="task-{{task_id}}" onchange="handleUpdateTaskStatus('{{task_id}}', this.checked)">
        <label for="task-{{task_id}}" class="task-description">{{ description }}</label>
        <span class="task-priority">{{ priority }}</span>
        <span class="task-patient-id">(Patient: {{ patient_id }})</span>
        <span class="task-timestamp">Added: {{ created_at_formatted }}</span>
      </li>
      <li class="task-item status-completed priority-medium">
        <input type="checkbox" id="task-{{task_id_2}}" onchange="handleUpdateTaskStatus('{{task_id_2}}', this.checked)" checked>
        <label for="task-{{task_id_2}}" class="task-description">{{ description_2 }}</label>
        <span class="task-priority">{{ priority_2 }}</span>
        <span class="task-patient-id">(Patient: {{ patient_id_2 }})</span>
        <span class="task-timestamp">Added: {{ created_at_formatted_2 }}</span>
      </li>
      <!-- ... more task list items ... -->
    </ul>
    <div id="no-tasks-message" style="display:none;">
      <p>No tasks found or match the current filter.</p>
    </div>
  </div>
</div>

<!--
Conceptual JavaScript functionality:

// Global variable for current patient filter, if any
let currentPatientFilter = null;

function renderTasks() {
  // 1. Fetch tasks:
  //    const allTasks = get_all_tasks(currentPatientFilter, true); // From todo_list_manager.py (simulated backend call)
  //    This would be an API call in a real app.

  const tasksList = document.getElementById('tasks-list');
  const noTasksMessage = document.getElementById('no-tasks-message');
  tasksList.innerHTML = ''; // Clear previous list

  if (allTasks && allTasks.length > 0) {
    noTasksMessage.style.display = 'none';
    allTasks.forEach(task => {
      const listItem = document.createElement('li');
      listItem.className = `task-item status-${task.status.toLowerCase()} priority-${task.priority.toLowerCase()}`;

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.id = `task-${task.task_id}`;
      checkbox.checked = task.status === 'Completed';
      checkbox.onchange = () => handleUpdateTaskStatus(task.task_id, checkbox.checked);

      const descriptionLabel = document.createElement('label');
      descriptionLabel.htmlFor = `task-${task.task_id}`;
      descriptionLabel.className = 'task-description';
      descriptionLabel.textContent = task.description;

      const prioritySpan = document.createElement('span');
      prioritySpan.className = 'task-priority';
      prioritySpan.textContent = task.priority;

      const patientIdSpan = document.createElement('span');
      patientIdSpan.className = 'task-patient-id';
      patientIdSpan.textContent = `(Patient: ${task.patient_id || 'N/A'})`;

      const timestampSpan = document.createElement('span');
      timestampSpan.className = 'task-timestamp';
      // Basic formatting for display, can be more sophisticated
      timestampSpan.textContent = `Added: ${new Date(task.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;

      listItem.appendChild(checkbox);
      listItem.appendChild(descriptionLabel);
      listItem.appendChild(prioritySpan);
      listItem.appendChild(patientIdSpan);
      listItem.appendChild(timestampSpan);
      tasksList.appendChild(listItem);
    });
  } else {
    noTasksMessage.style.display = 'block';
  }
}

function handleAddTask() {
  const description = document.getElementById('task-description-input').value;
  const priority = document.getElementById('task-priority-input').value;
  const patientId = document.getElementById('task-patient-id-input').value || "general"; // Default to general if empty

  if (!description) {
    alert("Task description cannot be empty.");
    return;
  }

  // add_task(description, priority, patientId); // From todo_list_manager.py (simulated backend call)
  // After successful backend call:
  document.getElementById('task-description-input').value = ''; // Clear input
  document.getElementById('task-patient-id-input').value = '';
  renderTasks(); // Re-render the list to show the new task
}

function handleUpdateTaskStatus(taskId, isChecked) {
  const newStatus = isChecked ? "Completed" : "Pending";
  // update_task_status(taskId, newStatus); // From todo_list_manager.py (simulated backend call)
  // After successful backend call:
  renderTasks(); // Re-render to reflect status change (styling, sorting)
}

function handleFilterTasks() {
    currentPatientFilter = document.getElementById('task-patient-filter-input').value;
    renderTasks();
}

function handleClearPatientFilter() {
    currentPatientFilter = null;
    document.getElementById('task-patient-filter-input').value = '';
    renderTasks();
}

// Initial load:
// window.onload = () => {
//   renderTasks(); // Load all tasks initially
// };
-->
```
