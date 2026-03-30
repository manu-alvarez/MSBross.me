"""
Timer Service - Background task timing with alerts
Manages Pomodoro-style timers for tasks
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import asyncio
import threading
import time
import uuid
import database as db

router = APIRouter()

# Timer Configuration Model
class TimerConfig(BaseModel):
    task_id: str
    duration_minutes: int
    alert_minutes: List[int] = [5, 1]
    enabled_notifications: bool = True
    recurring: bool = False


# Global timer state (in production, use Redis)
class TimerState:
    """Singleton to track timer state across requests"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.running = False
        self.current_task_id: Optional[str] = None
        self.current_config: Optional[TimerConfig] = None
        self.progress: float = 0.0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._stop_event = threading.Event()
        self._current_thread: Optional[threading.Thread] = None
        self._log_id: Optional[int] = None
    
    def reset(self):
        """Reset timer state"""
        self.running = False
        self.current_task_id = None
        self.current_config = None
        self.progress = 0.0
        self.start_time = None
        self.end_time = None
        self._log_id = None


# Global timer state instance
timer_state = TimerState()


def send_notification(title: str, message: str):
    """Send notification (console for now, can be expanded to push)"""
    print(f"[NOTIFICATION] {title}: {message}")


def run_timer_background(config: TimerConfig, task_id: str, log_id: int):
    """Background thread function to run the timer"""
    total_seconds = config.duration_minutes * 60
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=total_seconds)
    
    timer_state.start_time = start_time
    timer_state.end_time = end_time
    timer_state.running = True
    timer_state.current_task_id = task_id
    timer_state.current_config = config
    timer_state._log_id = log_id
    
    print(f"[TIMER] Started for task {task_id} - {config.duration_minutes} minutes")
    
    # Timer loop
    for remaining in range(total_seconds, 0, -1):
        if timer_state._stop_event.is_set():
            print(f"[TIMER] Stopped for task {task_id}")
            timer_state.reset()
            return
        
        # Calculate progress
        elapsed = datetime.now() - start_time
        progress = (elapsed.total_seconds() / total_seconds) * 100
        timer_state.progress = round(progress, 1)
        
        # Check for alerts
        for alert_min in config.alert_minutes:
            alert_threshold = end_time - timedelta(minutes=alert_min)
            if datetime.now() >= alert_threshold and remaining == alert_min * 60:
                send_notification(
                    f"Tarea en progreso: {task_id[:8]}...",
                    f"¡Faltan {alert_min} minuto(s)!"
                )
        
        time.sleep(1)
    
    # Timer completed
    send_notification(
        "¡Tiempo completado!",
        f"El temporizador de {config.duration_minutes} min ha terminado"
    )
    
    # Mark timer session as completed
    if log_id:
        asyncio.run(db.complete_timer_session(log_id))
    
    timer_state.reset()
    print(f"[TIMER] Completed for task {task_id}")


@router.post("/start")
async def start_timer(config: TimerConfig):
    """Start a new timer for a task"""
    # Check if a timer is already running
    if timer_state.running:
        raise HTTPException(
            status_code=400,
            detail="A timer is already running. Stop it first."
        )
    
    # Validate task exists
    task = await db.get_task_by_id(config.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Stop any previous stop event
    timer_state._stop_event.clear()
    
    # Log timer session
    log_id = await db.log_timer_session(config.task_id, config.duration_minutes)
    
    # Start timer in background thread
    thread = threading.Thread(
        target=run_timer_background,
        args=(config, config.task_id, log_id),
        daemon=True
    )
    timer_state._current_thread = thread
    thread.start()
    
    return {
        "status": "started",
        "task_id": config.task_id,
        "duration_minutes": config.duration_minutes,
        "end_time": (datetime.now() + timedelta(minutes=config.duration_minutes)).isoformat()
    }


@router.get("/status")
async def get_timer_status():
    """Get current timer status"""
    if not timer_state.running:
        return {
            "running": False,
            "current_task": None,
            "progress": 0,
            "remaining_seconds": 0
        }
    
    # Calculate remaining time
    remaining = 0
    if timer_state.end_time:
        remaining = max(0, int((timer_state.end_time - datetime.now()).total_seconds()))
    
    return {
        "running": timer_state.running,
        "current_task": timer_state.current_task_id,
        "progress": timer_state.progress,
        "remaining_seconds": remaining,
        "start_time": timer_state.start_time.isoformat() if timer_state.start_time else None,
        "end_time": timer_state.end_time.isoformat() if timer_state.end_time else None
    }


@router.post("/stop")
async def stop_timer():
    """Stop the current running timer"""
    if not timer_state.running:
        raise HTTPException(status_code=400, detail="No active timer to stop")
    
    # Signal the thread to stop
    timer_state._stop_event.set()
    
    # Wait for thread to finish (with timeout)
    if timer_state._current_thread:
        timer_state._current_thread.join(timeout=2)
    
    send_notification("Temporizador detenido", "El temporizador ha sido cancelado")
    
    return {"status": "stopped", "previous_task": timer_state.current_task_id}


@router.get("/stats")
async def get_timer_stats():
    """Get timer usage statistics"""
    return await db.get_timer_stats()