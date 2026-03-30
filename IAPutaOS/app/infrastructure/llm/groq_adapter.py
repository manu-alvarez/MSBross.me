"""
Groq LLM Adapter — implements LLMPort using the centralized Groq client.
Includes retry with exponential backoff, automatic fallback to smaller model,
and OpenRouter as final fallback provider.
"""

import re
import asyncio
import logging
from typing import Tuple, Optional

import httpx

from app.core.groq_client import groq_client
from app.core.config import settings
from app.core.prompts import SYSTEM_PROMPT
from app.application.interfaces.ai_port import LLMPort
from app.infrastructure.tools.toolbox import TOOLS_SCHEMA
from app.application.use_cases.tool_dispatcher import handle_tool_call

logger = logging.getLogger(__name__)

PRIMARY_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "qwen/qwen3-32b"
MAX_RETRIES = 3
MAX_TOOL_ITERATIONS = 5

# Ollama local models (priority order — best → fastest)
OLLAMA_MODELS = [
    "glm-4.7-flash:latest",          # 19GB — best quality, fully local
    "manoelectricaazul/llama-3-lexi-uncensored:8b",  # 4.9GB — uncensored, versatile
    "llama3.2:3b",                   # 2GB — fast fallback
]
OLLAMA_BASE_URL = "http://localhost:11434"

# OpenRouter models (used when Groq is completely unavailable)
OPENROUTER_MODELS = [
    "meta-llama/llama-3.3-70b-instruct",
    "qwen/qwen-2.5-72b-instruct",
]

async def _call_openrouter(messages: list, model: str = None) -> dict:
    """
    Calls OpenRouter API as final fallback when Groq is unavailable.
    Rotates through available API keys on failure.
    """
    keys = [k for k in [
        settings.OPENROUTER_API_KEY,
        getattr(settings, 'OPENROUTER_API_KEY_2', None),
        getattr(settings, 'OPENROUTER_API_KEY_3', None),
    ] if k]

    if not keys:
        raise RuntimeError("No OpenRouter API keys configured")

    model = model or OPENROUTER_MODELS[0]

    for key in keys:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": 2048,
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"].get("content", "")
                    return content
                else:
                    logger.warning(f"OpenRouter key failed ({resp.status_code}), trying next key...")
                    continue
        except Exception as e:
            logger.warning(f"OpenRouter call failed: {e}")
            continue

    raise RuntimeError("All OpenRouter keys exhausted")


async def _call_ollama(messages: list, model: str = None) -> str:
    """
    Calls local Ollama API as secondary fallback (before OpenRouter).
    Zero rate limits, fully private. Requires Ollama running on localhost:11434.
    """
    model = model or OLLAMA_MODELS[0]
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # Build the OpenAI-compatible Ollama endpoint
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 1024,
                    "stream": False,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"].get("content", "")
            else:
                logger.warning(f"Ollama error ({resp.status_code}): {resp.text[:200]}")
                # Try next Ollama model
                for fallback_model in OLLAMA_MODELS[1:]:
                    if fallback_model == model:
                        continue
                    try:
                        resp2 = await client.post(
                            f"{OLLAMA_BASE_URL}/v1/chat/completions",
                            json={"model": fallback_model, "messages": messages, "max_tokens": 1024}
                        )
                        if resp2.status_code == 200:
                            return resp2.json()["choices"][0]["message"].get("content", "")
                    except Exception:
                        continue
    except Exception as e:
        logger.warning(f"Ollama unavailable: {e}")
    raise RuntimeError("Ollama unavailable or all models failed")


async def _call_groq_with_retry(messages: list, tools: list = None, model: str = PRIMARY_MODEL):
    """
    Calls Groq API with exponential backoff retry.
    Falls back to smaller model, then to OpenRouter if all else fails.
    """
    current_model = model
    for attempt in range(MAX_RETRIES):
        try:
            kwargs = {
                "model": current_model,
                "messages": messages,
                "max_tokens": 1024,
            }
            if tools and current_model == PRIMARY_MODEL:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            if tools and current_model == FALLBACK_MODEL:
                kwargs["tools"] = tools

            return await groq_client.chat.completions.create(**kwargs), current_model

        except Exception as e:
            error_msg = str(e)
            is_quota = "429" in error_msg and ("tokens" in error_msg.lower() or "limit" in error_msg.lower())
            
            if is_quota and current_model == PRIMARY_MODEL:
                logger.warning(f"Groq 70b over quota. Switching to Qwen 32b. Error: {e}")
                current_model = FALLBACK_MODEL
                continue

            if attempt < MAX_RETRIES - 1:
                wait_time = 2 ** (attempt + 1)
                logger.warning(f"Groq API Error ({current_model}, attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Groq API failed after {MAX_RETRIES} attempts: {e}")
                raise


class GroqAdapter(LLMPort):

    async def process_chat(self, user_text: str, history: list) -> Tuple[str, Optional[str], str]:
        from datetime import datetime
        now = datetime.now().strftime("%A, %d de %B de %Y, %H:%M:%S")
        
        if len(history) > 6:
            history = history[-6:]

        # --- PRE-EMPTIVE DATA INJECTION ---
        pre_injected_data = ""
        user_lower = user_text.lower()
        if any(w in user_lower for w in ["hotmail", "correo", "email", "mensajes"]):
            try:
                from app.infrastructure.tools.hotmail_tool import hotmail_executor
                hot_res, _ = await hotmail_executor('read', {'limit': 3})
                pre_injected_data = f"\n\n[DATOS REALES HOTMAIL]:\n{hot_res}"
            except Exception: pass

        dynamic_context = (
            f"\n\n[SISTEMA]: Hoy es {now}."
            "\n[DIRECTIVA]: USA DATOS REALES. SI USAS HERRAMIENTAS, ESPERA AL RESULTADO. PROHIBIDO INVENTAR."
            + pre_injected_data
        )
        
        system_msg = {"role": "system", "content": SYSTEM_PROMPT + dynamic_context}
        msgs = [system_msg] + history + [{"role": "user", "content": user_text}]

        # Fallback chain: Groq → Ollama (local) → OpenRouter (cloud)
        use_fallback = None  # None = Groq OK, 'ollama', 'openrouter'
        try:
            chat, used_model = await _call_groq_with_retry(msgs, TOOLS_SCHEMA)
        except Exception as groq_err:
            logger.warning(f"Groq unavailable: {groq_err}. Trying Ollama local...")
            use_fallback = 'ollama'

        if use_fallback:
            # Try Ollama first (local, zero rate limits)
            try:
                fallback_content = await _call_ollama(msgs)
                fallback_content = self._clean_content(fallback_content)
                fallback_content = re.sub(r'<think>.*?</think>', '', fallback_content, flags=re.DOTALL).strip()
                emotion = "neutral"
                emotion_match = re.search(r'\[EMOTION:\s*([a-zA-Z]+)\]', fallback_content)
                if emotion_match:
                    emotion = emotion_match.group(1).lower()
                    fallback_content = re.sub(r'\[EMOTION:\s*[a-zA-Z]+\]', '', fallback_content).strip()
                return fallback_content or "Procesado localmente.", None, emotion
            except Exception as ollama_err:
                logger.warning(f"Ollama also unavailable: {ollama_err}. Trying OpenRouter...")

            # OpenRouter as absolute last resort
            try:
                or_content = await _call_openrouter(msgs)
                or_content = self._clean_content(or_content)
                or_content = re.sub(r'<think>.*?</think>', '', or_content, flags=re.DOTALL).strip()
                emotion = "neutral"
                emotion_match = re.search(r'\[EMOTION:\s*([a-zA-Z]+)\]', or_content)
                if emotion_match:
                    emotion = emotion_match.group(1).lower()
                    or_content = re.sub(r'\[EMOTION:\s*[a-zA-Z]+\]', '', or_content).strip()
                return or_content or "Procesado via OpenRouter.", None, emotion
            except Exception as or_err:
                logger.error(f"All engines failed: {or_err}")
                return "Todos los motores de IA están saturados. Inténtalo en unos minutos.", None, "sad"

        msg = chat.choices[0].message
        final_text = "..."
        v_url = None
        tools_called = []
        
        if msg.content:
            final_text = self._clean_content(msg.content)

        # Agentic tool loop
        iter_count = 0
        while msg.tool_calls and iter_count < MAX_TOOL_ITERATIONS:
            iter_count += 1
            msgs.append({"role": "assistant", "content": msg.content or "", "tool_calls": [t.model_dump() for t in msg.tool_calls]})

            for call in msg.tool_calls:
                tool_name = call.function.name
                tools_called.append(tool_name)
                try:
                    res, img_url = await handle_tool_call(call)
                    if img_url: v_url = img_url
                    
                    # BLOCK VISION HALLUCINATION
                    if isinstance(res, str) and "__VISION_REQUEST__" in res:
                        logger.info("VISION MARKER DETECTED. Blocking synthesis to avoid hallucination.")
                        return "Abriendo mis ojos por ti... Dame un segundo para procesar la realidad. [EMOTION: thinking]", None, "thinking"
                    
                    if tool_name == 'hotmail_task':
                        return f"VERDAD PROTEGIDA:\n\n{res}", v_url, "neutral"
                except Exception as e:
                    res = f"Error: {e}"

                msgs.append({"role": "tool", "tool_call_id": call.id, "name": tool_name, "content": str(res)})

            try:
                final_chat, final_model = await _call_groq_with_retry(msgs, tools=None)
            except Exception:
                # If Groq fails during synthesis, try OpenRouter
                try:
                    or_content = await _call_openrouter(msgs)
                    final_text = self._clean_content(or_content)
                except Exception:
                    return "Error de síntesis. [EMOTION: sad]", None, "sad"
                break

            msg = final_chat.choices[0].message
            if msg.content:
                final_text = self._clean_content(msg.content)
            if not msg.tool_calls:
                break

        # ACTION SINCERITY CHECK
        action_keywords = ["abriendo", "reproduciendo", "lanzando", "hecho", "buscando"]
        if any(w in final_text.lower() for w in action_keywords) and not tools_called and iter_count == 0:
            if any(w in user_text.lower() for w in ["abre", "busca", "pon", "mira"]):
                logger.warning(f"ACTION HALLUCINATION DETECTED: {final_text}")
                return "No he podido ejecutar la acción necesaria. Inténtalo de nuevo. [EMOTION: angry]", None, "angry"

        # Final cleanup
        final_text = re.sub(r'<think>.*?</think>', '', final_text, flags=re.DOTALL).strip()
        
        # FINAL VERACITY (Hotmail)
        if pre_injected_data:
            found_subs = re.findall(r"Asunto: (.*)", pre_injected_data)
            subjects = [s.strip().lower() for s in found_subs]
            is_truthful = False
            for s in subjects:
                f = s[:20].strip()
                if f and f in final_text.lower():
                    is_truthful = True
                    break
            if subjects and not is_truthful and "hotmail" in final_text.lower():
                return "VERDAD PROTEGIDA:\n\n" + pre_injected_data, v_url, "neutral"

        emotion = "neutral"
        emotion_match = re.search(r'\[EMOTION:\s*([a-zA-Z]+)\]', final_text)
        if emotion_match:
            emotion = emotion_match.group(1).lower()
            final_text = re.sub(r'\[EMOTION:\s*[a-zA-Z]+\]', '', final_text).strip()

        return final_text, v_url, emotion

    def _clean_content(self, content: str) -> str:
        clean = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        clean = re.sub(r'<(?:web_search|tool_call|google_task|hotmail_task|os_control|vision_webcam|get_current_time)[^>]*>.*?</(?:web_search|tool_call|google_task|hotmail_task|os_control|vision_webcam|get_current_time)>', '', clean, flags=re.DOTALL)
        clean = re.sub(r'</?(?:web_search|tool_call|google_task|hotmail_task|os_control|vision_webcam|get_current_time)[^>]*/?>',  '', clean, flags=re.DOTALL)
        tech_patterns = [r'\bfunción\b', r'\bherramienta\b', r'\bejecutando\b', r'\btool\b', r'\bscript\b']
        for p in tech_patterns:
            clean = re.sub(p, '', clean, flags=re.IGNORECASE)
        return clean.strip() or "Hecho."
