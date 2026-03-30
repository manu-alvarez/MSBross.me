"""
Telegram Tool — Send/receive messages via Telegram Bot API.
Includes background polling for auto-reply relay to owner.

Requires in .env:
  TELEGRAM_BOT_TOKEN=<bot token>
  TELEGRAM_DEFAULT_CHAT_ID=<your personal chat_id>
"""

import asyncio
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

# Track the last processed update to avoid duplicates
_last_update_id = 0

WELCOME_MESSAGE = (
    "👋 ¡Hola! Soy el asistente de Manu.\n\n"
    "Escríbeme lo que quieras y se lo paso directamente. "
    "Te responderé con lo que me diga. 🤖"
)


async def send_telegram(message: str, chat_id: str = None) -> tuple:
    """
    Sends a message via Telegram.
    chat_id: target chat ID. Falls back to TELEGRAM_DEFAULT_CHAT_ID.
    """
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    target_chat = chat_id or getattr(settings, 'TELEGRAM_DEFAULT_CHAT_ID', None)

    if not token:
        return "Error: TELEGRAM_BOT_TOKEN no configurado en las variables de entorno.", None
    if not target_chat:
        return "Error: TELEGRAM_DEFAULT_CHAT_ID no configurado. Especifica un chat_id o configúralo en .env.", None

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": target_chat, "text": message, "parse_mode": "Markdown"}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(url, json=payload)
            data = resp.json()
            if data.get("ok"):
                return f"Mensaje enviado por Telegram a chat {target_chat}.", None
            else:
                return f"Error Telegram: {data.get('description', 'desconocido')}", None
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return f"Error enviando Telegram: {str(e)}", None


async def get_telegram_updates() -> tuple:
    """Gets the latest messages received by the bot."""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token:
        return "Error: TELEGRAM_BOT_TOKEN no configurado.", None

    url = f"https://api.telegram.org/bot{token}/getUpdates?limit=5"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url)
            data = resp.json()
            messages = data.get("result", [])
            if not messages:
                return "Telegram: No hay mensajes nuevos.", None
            lines = []
            for upd in messages:
                msg = upd.get("message", {})
                sender = msg.get("from", {}).get("first_name", "?")
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id", "?")
                lines.append(f"- {sender} (chat:{chat_id}): {text}")
            return "Mensajes Telegram:\n" + "\n".join(lines), None
        except Exception as e:
            return f"Error obteniendo mensajes Telegram: {str(e)}", None


# ---------------------------------------------------------------------------
# Background Polling: Auto-reply relay
# ---------------------------------------------------------------------------
async def _send_raw(token: str, chat_id, text: str):
    """Low-level send helper used by the poller (no settings checks)."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json=payload)


async def telegram_polling_loop():
    """
    Background task that polls for new Telegram messages every 3 seconds.
    - On /start: sends welcome message.
    - On any other message from a third party: auto-replies and relays to owner.
    - Ignores messages from the owner's own chat.
    """
    global _last_update_id

    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    owner_chat = getattr(settings, 'TELEGRAM_DEFAULT_CHAT_ID', None)

    if not token or not owner_chat:
        logger.warning("Telegram polling disabled: missing BOT_TOKEN or DEFAULT_CHAT_ID.")
        return

    owner_chat_str = str(owner_chat)
    logger.info("Telegram auto-reply polling started.")

    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={_last_update_id + 1}&timeout=10"
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
                data = resp.json()

            for update in data.get("result", []):
                _last_update_id = update["update_id"]
                msg = update.get("message")
                if not msg:
                    continue

                chat_id = msg.get("chat", {}).get("id")
                sender_name = msg.get("from", {}).get("first_name", "Desconocido")
                sender_username = msg.get("from", {}).get("username", "")
                text = msg.get("text", "")

                # Skip messages from the owner (Manu himself)
                if str(chat_id) == owner_chat_str:
                    continue

                # /start command → welcome message
                if text.startswith("/start"):
                    await _send_raw(token, chat_id, WELCOME_MESSAGE)
                    # Notify owner about new contact
                    await _send_raw(
                        token, owner_chat_str,
                        f"📬 Nuevo contacto en el bot:\n"
                        f"Nombre: {sender_name}\n"
                        f"Username: @{sender_username}\n"
                        f"Chat ID: {chat_id}\n"
                        f"(Ya le he dado la bienvenida)"
                    )
                else:
                    # Auto-reply to the sender
                    await _send_raw(
                        token, chat_id,
                        f"✅ Recibido. Le paso tu mensaje a Manu y te responderé con lo que me diga."
                    )
                    # Relay the message to the owner
                    await _send_raw(
                        token, owner_chat_str,
                        f"💬 Mensaje de {sender_name} (@{sender_username}, chat:{chat_id}):\n\n{text}"
                    )

        except Exception as e:
            logger.error(f"Telegram polling error: {e}")

        await asyncio.sleep(3)
