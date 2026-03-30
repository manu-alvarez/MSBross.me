import logging
import os
import json
import httpx
import msal

logger = logging.getLogger(__name__)

TOKEN_CACHE_FILE = "msal_token.json"
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"

def _get_access_token():
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
    tenant_id = os.getenv("MICROSOFT_TENANT_ID", "common")
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scopes = ["Mail.Read", "Mail.ReadWrite", "Mail.Send", "User.Read"]
    
    if not client_id or not client_secret:
        raise ValueError("MICROSOFT_CLIENT_ID o MICROSOFT_CLIENT_SECRET no configurados en .env")

    cache = msal.SerializableTokenCache()
    
    # We load cache first if it exists and works via msal
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, "r") as f:
                content = f.read()
                # Simple heuristic to determine if it's the raw json token or a serialized cache
                if '"AccessToken"' in content:
                    cache.deserialize(content)
        except Exception as e:
            logger.warning(f"Failed to deserialize cache: {e}")
            
    app = msal.ConfidentialClientApplication(
        client_id, authority=authority,
        client_credential=client_secret,
        token_cache=cache
    )
    
    # Attempt 1: Get token from valid cache (only works if we already converted the token into msal cache)
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])
        if result and "access_token" in result:
            if cache.has_state_changed:
                with open(TOKEN_CACHE_FILE, "w") as f:
                    f.write(cache.serialize())
            return result["access_token"]
            
    # Attempt 2: Use the manual raw json dumped by our local script with refresh_token
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, "r") as f:
                data = json.load(f)
                
            if "refresh_token" in data:
                result = app.acquire_token_by_refresh_token(data["refresh_token"], scopes=scopes)
                if result and "access_token" in result:
                    if cache.has_state_changed:
                        with open(TOKEN_CACHE_FILE, "w") as f:
                            f.write(cache.serialize())
                    return result["access_token"]
        except Exception as e:
            logger.error(f"Error parseando el token manual: {e}")
            
    raise Exception("No se pudo obtener un token de acceso válido. La autorización expiró o el archivo no existe.")


async def hotmail_executor(task_type: str, args: dict) -> tuple[str, str]:
    """
    Ejecutor principal para Hotmail usando Microsoft Graph API + MSAL OAuth2.
    """
    logger.info(f"Hotmail Graph API Task: {task_type}")

    try:
        access_token = _get_access_token()
    except Exception as e:
        logger.error(f"Hotmail Auth Error: {e}")
        return f"Error de autenticación con Hotmail (Microsoft Graph API). Intenta loguearte de nuevo: {e}", None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    if task_type == "read":
        limit = args.get("limit", 5)
        try:
            # Obtenemos los mensajes ordenados del más nuevo al más antiguo
            url = f"{GRAPH_ENDPOINT}/me/messages?$top={limit}&$select=sender,subject,bodyPreview,id&$orderby=receivedDateTime desc"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                
            if response.status_code != 200:
                logger.error(f"Graph API Error: {response.text}")
                return f"Error leyendo correos de Hotmail (Graph API). Código: {response.status_code}. Mensaje: {response.text}", None
                
            data = response.json()
            messages = data.get("value", [])
            
            if not messages:
                return "La bandeja de entrada de Hotmail está vacía.", None
                
            results = []
            for msg in messages:
                sender = msg.get("sender", {}).get("emailAddress", {}).get("address", "Desconocido")
                subject = msg.get("subject", "Sin asunto")
                preview = msg.get("bodyPreview", "")
                clean_preview = preview.replace('\n', ' ')[:100]
                results.append(f"De: {sender}\nAsunto: {subject}\nResumen: {preview}\n")
                
            verification_marker = "\n[SISTEMA: Estos datos son REALES de MICROSOFT GRAPH API. No inventes.]\n"
            return f"{verification_marker}Últimos {limit} correos en Hotmail:\n\n" + "\n---\n".join(results), None
            
        except Exception as e:
            logger.error(f"Error en hotmail_read_graph: {e}")
            return f"Error de red leyendo correos de Hotmail: {e}", None

    elif task_type == "send":
        to_email = args.get("to")
        subject = args.get("subject", "Sin asunto")
        body = args.get("body", "")
        
        if not to_email:
            return "Error: Falta el destinatario (to).", None
            
        try:
            url = f"{GRAPH_ENDPOINT}/me/sendMail"
            payload = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "Text",
                        "content": body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to_email
                            }
                        }
                    ]
                },
                "saveToSentItems": "true"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
            if response.status_code == 202:
                logger.info(f"Correo enviado exitosamente a {to_email}")
                return f"Correo enviado exitosamente a {to_email} por Hotmail (Graph API).", None
            else:
                logger.error(f"Graph API Error Send: {response.text}")
                return f"Error al enviar correo por Hotmail. Código: {response.status_code}. Razón: {response.text}", None
                
        except Exception as e:
            logger.error(f"Error en hotmail_send_graph: {e}")
            return f"Error de red enviando correo de Hotmail: {e}", None

    return f"Error: Tarea de Hotmail desconocida '{task_type}'", None
