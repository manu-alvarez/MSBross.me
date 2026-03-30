"""
Task Management API Routes
Handles CRUD operations for tasks with SQLite persistence
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import json
import database as db

router = APIRouter()

# Pydantic Models
class TaskBase(BaseModel):
    title: str
    description: str = ""
    deadline: Optional[str] = None
    priority: str = "Medium"
    dependencies: List[str] = []
    recurring: bool = False
    recurring_interval: str = "Daily"

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None
    dependencies: Optional[List[str]] = None
    recurring: Optional[bool] = None
    recurring_interval: Optional[str] = None
    completed: Optional[bool] = None

class Task(TaskBase):
    id: str
    created_at: str
    completed: bool = False


@router.on_event("startup")
async def startup():
    """Initialize database on startup"""
    await db.init_db()


@router.post("/", response_model=Task, status_code=201)
async def create_task(task: TaskCreate):
    """Create a new task"""
    task_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    
    task_dict = {
        "id": task_id,
        "title": task.title,
        "description": task.description,
        "deadline": task.deadline,
        "priority": task.priority,
        "dependencies": json.dumps(task.dependencies),
        "recurring": task.recurring,
        "recurring_interval": task.recurring_interval,
        "created_at": created_at,
        "completed": False
    }
    
    await db.create_task(task_dict)
    
    return Task(
        id=task_id,
        title=task.title,
        description=task.description,
        deadline=task.deadline,
        priority=task.priority,
        dependencies=task.dependencies,
        recurring=task.recurring,
        recurring_interval=task.recurring_interval,
        created_at=created_at,
        completed=False
    )


@router.get("/", response_model=List[Task])
async def get_tasks():
    """Get all tasks"""
    tasks = await db.get_all_tasks()
    return [
        Task(
            id=t["id"],
            title=t["title"],
            description=t["description"] or "",
            deadline=t["deadline"],
            priority=t["priority"],
            dependencies=json.loads(t["dependencies"]) if t["dependencies"] else [],
            recurring=bool(t["recurring"]),
            recurring_interval=t["recurring_interval"],
            created_at=t["created_at"],
            completed=bool(t["completed"])
        )
        for t in tasks
    ]


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """Get a specific task"""
    task = await db.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return Task(
        id=task["id"],
        title=task["title"],
        description=task["description"] or "",
        deadline=task["deadline"],
        priority=task["priority"],
        dependencies=json.loads(task["dependencies"]) if task["dependencies"] else [],
        recurring=bool(task["recurring"]),
        recurring_interval=task["recurring_interval"],
        created_at=task["created_at"],
        completed=bool(task["completed"])
    )


@router.patch("/{task_id}", response_model=Task)
async def update_task(task_id: str, updates: TaskUpdate):
    """Update a task"""
    existing = await db.get_task_by_id(task_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_dict = updates.dict(exclude_unset=True)
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No valid updates provided")
    
    updated = await db.update_task(task_id, update_dict)
    
    return Task(
        id=updated["id"],
        title=updated["title"],
        description=updated["description"] or "",
        deadline=updated["deadline"],
        priority=updated["priority"],
        dependencies=json.loads(updated["dependencies"]) if updated["dependencies"] else [],
        recurring=bool(updated["recurring"]),
        recurring_interval=updated["recurring_interval"],
        created_at=updated["created_at"],
        completed=bool(updated["completed"])
    )


@router.put("/{task_id}/toggle", response_model=Task)
async def toggle_task_completion(task_id: str):
    """Toggle task completion status"""
    task = await db.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    new_status = not bool(task["completed"])
    updated = await db.update_task(task_id, {"completed": new_status})
    
    return Task(
        id=updated["id"],
        title=updated["title"],
        description=updated["description"] or "",
        deadline=updated["deadline"],
        priority=updated["priority"],
        dependencies=json.loads(updated["dependencies"]) if updated["dependencies"] else [],
        recurring=bool(updated["recurring"]),
        recurring_interval=updated["recurring_interval"],
        created_at=updated["created_at"],
        completed=bool(updated["completed"])
    )


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    task = await db.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete_task(task_id)
    return {"message": "Task deleted successfully", "task_id": task_id}


@router.get("/stats/summary")
async def get_task_stats():
    """Get task statistics"""
    tasks = await db.get_all_tasks()
    timer_stats = await db.get_timer_stats()
    
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("completed"))
    pending = total - completed
    high_priority = sum(1 for t in tasks if t.get("priority") == "High" and not t.get("completed"))
    
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": pending,
        "high_priority": high_priority,
        "completion_rate": round((completed / total * 100), 1) if total > 0 else 0,
        "timer_stats": timer_stats
    }