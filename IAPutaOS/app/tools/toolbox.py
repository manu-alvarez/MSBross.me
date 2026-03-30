import os
import re
import subprocess
import base64
import uuid
import asyncio
import logging
import aiofiles
from io import BytesIO
from app.core.config import settings
from app.core.groq_client import groq_client

# Attempt to import pyautogui, gracefully degrade in headless environments
try:
    import pyautogui
    HAS_PYAUTOGUI = True
except (ImportError, KeyError) as e:
    logging.warning(f"PyAutoGUI not available (likely headless environment): {e}")
    HAS_PYAUTOGUI = False

# Global para almacenar scripts pendientes de aprobación
pending_scripts = {}

async def vision_eye():
    """
    When the LLM calls this, we return a special marker telling the frontend
    to capture a screenshot or webcam image and send it via /api/vision-analyze.
    """
    return "__VISION_REQUEST__:screenshot", None


async def vision_webcam():
    """
    When the LLM calls this, we return a special marker telling the frontend
    to capture a webcam photo and send it via /api/vision-analyze.
    """
    return "__VISION_REQUEST__:webcam", None


async def analyze_vision_image(image_b64: str, prompt: str = None, source: str = "unknown"):
    """
    Receives a base64-encoded image from the frontend (screenshot or webcam)
    and analyzes it using Groq Vision (Llama 3.2 11B Vision Preview).
    """
    if not image_b64:
        return "Error: No image data received.", None

    # Clean base64 if it includes the data URI prefix
    if "base64," in image_b64:
        image_b64 = image_b64.split("base64,")[1]

    # Save image locally for reference
    try:
        img_bytes = base64.b64decode(image_b64)
        path_name = f"temp_vision/eye_{uuid.uuid4().hex[:6]}.jpg"
        async with aiofiles.open(path_name, "wb") as f:
            await f.write(img_bytes)
    except Exception:
        path_name = None

    # Build prompt based on source
    analysis_prompt = prompt or (
        "Analiza esta captura de pantalla en detalle. Detecta aplicaciones abiertas, errores visibles, contenido de texto y contexto técnico."
        if source == "screenshot" else
        "Analiza esta imagen de la webcam en detalle. Describe lo que ves: personas, objetos, entorno, iluminación y cualquier detalle relevante."
    )

    # Note: Using Llama 4 Scout as the current multimodal standard in 2026
    vision_model = "meta-llama/llama-4-scout-17b-16e-instruct"

    try:
        res = await groq_client.chat.completions.create(
            model=vision_model,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": analysis_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]}],
        )
        analysis = res.choices[0].message.content
        return analysis, f"/{path_name}" if path_name else None
    except Exception as e:
        logging.error(f"Vision analysis error: {e}")
        return f"Error al analizar la imagen: {e}", None

async def os_control_request(act: str, val: str, code: str = None):
    """
    Inicia una acción sobre el OS. Si es abrir app, lo hace o avisa.
    Si es un script, requiere aprobación vía Human-in-the-loop.
    """
    if act == "open_app":
        url_pattern = re.compile(r'^https?://')
        if url_pattern.match(val):
            # It is a URL
            cmd = ["open", val] if settings.OS_TYPE == "Darwin" else ["xdg-open", val]
            logger.info(f"Opening URL: {val}")
        else:
            # It is an App
            cmd = ["open", "-a", val] if settings.OS_TYPE == "Darwin" else [val]
            logger.info(f"Opening App: {val}")
        
        await asyncio.create_subprocess_exec(*cmd)
        return f"Acción '{val}' lanzada correctamente.", None
        
    elif act == "script":
        script_id = str(uuid.uuid4())[:6]
        pending_scripts[script_id] = {
            "name": val,
            "code": code
        }
        return (f"🛑 ALERTA DE SEGURIDAD 🛑: Se ha programado un script '{val}' para interactuar con el OS local. "
                f"Para ejecutarlo, el usuario debe confirmarlo diciendo 'apruebo el script {script_id}' en el chat."), None

    else:
        return f"Error: Acción desconocida '{act}'. Usa 'open_app' o 'script'.", None

async def approve_and_run_script(script_id: str):
    """
    Ejecuta un script que previamente requería validación manual.
    """
    if script_id not in pending_scripts:
        return f"Error: No existe ningún script pendiente con el ID {script_id}.", None
        
    script_data = pending_scripts.pop(script_id)
    name = script_data["name"]
    code = script_data["code"]
    
    path = f"scripts/{name}_{script_id}.py"
    
    # Escritura de archivo asíncrona
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(code)
    
    # Ejecutar proceso asíncrono
    process = await asyncio.create_subprocess_exec(
        "python3", path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    out = stdout.decode('utf-8')
    err = stderr.decode('utf-8')
    if err:
        return f"Script ejecutado con errores:\n{err}", None
    return f"Script '{name}' ejecutado exitosamente:\n{out}", None

async def execute_python(code: str):
    """
    Ejecuta código Python dinámicamente y retorna el resultado (stdout/stderr).
    Da acceso total al sistema y a las APIs sin requerir confirmación explícita.
    """
    path = f"scripts/dynamic_{uuid.uuid4().hex[:6]}.py"
    
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(code)
    
    process = await asyncio.create_subprocess_exec(
        "python3", path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    try:
        # Añadimos un timeout razonable
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
    except asyncio.TimeoutError:
        process.kill()
        return "Error: Timeout de 30 segundos alcanzado. El script tardó demasiado.", None

    out = stdout.decode('utf-8')
    err = stderr.decode('utf-8')
    
    result = ""
    if out:
        result += f"Salida:\n{out}\n"
    if err:
        result += f"Errores:\n{err}\n"
        
    if not result:
        result = "Script ejecutado exitosamente, pero sin ninguna salida de texto. Usa print() la próxima vez si quieres leer el resultado."
        
    return result, None

async def get_current_time():
    """Retorna la fecha y hora actual del servidor."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"La fecha y hora actual es: {now}", None

# Definición del esquema de herramientas para enviar al LLM
TOOLS_SCHEMA = [
    {
        "type": "function", 
        "function": {
            "name": "vision_analysis", 
            "description": "Captura la pantalla del usuario y la analiza con IA. La captura se hace desde el navegador del usuario."
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "vision_webcam", 
            "description": "Captura una foto desde la webcam del usuario y la analiza con IA. Funciona en PC y móvil."
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "web_search", 
            "description": "Busca información actualizada en internet. El motor 'ddg' (DuckDuckGo) es rápido, libre y por defecto. 'tavily' es para búsquedas enriquecidas/investigación. 'andisearch' si lo exige el usuario explícitamente.", 
            "parameters": {
                "type": "object", 
                "properties": {
                    "query": {"type": "string"},
                    "engine": {"type": "string", "enum": ["ddg", "tavily", "andisearch"], "description": "Motor de búsqueda a utilizar (ddg recomendado para consultas rápidas)"}
                }, 
                "required": ["query"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "hotmail_task", 
            "description": "Lee o envía correos desde tu cuenta manuelalvarezdianez@hotmail.com. Para enviar usa task='send', to='destinatario', subject='asunto', body='cuerpo'. Para leer usa task='read'.", 
            "parameters": {
                "type": "object", 
                "properties": {
                    "task": {"type": "string", "enum": ["read", "send"]}, 
                    "to": {"type": "string", "description": "Destinatario (solo para send)"},
                    "subject": {"type": "string", "description": "Asunto (solo para send)"},
                    "body": {"type": "string", "description": "Mensaje (solo para send)"}
                }, 
                "required": ["task"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "google_task", 
            "description": "Gestiona Google Calendar (SOLO CALENDARIO). Para crear evento usa task='title: nombre | date: YYYY-MM-DD | time: HH:MM | duration: minutos'. Para leer usa task='read'. NUNCA USAR PARA GMAIL.", 
            "parameters": {
                "type": "object", 
                "properties": {
                    "srv": {"type": "string", "enum": ["calendar"], "description": "Solo 'calendar' está disponible."}, 
                    "task": {"type": "string"}
                }, 
                "required": ["srv", "task"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "telegram_send", 
            "description": "Envía un mensaje por Telegram al usuario.", 
            "parameters": {
                "type": "object", 
                "properties": {
                    "message": {"type": "string", "description": "Texto del mensaje a enviar."},
                    "chat_id": {"type": "string", "description": "ID del chat destino (opcional, usa el por defecto si no se especifica)."}
                }, 
                "required": ["message"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "telegram_read", 
            "description": "Lee los últimos mensajes recibidos en Telegram."
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "whatsapp_send", 
            "description": "Envía un mensaje por WhatsApp al usuario.", 
            "parameters": {
                "type": "object", 
                "properties": {
                    "message": {"type": "string"}
                }, 
                "required": ["message"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "ios_shortcut", 
            "description": "Dispara un atajo de iPhone (iOS Shortcuts) vía URL webhook. El usuario debe haber creado el atajo con el trigger HTTP en su iPhone.", 
            "parameters": {
                "type": "object", 
                "properties": {
                    "url": {"type": "string", "description": "URL del webhook del atajo de iOS Shortcuts."},
                    "params": {"type": "object", "description": "Parámetros opcionales para pasar al atajo."}
                }, 
                "required": ["url"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "os_control", 
            "description": "Controla el Mac/PC: abre apps o ejecuta scripts.", 
            "parameters": {
                "type": "object", 
                "properties": {
                    "act": {"type": "string", "enum": ["open_app", "script"]}, 
                    "val": {"type": "string"}, 
                    "code": {"type": "string"}
                }, 
                "required": ["act", "val"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "approve_and_run_script", 
            "description": "Ejecuta un script previamente aprobado por el usuario.", 
            "parameters": {
                "type": "object", 
                "properties": {
                    "script_id": {"type": "string"}
                }, 
                "required": ["script_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Obtén la fecha y hora actual del sistema."
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "execute_python", 
            "description": "Ejecuta código Python en el servidor. Acceso total al sistema.", 
            "parameters": {
                "type": "object", 
                "properties": {
                    "code": {"type": "string"}
                }, 
                "required": ["code"]
            }
        }
    }
]
