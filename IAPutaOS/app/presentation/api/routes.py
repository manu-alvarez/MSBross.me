import uuid
import aiofiles
import logging
from fastapi import APIRouter, File, UploadFile, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings, APP_PREFIX
from app.application.use_cases.chat_use_case import ChatUseCase
from app.infrastructure.llm.groq_adapter import GroqAdapter
from app.infrastructure.audio.tts_stt_adapter import GroqEdgeAudioAdapter
from app.application.use_cases.memory_service import clear_history
from app.domain.entities import AIResponse
from app.infrastructure.tools.toolbox import analyze_vision_image

logger = logging.getLogger(__name__)

router = APIRouter()

def get_chat_usecase() -> ChatUseCase:
    llm_port = GroqAdapter()
    audio_port = GroqEdgeAudioAdapter()
    return ChatUseCase(llm_adapter=llm_port, audio_adapter=audio_port)

def get_audio_adapter() -> GroqEdgeAudioAdapter:
    return GroqEdgeAudioAdapter()

def _verify_api_key(request: Request):
    expected = settings.IAPUTA_API_KEY
    if not expected:
        return
    
    # Nginx and some browsers lowercase headers. We should check both.
    incoming_key = request.headers.get("x-api-key") or request.headers.get("X-API-KEY")
    
    if incoming_key != expected:
        logger.warning(f"AUTH FAILED: Expected {expected}, got {incoming_key}")
        raise HTTPException(status_code=401, detail="API key inválida o ausente.")

class TextCommandRequest(BaseModel):
    text: str

class VisionAnalyzeRequest(BaseModel):
    image: str
    source: str = "screenshot"
    prompt: str = None

@router.post("/api/voice-command", response_model=AIResponse)
async def voice_command_endpoint(request: Request, audio_file: UploadFile = File(...), chat_usecase: ChatUseCase = Depends(get_chat_usecase)):
    _verify_api_key(request)
    try:
        content = await audio_file.read()
        if len(content) == 0:
            return JSONResponse(status_code=400, content={"error": "El archivo de audio está vacío."})

        ext = "mp4" if audio_file.content_type and "mp4" in audio_file.content_type else "webm"
        temp_in = f"{APP_PREFIX}/temp_audio/in_{uuid.uuid4().hex[:6]}.{ext}"
        
        async with aiofiles.open(temp_in, "wb") as f:
            await f.write(content)

        res = await chat_usecase.execute_voice(temp_in)
        return res.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in voice-command")
        return JSONResponse(status_code=500, content={"transcript": "Error de audio", "error": str(e), "emotion": "error"})

@router.post("/api/text-command", response_model=AIResponse)
async def text_command_endpoint(request: Request, body: TextCommandRequest, chat_usecase: ChatUseCase = Depends(get_chat_usecase)):
    _verify_api_key(request)
    try:
        res = await chat_usecase.execute_text(body.text)
        return res.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in text-command")
        return JSONResponse(status_code=500, content={"transcript": "Error interceptado", "error": str(e), "emotion": "error"})

@router.post("/api/vision-analyze")
async def vision_analyze_endpoint(request: Request, body: VisionAnalyzeRequest, audio_adapter: GroqEdgeAudioAdapter = Depends(get_audio_adapter)):
    _verify_api_key(request)
    try:
        analysis, vision_url = await analyze_vision_image(body.image, body.prompt, body.source)
        audio_url = None
        try:
            audio_url = await audio_adapter.generate_speech(analysis)
        except Exception as tts_err:
            logger.warning(f"TTS failed: {tts_err}")

        return {"response": analysis, "vision_url": vision_url, "audio_url": audio_url, "emotion": "thinking", "source": body.source}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in vision-analyze")
        return JSONResponse(status_code=500, content={"response": f"Error visión: {e}", "emotion": "error"})

@router.post("/api/clear-memory")
async def clear_memory_endpoint(request: Request):
    _verify_api_key(request)
    clear_history()
    return {"status": "success", "message": "Memoria purgada limpiamente."}

@router.get("/api/status")
async def status_endpoint():
    return {"status": "online"}
