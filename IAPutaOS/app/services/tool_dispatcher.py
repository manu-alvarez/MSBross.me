"""
Tool dispatcher — routes LLM tool_calls to the correct handler function.
Clean version: No WhatsApp, no duplicates.
"""

import json
import logging

from app.tools.toolbox import (
    vision_eye, vision_webcam,
    os_control_request,
    approve_and_run_script, execute_python
)
from app.tools.google_tools import google_executor
from app.tools.hotmail_tool import hotmail_executor
from app.tools.search_tools import unified_search
from app.tools.telegram_tool import send_telegram, get_telegram_updates

logger = logging.getLogger(__name__)


async def handle_tool_call(call):
    """
    Dispatch a single LLM tool_call to its corresponding Python handler.
    Returns a tuple of (result_text, optional_image_url).
    """
    name = call.function.name
    try:
        args = json.loads(call.function.arguments)
    except Exception:
        args = {}

    if name == "vision_analysis":
        return await vision_eye()

    elif name == "vision_webcam":
        return await vision_webcam()

    elif name == "web_search":
        return await unified_search(args.get("query", ""), args.get("engine", "tavily")), None

    elif name == "hotmail_task":
        res, img = await hotmail_executor(args.get("task", ""), args)
        logger.info(f"HOTMAIL_RESULT: {res[:200]}...")
        return res, img

    elif name == "google_task":
        srv = args.get('srv')
        if srv == "gmail":
            return "Error: Gmail no está disponible. Usa hotmail_task para correos.", None
        res, img = await google_executor(srv, args.get('task'))
        return res, img

    elif name == "os_control":
        return await os_control_request(
            args.get("act"), args.get("val"), args.get("code")
        )

    elif name == "approve_and_run_script":
        return await approve_and_run_script(args.get("script_id"))

    elif name == "execute_python":
        return await execute_python(args.get("code"))

    elif name == "get_current_time":
        from app.tools.toolbox import get_current_time
        return await get_current_time()

    elif name == "telegram_send":
        return await send_telegram(args.get("message", ""), args.get("chat_id"))

    elif name == "telegram_read":
        return await get_telegram_updates()

    elif name == "ios_shortcut":
        import httpx
        webhook_url = args.get("url", "")
        params = args.get("params", {})
        if not webhook_url:
            return "Error: Se necesita una URL de webhook de iOS Shortcuts.", None
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(webhook_url, params=params)
            return f"iOS Shortcut disparado. Respuesta: {resp.status_code}", None

    return f"Unknown tool: {name}", None
