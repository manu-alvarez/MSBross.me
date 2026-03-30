import uuid
import re
import os
import edge_tts
from app.core.groq_client import groq_client
from app.application.interfaces.ai_port import AudioPort


def _clean_for_tts(text: str) -> str:
    """Elimina TODO el ruido visual/técnico antes de convertir a voz."""
    # 1. Bloques de código markdown (```...```)
    text = re.sub(r'```[\s\S]*?```', '', text)
    # 2. Bloques XML (<tag>...</tag>)
    text = re.sub(r'<[a-zA-Z0-9_]+[^>]*>[\s\S]*?</[a-zA-Z0-9_]+>', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    # 3. JSON suelto ({...})
    text = re.sub(r'\{[^{}]*\}', '', text)
    # 4. Tags tipo [NEUTRAL] o [EMOTION: happy]
    text = re.sub(r'\[[A-Z_]+[^\]]*\]', '', text)
    # 5. Código inline (`...`)
    text = re.sub(r'`[^`]+`', '', text)
    # 6. URLs
    text = re.sub(r'https?://\S+', '', text)
    # 7. ⚡ MARKDOWN ASTERISCOS ⚡ — esto es lo que se leía en voz alta
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)  # **bold**, *italic*, ***both***
    text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)     # __bold__, _italic_
    # 8. Headers markdown (# ## ### etc)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # 9. Bullet points y listas
    text = re.sub(r'^\s*[-•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    # 10. Emojis (la mayoría de rangos unicode)
    text = re.sub(r'[\U0001F300-\U0001FAD6\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\u2600-\u26FF\u2700-\u27BF\u2B50\u23F0-\u23FA\u200D\uFE0F]', '', text)
    # 11. Líneas decorativas (--- === ***)
    text = re.sub(r'^[\-=_*]{3,}$', '', text, flags=re.MULTILINE)
    # 12. Asteriscos sueltos que queden
    text = text.replace('*', '')
    # 13. Colapsar espacios y saltos
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()
    # 14. Limitar a 1200 chars (antes era 600, cortaba demasiado)
    if len(text) > 1200:
        # Cortar en el último punto/frase para no dejar a medias
        cut = text[:1200]
        last_period = max(cut.rfind('.'), cut.rfind('!'), cut.rfind('?'))
        if last_period > 600:
            text = cut[:last_period + 1]
        else:
            text = cut + "..."
    return text


class GroqEdgeAudioAdapter(AudioPort):
    def __init__(self):
        self.groq_client = groq_client
        
    async def transcribe(self, audio_path: str) -> str:
        """STT via Whisper asíncrono"""
        with open(audio_path, "rb") as f:
            transcription = await self.groq_client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), f.read()), 
                model="whisper-large-v3", 
                response_format="text"
            )
        return transcription

    async def generate_speech(self, text: str) -> str:
        """TTS asíncrono via Edge-TTS — filtra código y ruido antes de hablar."""
        clean_text = _clean_for_tts(text)
        if not clean_text:
            clean_text = "Listo."
        temp_out = f"temp_audio/out_{uuid.uuid4().hex[:6]}.mp3"
        communicate = edge_tts.Communicate(clean_text, "es-ES-AlvaroNeural", rate="+25%")
        await communicate.save(temp_out)
        return f"/{temp_out}"
