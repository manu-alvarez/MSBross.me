"""
DOHLER Task Manager - Main Application
FastAPI backend with SQLite database
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from routes import tasks as tasks_router
from services import timer as timer_router

# Database initialization
import database as db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """lifespan handler for startup and shutdown"""
    # Startup: initialize database
    await db.init_db()
    print("[STARTUP] Database initialized")
    yield
    # Shutdown: cleanup if needed
    print("[SHUTDOWN] Application stopping")


# Create FastAPI app
app = FastAPI(
    title="DOHLER Task Manager API",
    description="Intelligent task management with timers",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks_router.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(timer_router.router, prefix="/api/timer", tags=["timer"])


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "DOHLER Task Manager API",
        "version": "1.0.0",
        "status": "running",
    }


# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True, log_level="info")
