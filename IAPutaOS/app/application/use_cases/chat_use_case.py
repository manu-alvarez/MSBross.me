from app.domain.entities import AIResponse
from app.application.interfaces.ai_port import LLMPort, AudioPort
from app.application.use_cases.memory_service import save_message, get_recent_history

class ChatUseCase:
    def __init__(self, llm_adapter: LLMPort, audio_adapter: AudioPort = None):
        self.llm = llm_adapter
        self.audio = audio_adapter
        
    async def execute_text(self, text: str) -> AIResponse:
        save_message("user", text)
        history = get_recent_history(limit=8)
        
        final_text, v_url, emotion = await self.llm.process_chat(text, history)
        
        audio_url = None
        if self.audio:
            audio_url = await self.audio.generate_speech(final_text)
            
        save_message("assistant", final_text)
        
        return AIResponse(
            transcript=text,
            response=final_text,
            audio_url=audio_url,
            vision_url=v_url,
            emotion=emotion
        )

    async def execute_voice(self, audio_path: str) -> AIResponse:
        if not self.audio:
            raise ValueError("Audio adapter not provided.")
            
        ts = await self.audio.transcribe(audio_path)
        return await self.execute_text(ts)
