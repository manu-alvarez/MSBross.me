import os
import base64
import datetime
import asyncio
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    'https://mail.google.com/', 
    'https://www.googleapis.com/auth/calendar', 
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/youtube.readonly'
]


def get_google_creds():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
        else:
            # Note: This part shouldn't run on the VPS without a browser, 
            # we rely on the token.json uploaded from local.
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token: 
            token.write(creds.to_json())
    return creds


def _parse_task(task: str) -> dict:
    """Parse a natural language task string into a dict of action + params."""
    task_lower = task.lower()
    params = {"raw": task}
    
    # Send email
    if any(kw in task_lower for kw in ['envia', 'enviar', 'manda', 'mandar', 'send', 'escribe', 'redacta']):
        params["action"] = "send"
    # Create calendar event
    elif any(kw in task_lower for kw in ['crea evento', 'añade evento', 'agenda', 'create event', 'add event']):
        params["action"] = "create_event"
    # Search / List
    elif any(kw in task_lower for kw in ['busca', 'buscar', 'search', 'lista', 'listar', 'list', 'ver', 'mira', 'qué hay']):
        params["action"] = "list"
    else:
        params["action"] = "list"
    
    return params


async def google_executor(srv: str, task: str):
    """
    Principal executor for Google APIs.
    srv: 'gmail' | 'calendar' | 'drive' | 'contacts' | 'youtube'
    """
    def _run():
        try:
            creds = get_google_creds()
            params = _parse_task(task)
            
            # ───────────────────────────── GMAIL ─────────────────────────────
            if srv == 'gmail':
                service = build('gmail', 'v1', credentials=creds)
                
                if params["action"] == "send":
                    parts = {p.split(':', 1)[0].strip().lower(): p.split(':', 1)[1].strip()
                             for p in task.split('|') if ':' in p}
                    to = parts.get('to', '')
                    subject = parts.get('subject', 'Sin asunto')
                    body = parts.get('body', '')
                    
                    if not to:
                        return "Error: Falta destinatario (to: correo | subject: asunto | body: mensaje)"
                    
                    msg = MIMEMultipart()
                    msg['to'] = to
                    msg['subject'] = subject
                    msg.attach(MIMEText(body, 'plain'))
                    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
                    service.users().messages().send(userId='me', body={'raw': raw}).execute()
                    return f"Gmail enviado a {to}."
                
                else:
                    results = service.users().messages().list(userId='me', maxResults=5).execute()
                    messages = results.get('messages', [])
                    if not messages: return "Gmail: Sin mensajes."
                    sums = []
                    for m in messages:
                        msg = service.users().messages().get(userId='me', id=m['id'], format='metadata').execute()
                        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
                        sums.append(f"De: {headers.get('From')} | Asunto: {headers.get('Subject')}")
                    return "Gmail:\n" + "\n".join(sums)
            
            # ───────────────────────────── CALENDAR ─────────────────────────────
            elif srv == 'calendar':
                service = build('calendar', 'v3', credentials=creds)
                if params["action"] == "create_event":
                    # Simple creation logic
                    return "Función de creación en desarrollo. Por ahora lee la agenda."
                else:
                    now = datetime.datetime.utcnow().isoformat() + 'Z'
                    events = service.events().list(calendarId='primary', timeMin=now, maxResults=5).execute().get('items', [])
                    if not events: return "Calendario: Sin eventos próximos."
                    return "Eventos:\n" + "\n".join([f"- {e['start'].get('dateTime', e['start'].get('date'))}: {e.get('summary')}" for e in events])

            # ───────────────────────────── DRIVE ─────────────────────────────
            elif srv == 'drive':
                service = build('drive', 'v3', credentials=creds)
                query = f"name contains '{task}'" if task else "trashed = false"
                results = service.files().list(pageSize=10, q=query, fields="files(name, mimeType)").execute()
                items = results.get('files', [])
                if not items: return "Drive: No se encontraron archivos."
                return "Archivos en Drive:\n" + "\n".join([f"- {i['name']} ({i['mimeType']})" for i in items])

            # ───────────────────────────── CONTACTS ─────────────────────────────
            elif srv == 'contacts':
                service = build('people', 'v1', credentials=creds)
                results = service.people().connections().list(
                    resourceName='people/me', pageSize=10, personFields='names,emailAddresses'
                ).execute()
                conns = results.get('connections', [])
                if not conns: return "Contactos: No se encontraron contactos."
                return "Contactos:\n" + "\n".join([f"- {c['names'][0]['displayName']} ({c['emailAddresses'][0]['value'] if 'emailAddresses' in c else 'No email'})" for c in conns])

            # ───────────────────────────── YOUTUBE ─────────────────────────────
            elif srv == 'youtube':
                service = build('youtube', 'v3', credentials=creds)
                results = service.subscriptions().list(part="snippet", mine=True, maxResults=10).execute()
                items = results.get('items', [])
                if not items: return "YouTube: No se encontraron suscripciones."
                return "Suscripciones YouTube:\n" + "\n".join([f"- {i['snippet']['title']}" for i in items])

            return f"Servicio '{srv}' no implementado aún."
        except Exception as e:
            return f"Error Google ({srv}): {str(e)}"
    
    res = await asyncio.to_thread(_run)
    return res, None
