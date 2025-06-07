# Noah AI Report - Section VII: Plan of Care & To-Do List (MVP)

This directory contains the MVP definition for the data structures, basic management logic, and UI outline for Section VII (Plan of Care & To-Do List) of the AI-Powered Shift Report. This section focuses on a simple task management system.

## File Index

1.  **`todo_list_manager.py`**
    *   **Purpose:** This Python script simulates the backend logic for managing a to-do list.
    *   **Functionality:**
        *   **Task Data Structure:** A task is represented as a Python dictionary with fields like `task_id`, `patient_id`, `description`, `priority` ("Urgent", "High", "Medium", "Low"), `status` ("Pending", "Completed"), `created_at`, and `updated_at`.
        *   **In-Memory Storage (`MOCK_TASKS_DB`):** A global list in the script acts as an in-memory database to store these task dictionaries.
        *   **Task Management Functions:**
            *   `add_task(description: str, priority: str, patient_id: str) -> dict`: Creates a new task with a unique ID, timestamp, and initial "Pending" status, then adds it to `MOCK_TASKS_DB`.
            *   `get_task(task_id: str) -> dict | None`: Retrieves a specific task by its ID.
            *   `update_task_status(task_id: str, new_status: str) -> dict | None`: Updates a task's status (must be "Pending" or "Completed").
            *   `get_all_tasks(patient_id_filter: str = None, sort_by_priority: bool = True) -> list`: Returns tasks. Can be filtered by `patient_id` (also includes "general" tasks if a patient ID is provided) and sorted by status (Pending tasks first) then by priority (Urgent > High > Medium > Low).
    *   **Example Usage:** The `if __name__ == "__main__":` block demonstrates adding tasks, listing them (with and without patient filtering), updating task statuses, and retrieving specific tasks.

2.  **`section_vii_plan_of_care_ui.md`**
    *   **Purpose:** A markdown file outlining a conceptual HTML-like structure for the Plan of Care & To-Do List section of the UI.
    *   **Content:**
        *   **Task Input Area:** Mockup for UI elements to add new tasks:
            *   Text input for the task `description`.
            *   Dropdown select for choosing task `priority`.
            *   Text input for optional `patient_id` assignment.
            *   An "Add Task" button.
        *   **Task Display Area:**
            *   An unordered list (`<ul>`) to display tasks.
            *   Each task item conceptually shows:
                *   A checkbox indicating its `status` (checked if "Completed").
                *   The task `description`.
                *   The task `priority` (could be styled differently based on value).
                *   The assigned `patient_id`.
                *   A formatted creation timestamp.
            *   Input field and buttons for filtering tasks by `patient_id`.
        *   **Conceptual JavaScript:** Comments outline JavaScript functions to:
            *   `renderTasks()`: Fetch and display the list of tasks.
            *   `handleAddTask()`: Get data from input fields and call the (simulated) `add_task` backend function, then refresh the list.
            *   `handleUpdateTaskStatus()`: Call the (simulated) `update_task_status` backend function when a task's checkbox state changes, then refresh the list.
            *   `handleFilterTasks()` and `handleClearPatientFilter()`: Manage filtering tasks by patient ID.

## How the System Works (Conceptually)

1.  The `todo_list_manager.py` script acts as a simple in-memory backend for task data. In a real application, this would be replaced by a persistent database and API endpoints.
2.  The `section_vii_plan_of_care_ui.md` file provides a blueprint for the front-end UI.
3.  When a user interacts with the UI:
    *   **Adding a Task:** User fills in the description, selects a priority, optionally assigns a patient ID, and clicks "Add Task". Conceptual JavaScript calls the `add_task` function (simulated) and then re-renders the task list.
    *   **Updating Task Status:** User clicks the checkbox next to a task. Conceptual JavaScript calls the `update_task_status` function (simulated) with the new status ("Completed" or "Pending") and then re-renders the list to reflect the change (e.g., styling the task as completed, moving it in the sort order).
    *   **Filtering Tasks:** User enters a patient ID and clicks "Filter Tasks". Conceptual JavaScript calls `get_all_tasks` with the filter and re-renders the list.

## Important Notes

*   **Simulations:** All task management logic (adding, updating, fetching) is simulated in memory by `todo_list_manager.py`. No actual database is used.
*   **UI Blueprint:** The `.md` file is **not** functional UI code. It's an HTML-like outline to guide UI development, using `{{ placeholder }}` syntax and conceptual JavaScript comments to illustrate dynamic behavior.
*   **MVP Focus:** This MVP defines basic task data structures, core management functions (add, get, update status, list), and a conceptual UI for interacting with these tasks. AI-driven prioritization or more complex plan of care features are out of scope for this step.
*   **Patient ID:** The `patient_id` field in tasks allows for future expansion where tasks can be specifically tied to patients, while also supporting general unit tasks. The filtering logic demonstrates a basic approach to this.
