# DOHLER Task Manager

Aplicación completa de gestión de tareas con temporizadores Pomodoro.

## 🚀 Quick Start

### Prerrequisitos
- Python 3.9+
- Node.js 18+ 
- npm o yarn

### Pasos para ejecutar

#### 1. Backend (Terminal 1)
```bash
cd backend

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python app.py
```
El backend correrá en `http://localhost:8000`

#### 2. Frontend (Terminal 2)
```bash
cd frontend

# Instalar dependencias
npm install

# Ejecutar app
npm start
```
La aplicación abrirá en `http://localhost:3000`

---

## 📁 Estructura del Proyecto

```
DOHLER/
├── backend/
│   ├── app.py              # FastAPI app principal
│   ├── database.py         # Módulo de base de datos SQLite
│   ├── requirements.txt    # Dependencias Python
│   ├── routes/
│   │   └── tasks.py        # Endpoints de tareas
│   └── services/
│       └── timer.py        # Servicio de temporizador
│
└── frontend/
    ├── package.json        # Dependencias Node
    ├── src/
    │   ├── App.js          # Componente principal
    │   ├── index.css       # Estilos globales
    │   └── components/
    │       ├── TaskList.js # Lista de tareas
    │       ├── TaskItem.js # Item individual
    │       ├── Timer.js    # Temporizador Pomodoro
    │       └── TimerBar.js # Barra de progreso
    └── tailwind.config.js  # Configuración Tailwind
```

---

## 🔌 API Endpoints

### Tareas
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/tasks/` | Listar todas las tareas |
| POST | `/api/tasks/` | Crear nueva tarea |
| GET | `/api/tasks/{id}` | Obtener tarea específica |
| PATCH | `/api/tasks/{id}` | Actualizar tarea |
| PUT | `/api/tasks/{id}/toggle` | Alternar completada |
| DELETE | `/api/tasks/{id}` | Eliminar tarea |
| GET | `/api/tasks/stats/summary` | Estadísticas |

### Temporizador
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/timer/start` | Iniciar temporizador |
| GET | `/api/timer/status` | Estado actual |
| POST | `/api/timer/stop` | Detener temporizador |
| GET | `/api/timer/stats` | Estadísticas de timer |

---

## 🎯 Funcionalidades

- ✅ Crear/editar/eliminar tareas
- ✅ Prioridades (Alta, Media, Baja)
- ✅ Tareas recurrentes
- ✅ Temporizador Pomodoro (15/25/45/60 min)
- ✅ Alertas a 5 y 1 minuto
- ✅ Persistencia SQLite
- ✅ Estadísticas en tiempo real

---

## 🛠️ Tecnologías

**Backend:**
- FastAPI (Python)
- SQLite con aiosqlite
- Pydantic

**Frontend:**
- React 18
- Tailwind CSS
- Axios
- React Icons

---

## ⚠️ Notas Importantes

1. **CORS**: Configurado para `localhost:3000`. Cambiar en producción.
2. **Base de datos**: Se crea automáticamente en `backend/tasks.db`
3. **Sin autenticación**: Versión actual es single-user local

---

## 🚢 Deploy Rápido (Producción)

### Backend
```bash
# Production server
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend
```bash
npm run build
# Los archivos estáticos están en build/
```

---

**¡Listo!** La aplicación debería estar funcionando en `http://localhost:3000`