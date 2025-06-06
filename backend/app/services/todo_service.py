from google.cloud.firestore_async import AsyncClient
from google.cloud.firestore import Query, AsyncWriteBatch
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid # For todo_id if not using Firestore auto-generated IDs for some reason (though we will)

from backend.app.models.firestore_models import Todo, TodoCreate, TodoUpdate, TodoPriority, TodoStatus

# Firestore client (similar to firestore_service.py, consider shared client via DI in real app)
db = AsyncClient()
TODOS_COLLECTION = "todos"

def utcnow():
    return datetime.now(timezone.utc)

# For sorting if done in Python (Firestore can also order)
# Higher number = higher priority
PRIORITY_ORDER_MAP = {
    TodoPriority.URGENT: 4,
    TodoPriority.HIGH: 3,
    TodoPriority.MEDIUM: 2,
    TodoPriority.LOW: 1
}

async def create_todo(todo_data: TodoCreate) -> Todo:
    """Creates a new To-Do item in Firestore."""
    doc_ref = db.collection(TODOS_COLLECTION).document() # Firestore auto-generated ID
    current_time = utcnow()

    todo_doc_data = todo_data.model_dump(exclude_unset=True)
    todo_doc_data["created_at"] = current_time
    todo_doc_data["updated_at"] = current_time
    # Ensure enum values are stored if model_config use_enum_values=True is set,
    # otherwise .value might be needed depending on Pydantic version and exact setup.
    # Pydantic v2 with use_enum_values=True should store the enum's value.

    await doc_ref.set(todo_doc_data)

    # Construct the Todo object for return
    return Todo(todo_id=doc_ref.id, **todo_doc_data)

async def get_todo(todo_id: str) -> Optional[Todo]:
    """Retrieves a specific To-Do item by its ID."""
    doc_ref = db.collection(TODOS_COLLECTION).document(todo_id)
    snapshot = await doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        return Todo(todo_id=snapshot.id, **data)
    return None

async def update_todo(todo_id: str, todo_update_data: TodoUpdate) -> Optional[Todo]:
    """Updates an existing To-Do item in Firestore."""
    doc_ref = db.collection(TODOS_COLLECTION).document(todo_id)

    update_data = todo_update_data.model_dump(exclude_unset=True)
    if not update_data: # No fields to update
        return await get_todo(todo_id) # Return current state

    update_data["updated_at"] = utcnow()

    # Ensure document exists before update if strict update is needed
    # current_doc = await doc_ref.get()
    # if not current_doc.exists:
    #     return None # Or raise error

    await doc_ref.update(update_data)

    updated_snapshot = await doc_ref.get()
    if updated_snapshot.exists:
        return Todo(todo_id=updated_snapshot.id, **updated_snapshot.to_dict())
    return None # Should ideally not happen if update was on existing doc

async def delete_todo(todo_id: str) -> bool:
    """Deletes a To-Do item from Firestore."""
    doc_ref = db.collection(TODOS_COLLECTION).document(todo_id)
    await doc_ref.delete()
    # Check deletion if necessary:
    # snapshot = await doc_ref.get()
    # return not snapshot.exists
    return True # Assume success for now

async def list_todos(
    patient_id_filter: Optional[str] = None,
    status_filter: Optional[TodoStatus] = None, # New filter option
    sort_by_priority: bool = True # Original script sorted by status then priority
) -> List[Todo]:
    """
    Lists To-Do items, with optional filtering by patient_id and status.
    Sorts by status ("Pending" first) then by priority (descending) if sort_by_priority is True.
    """
    query = db.collection(TODOS_COLLECTION)

    # Apply filters
    # For patient_id, original script included "general" tasks along with patient-specific ones.
    # This is harder with Firestore queries directly unless we do two queries and merge,
    # or denormalize/add a field like "is_general_task".
    # For now, if patient_id_filter is provided, we filter by that ID *or* "general".
    # This requires an OR query which Firestore supports via `OR` operator on different fields or `IN` on the same field.
    # A simpler approach for now for this subtask: if patient_id_filter, query for that specific ID.
    # The "general" task inclusion can be a TODO or handled by client making two calls.
    # Let's stick to simpler filter for now:
    if patient_id_filter:
        # This query will find tasks for specific patient OR general tasks.
        # Firestore requires composite index for this kind of query if patient_id and other fields are involved in where/orderBy.
        # For simplicity, let's assume we want tasks FOR that patient OR tasks that are general.
        # This is complex with Firestore. A common pattern is to have a field like 'associated_entities' (array)
        # and query array_contains 'patient_id_filter' OR array_contains 'general'.
        # Or, fetch all and filter in Python if dataset is small.
        # For now, let's implement patient_id_filter to mean "only for this patient" OR "only general tasks"
        # and not a combination unless patient_id_filter *is* "general".
         query = query.where("patient_id", "==", patient_id_filter)


    if status_filter:
        query = query.where("status", "==", status_filter.value) # Use .value for enum

    # Sorting: Firestore requires the first orderBy field to be the one used in inequality filters (not applicable here yet).
    # To sort by "Pending" first, then priority, is tricky with direct Firestore queries
    # unless we have a numerical sort_order field that combines these.
    # Python sort is more flexible here if data size is manageable.
    # For now, let's try basic Firestore ordering and then Python sort if needed.

    # If sorting by priority, and also by status (Pending first):
    # Option 1: Add a field to model `is_pending_numerical` (0 for pending, 1 for completed)
    # Option 2: Sort in Python after fetching.
    # Let's do Firestore sort by priority, then Python sort by status for Pending first.

    if sort_by_priority:
        # Firestore sorts Enums by their string value by default if not mapped differently.
        # We need custom sort for priority (Urgent > High > ...).
        # This means we will fetch and sort in Python for priority if complex.
        # Simple Firestore sort by 'priority' string might not be what we want.
        # Let's sort by 'updated_at' as a default for now and do complex sort in Python.
        query = query.order_by("updated_at", direction=Query.DESCENDING)
    else:
        query = query.order_by("created_at", direction=Query.ASCENDING)

    todos = []
    async for snapshot in query.stream():
        if snapshot.exists:
            data = snapshot.to_dict()
            todos.append(Todo(todo_id=snapshot.id, **data))

    # Python-side sorting for complex logic (status then priority)
    if sort_by_priority:
        todos.sort(key=lambda t: (
            t.status != TodoStatus.PENDING, # False (0) for Pending, True (1) for Completed
            -PRIORITY_ORDER_MAP.get(t.priority, 0) # Negative for descending priority
        ))

    return todos
