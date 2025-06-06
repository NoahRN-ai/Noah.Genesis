import datetime
import uuid

# In-memory "database" for tasks
MOCK_TASKS_DB = []

# Define priority order for sorting (higher number = higher priority)
PRIORITY_ORDER = {"Urgent": 4, "High": 3, "Medium": 2, "Low": 1}

VALID_STATUSES = ["Pending", "Completed"]


def add_task(description: str, priority: str, patient_id: str = "general") -> dict:
    """Adds a new task to the MOCK_TASKS_DB.
    Includes a patient_id for future potential linking, defaults to "general".
    """
    if priority not in PRIORITY_ORDER:
        print(
            f"[{datetime.datetime.utcnow().isoformat()}] WARN: Invalid priority '{priority}'. Defaulting to 'Medium'."
        )
        priority = "Medium"

    task_id = str(uuid.uuid4())
    created_at = datetime.datetime.utcnow().isoformat() + "Z"

    new_task = {
        "task_id": task_id,
        "patient_id": patient_id,  # For potential future patient-specific task lists
        "description": description,
        "priority": priority,
        "status": "Pending",  # Initial status
        "created_at": created_at,
        "updated_at": created_at,  # Initially same as created_at
    }
    MOCK_TASKS_DB.append(new_task)
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] INFO: Task added: {task_id} - '{description}'"
    )
    return new_task


def get_task(task_id: str) -> dict | None:
    """Retrieves a task by its ID."""
    for task in MOCK_TASKS_DB:
        if task["task_id"] == task_id:
            return task
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] INFO: Task with ID {task_id} not found."
    )
    return None


def update_task_status(task_id: str, new_status: str) -> dict | None:
    """Updates the status of an existing task."""
    if new_status not in VALID_STATUSES:
        print(
            f"[{datetime.datetime.utcnow().isoformat()}] ERROR: Invalid status '{new_status}'. Must be one of {VALID_STATUSES}."
        )
        return None

    task = get_task(task_id)
    if task:
        task["status"] = new_status
        task["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        print(
            f"[{datetime.datetime.utcnow().isoformat()}] INFO: Task {task_id} status updated to '{new_status}'."
        )
        return task
    return None  # Task not found


def get_all_tasks(patient_id_filter: str = None, sort_by_priority: bool = True) -> list:
    """Returns all tasks, optionally filtered by patient_id and sorted by priority.
    If patient_id_filter is None, returns all tasks (general and patient-specific).
    If patient_id_filter is specified, returns tasks for that patient plus general tasks.
    """
    tasks_to_return = []
    if patient_id_filter:
        # Include tasks specific to the patient AND general tasks (patient_id="general")
        tasks_to_return = [
            task
            for task in MOCK_TASKS_DB
            if task.get("patient_id") == patient_id_filter
            or task.get("patient_id") == "general"
        ]
    else:
        # Return all tasks if no patient filter
        tasks_to_return = list(MOCK_TASKS_DB)

    if sort_by_priority:
        # Sort by status ("Pending" first) then by priority (Urgent > High > Medium > Low)
        tasks_to_return.sort(
            key=lambda t: (
                t["status"] != "Pending",
                -PRIORITY_ORDER.get(t["priority"], 0),
            )
        )
    else:
        # Default sort by creation time if not by priority
        tasks_to_return.sort(key=lambda t: t["created_at"])

    print(
        f"[{datetime.datetime.utcnow().isoformat()}] INFO: Returning {len(tasks_to_return)} tasks."
    )
    return tasks_to_return


if __name__ == "__main__":
    print("--- To-Do List Manager Demo ---")

    # Add some tasks
    print("\n1. Adding tasks:")
    task1 = add_task(
        "Administer morning medications for Patient A (Room 301)",
        "High",
        patient_id="PatientA_Room301",
    )
    task2 = add_task(
        "Follow up on pending lab results for Patient B (Room 302)",
        "Urgent",
        patient_id="PatientB_Room302",
    )
    task3 = add_task(
        "Restock isolation cart in Room 301", "Medium", patient_id="general_unit"
    )  # General unit task
    task4 = add_task(
        "Complete shift handoff report documentation",
        "High",
        patient_id="general_reporting",
    )
    task5 = add_task(
        "Check IV site for Patient A (Room 301)",
        "Medium",
        patient_id="PatientA_Room301",
    )
    task_low = add_task(
        "Review new unit protocols (non-urgent)", "Low", patient_id="general_unit"
    )

    print("\n2. Listing all tasks (sorted by priority and status):")
    all_tasks_sorted = get_all_tasks()  # Gets all tasks (general and patient-specific)
    for task in all_tasks_sorted:
        print(
            f"  - [{task['status']}] {task['description']} (Priority: {task['priority']}, Patient: {task.get('patient_id', 'N/A')})"
        )

    print("\n3. Listing tasks for Patient A (Room 301):")
    patient_a_tasks = get_all_tasks(patient_id_filter="PatientA_Room301")
    for task in patient_a_tasks:
        print(
            f"  - [{task['status']}] {task['description']} (Priority: {task['priority']})"
        )

    print("\n4. Updating task status (task2 to 'Completed'):")
    if task2:
        updated_task2 = update_task_status(task2["task_id"], "Completed")
        if updated_task2:
            print(
                f"  Task '{updated_task2['description']}' is now '{updated_task2['status']}'."
            )

    print("\n5. Updating task status (task_low to 'Completed'):")
    if task_low:
        updated_task_low = update_task_status(task_low["task_id"], "Completed")

    print(
        "\n6. Listing all tasks again (notice completed tasks are typically at the bottom or styled differently):"
    )
    all_tasks_after_update = get_all_tasks()
    for task in all_tasks_after_update:
        print(
            f"  - [{task['status']}] {task['description']} (Priority: {task['priority']}, Patient: {task.get('patient_id')})"
        )

    print("\n7. Get a specific task (task1):")
    specific_task = get_task(task1["task_id"])
    if specific_task:
        print(
            f"  Found task: {specific_task['description']}, Status: {specific_task['status']}"
        )

    print("\n8. Try to update with invalid status:")
    update_task_status(
        task1["task_id"], "InProgress"
    )  # This is an invalid status as per current VALID_STATUSES

    print("\n--- Demo Completed ---")
