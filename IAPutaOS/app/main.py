import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from app.core.config import settings
from app.presentation.api.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tareas en segundo plano
from app.infrastructure.tools.telegram_tool import telegram_polling_loop
from app.application.use_cases.memory_service import cleanup_task

background_tasks = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.TELEGRAM_BOT_TOKEN:
        logger.info("Iniciando Telegram polling...")
        tg_task = asyncio.create_task(telegram_polling_loop())
        background_tasks.add(tg_task)
        tg_task.add_done_callback(background_tasks.discard)

    logger.info("Iniciando tarea de limpieza de memoria (10m idle)...")
    clean_task = asyncio.create_task(cleanup_task(idle_minutes=10))
    background_tasks.add(clean_task)
    clean_task.add_done_callback(background_tasks.discard)

    yield

    logger.info("Apagando tareas en segundo plano...")
    for t in background_tasks:
        t.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)

app = FastAPI(title="IAPuta OS Core API", lifespan=lifespan)

# CORS DEFINITIVE FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False
    )
