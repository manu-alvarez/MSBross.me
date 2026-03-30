"""
MSB LiveKit Voice Assistant — Provider Factory

Factory for creating LLM, STT, TTS instances dynamically.
Supports multiple providers: Gemini, Ollama, OpenAI, Kokoro, Faster-Whisper.
"""

import json
import logging
import os
from typing import Optional, AsyncIterable, AsyncIterator
import asyncio
import httpx

from livekit.agents import stt, tts, utils, APIConnectOptions

logger = logging.getLogger("msb-assistant")


class NotImplementedSTT(stt.STT):
    """A placeholder for STT providers that are not fully implemented."""
    def __init__(self, provider: str):
        super().__init__(
            capabilities=stt.STTCapabilities(streaming=False, interim_results=False)
        )
        self._provider = provider

    async def _recognize_impl(
        self, 
        buffer: utils.AudioBuffer, 
        *, 
        language: Optional[str] = None
    ) -> stt.SpeechEvent:
        logger.error(f"STT provider '{self._provider}' is not implemented.")
        return stt.SpeechEvent(type=stt.SpeechEventType.ERROR, alternates=[])


class ProviderFactory:
    """Factory for creating LLM, STT, TTS instances based on configuration."""
    
    @staticmethod
    def create_llm(
        provider: str,
        model: str,
        base_url: Optional[str] = None,
        temperature: float = 0.7
    ):
        logger.info(f"Creating LLM: provider={provider}, model={model}")
        
        if provider == "gemini":
            from livekit.plugins.google import LLM as GeminiLLM
            return GeminiLLM(model=model, temperature=temperature)
        
        elif provider == "ollama":
            from livekit.plugins import openai as lk_openai
            # Try to use provided base_url, fallback to env or default
            url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            # Ensure URL ends with /v1 for OpenAI-compatible API
            if url and not url.rstrip("/").endswith("/v1"):
                url = url.rstrip("/") + "/v1"
            logger.info(f"Ollama LLM base_url: {url}")
            return lk_openai.LLM.with_ollama(
                model=model,
                base_url=url,
                temperature=temperature
            )
        
        elif provider == "openai":
            from livekit.plugins import openai as lk_openai
            return lk_openai.LLM(model=model, temperature=temperature)
        
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    @staticmethod
    def create_stt(
        provider: str,
        model: str = "small",
        language: str = "es"
    ):
        logger.info(f"Creating STT: provider={provider}, model={model}, language={language}")
        
        google_available = bool(os.getenv("GOOGLE_API_KEY"))

        if provider == "google-stt":
            from livekit.plugins.google import STT as GoogleSTT
            return GoogleSTT(languages=[language])
        
        elif provider == "faster-whisper":
            return FasterWhisperSTTWrapper(
                base_url=os.getenv("FASTER_WHISPER_URL", "http://localhost:9000"),
                model=model,
                language=language,
            )
        

        
        elif provider == "openai":
            from livekit.plugins import openai as lk_openai
            return lk_openai.STT()
        
        else:
            logger.error(f"No viable STT provider found for '{provider}'. Using NotImplemented placeholder.")
            return NotImplementedSTT(provider=provider)
    
    @staticmethod
    def create_tts(
        provider: str,
        voice: str,
        server_url: Optional[str] = None,
        speed: float = 1.0
    ):
        logger.info(f"Creating TTS: provider={provider}, voice={voice}")
        
        google_available = bool(os.getenv("GOOGLE_API_KEY"))

        if provider == "google-tts":
            from livekit.plugins.google import TTS as GoogleTTS
            return GoogleTTS(voice=voice if "-" in voice else "es-ES-Standard-A")
        
        elif provider == "kokoro":
            return KokoroTTSWrapper(
                base_url=server_url or "http://localhost:8001",
                voice=voice,
                speed=speed
            )
        

        
        elif provider == "openai":
            from livekit.plugins import openai as lk_openai
            return lk_openai.TTS(voice=voice, speed=speed)
        
        else:
            raise ValueError(f"Unknown TTS provider: {provider}")




class FasterWhisperSTTWrapper(stt.STT):
    """Wrapper for Faster-Whisper server (OpenAI-compatible API) for LiveKit 1.4.3."""

    def __init__(self, base_url: str, model: str = "medium", language: str = "es"):
        super().__init__(
            capabilities=stt.STTCapabilities(streaming=False, interim_results=False)
        )
        self.base_url = base_url.rstrip("/")
        self._fw_model = model
        self.language = language
        logger.info(f"FasterWhisperSTT initialized: {self.base_url}, model={model}, language={language}")

    async def _recognize_impl(
        self,
        buffer: utils.AudioBuffer,
        *,
        language: Optional[str] = None,
        **kwargs,
    ) -> stt.SpeechEvent:
        import io
        import wave
        import struct

        lang = language or self.language

        try:
            # Convert AudioBuffer frames to WAV bytes
            frames = buffer if isinstance(buffer, (list, tuple)) else [buffer]
            pcm_data = b""
            sample_rate = 16000
            num_channels = 1

            for frame in frames:
                if hasattr(frame, "data"):
                    pcm_data += bytes(frame.data)
                    if hasattr(frame, "sample_rate"):
                        sample_rate = frame.sample_rate
                    if hasattr(frame, "num_channels"):
                        num_channels = frame.num_channels
                else:
                    pcm_data += bytes(frame)

            # Build WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(num_channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(pcm_data)
            wav_buffer.seek(0)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/audio/transcriptions",
                    files={"file": ("audio.wav", wav_buffer, "audio/wav")},
                    data={
                        "model": self._fw_model,
                        "language": lang,
                        "response_format": "json",
                    },
                )
                response.raise_for_status()
                result = response.json()
                text = result.get("text", "").strip()

                return stt.SpeechEvent(
                    type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                    alternatives=[stt.SpeechData(text=text, language=lang)]
                )

        except Exception as e:
            logger.error(f"FasterWhisper STT failed: {e}")
            return stt.SpeechEvent(
                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                alternatives=[stt.SpeechData(text="", language=lang)]
            )


class KokoroStream(tts.ChunkedStream):
    """Async stream for Kokoro audio chunks."""
    
    def __init__(self, tts_instance: 'KokoroTTSWrapper', text: str, conn_options: APIConnectOptions):
        super().__init__(tts=tts_instance, input_text=text, conn_options=conn_options)
        self._text = text
        self._tts = tts_instance

    async def _run(self) -> None:
        try:
            try:
                import av
                import io
                import numpy as np
                import httpx
            except ImportError:
                logger.error("Missing dependencies for Kokoro TTS. Run: pip install av numpy httpx")
                self._event_ch.send_nowait(tts.SynthesizedAudio(
                    text=self._text,
                    data=b"",
                    sample_rate=self._tts.sample_rate
                ))
                return

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._tts.base_url}/v1/audio/speech",
                    json={
                        "input": self._text,
                        "voice": self._tts.voice,
                        "speed": self._tts.speed
                    }
                )
                response.raise_for_status()

                # Decode MP3 response to raw PCM int16 for LiveKit
                audio_bytes = response.content
                container = av.open(io.BytesIO(audio_bytes))
                pcm_data = b""
                target_rate = self._tts.sample_rate

                for frame in container.decode(audio=0):
                    frame_resampled = frame.to_ndarray(format="s16", layout="mono")
                    if frame.sample_rate != target_rate:
                        samples = frame_resampled.flatten()
                        ratio = target_rate / frame.sample_rate
                        new_len = int(len(samples) * ratio)
                        indices = np.linspace(0, len(samples) - 1, new_len).astype(int)
                        resampled = samples[indices]
                        pcm_data += resampled.astype(np.int16).tobytes()
                    else:
                        pcm_data += frame_resampled.tobytes()

                container.close()

                self._event_ch.send_nowait(tts.SynthesizedAudio(
                    text=self._text,
                    data=pcm_data,
                    sample_rate=target_rate
                ))
        except Exception as e:
            logger.error(f"Kokoro TTS stream failed: {e}", exc_info=True)
            self._event_ch.send_nowait(tts.SynthesizedAudio(
                text=self._text,
                data=b"",
                sample_rate=self._tts.sample_rate
            ))
        finally:
            self._event_ch.close()


class KokoroTTSWrapper(tts.TTS):
    """Wrapper for Kokoro TTS via FastAPI server for LiveKit 1.4.3."""
    
    def __init__(self, base_url: str, voice: str, speed: float = 1.0):
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=24000,
            num_channels=1
        )
        self.base_url = base_url.rstrip("/")
        self.voice = voice
        self.speed = speed
        logger.info(f"KokoroTTS initialized: {self.base_url}, voice={voice}, speed={speed}")
    
    def synthesize(
        self, 
        text: str, 
        *, 
        conn_options: Optional[APIConnectOptions] = None
    ) -> tts.ChunkedStream:
        return KokoroStream(
            tts_instance=self, 
            text=text, 
            conn_options=conn_options or APIConnectOptions()
        )




async def check_provider_status() -> dict:
    """Check availability status of all providers."""
    status = {
        "ollama": {"available": False, "url": "http://localhost:11434", "models": []},
        "kokoro": {"available": False, "url": "http://localhost:8001"},
        "faster-whisper": {"available": False, "url": "http://localhost:9000"},
        "gemini": {"available": bool(os.getenv("GOOGLE_API_KEY")), "note": "API key required"},
    }
    
    async with httpx.AsyncClient(timeout=3.0) as client:
        # Ollama
        try:
            resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code == 200:
                status["ollama"]["available"] = True
                data = resp.json()
                status["ollama"]["models"] = [m["name"] for m in data.get("models", [])]
        except:
            pass
        
        # Kokoro TTS
        try:
            resp = await client.get("http://localhost:8001/v1/models")
            if resp.status_code == 200:
                status["kokoro"]["available"] = True
        except:
            pass

        # Faster-Whisper STT
        try:
            resp = await client.get("http://localhost:9000/")
            if resp.status_code == 200:
                status["faster-whisper"]["available"] = True
        except:
            pass
    
    return status

