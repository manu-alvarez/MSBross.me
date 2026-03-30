import { 
  IconMonitor, IconCamera, IconGlobe, 
  IconCalendar, IconMail, IconSend 
} from '../components/Icons.jsx';

export const CORE_PLUGINS = [
  { id: 'vision', label: '(V)ision Eye', status: 'ACTIVE', color: '#ff3c3c' },
  { id: 'search', label: '(W)eb Search', status: 'STANDBY', color: '#3b82f6' },
  { id: 'workspace', label: '(O)ffice Workspace', status: 'CONNECTED', color: '#a855f7' },
  { id: 'imap', label: '(Email) IMAP', status: 'SYNCED', color: '#00d4ff' },
  { id: 'terminal', label: '(T)erminal', status: 'READY', color: '#10b981' },
];

export const TOOLS = [
  { id: 'screenshot', icon: IconMonitor, color: '#a855f7', label: 'Pantalla', sub: 'Captura', action: 'screenshot' },
  { id: 'webcam', icon: IconCamera, color: '#ec4899', label: 'Visión', sub: 'IA Cámara', action: 'webcam' },
  { id: 'search', icon: IconGlobe, color: '#3b82f6', label: 'Buscar', sub: 'Tavily AI', cmd: 'Busca en internet últimas noticias de IA' },
  { id: 'calendar', icon: IconCalendar, color: '#10b981', label: 'Agenda', sub: 'Google', cmd: '¿Qué tengo hoy en mi Google Calendar?' },
  { id: 'email', icon: IconMail, color: '#0078d4', label: 'Correo', sub: 'Outlook', cmd: 'Léeme mis últimos correos de Hotmail' },
];
