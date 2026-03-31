#!/usr/bin/env bash
set -e

# Load environment variables
if [[ -f .env.local ]]; then
  export $(grep -v '^#' .env.local | xargs)
fi

echo "🚀 Iniciando despliegue del ecosistema"

# 1️⃣ IAPuta OS (Docker‑Compose o native)
echo "⚠️ Docker daemon no disponible o Docker‑Compose falló, iniciando IAPuta OS nativamente"
# Backend (FastAPI)
(cd IAPutaOS && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000 &) 
# Frontend (Vite)
(cd IAPutaOS/frontend && npm install && npm run dev &)

# 2️⃣ LIVEKIT (backend, agent, frontend)
if [[ -d livekit-backend ]]; then
  echo "▶️ Iniciando LIVEKIT backend"
  (cd livekit-backend && npm install && npm run dev &) 
fi
if [[ -d livekit-frontend ]]; then
  echo "▶️ Iniciando LIVEKIT frontend"
  (cd livekit-frontend && npm install && npm run dev &) 
fi
if [[ -d livekit-backend/agent ]]; then
  echo "▶️ Iniciando LIVEKIT agent"
  (cd livekit-backend/agent && npm install && npm run dev &) 
fi

# 3️⃣ DOHLER (frontend + backend)
if [[ -d dohler_src/frontend ]]; then
  echo "▶️ Iniciando DOHLER frontend"
  (cd dohler_src/frontend && npm run dev &) 
fi
if [[ -d dohler_src/backend ]]; then
  echo "▶️ Iniciando DOHLER backend"
  (cd dohler_src/backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python3 app.py &) 
fi

# 4️⃣ Arantxa Translate PRO (client + server)
if [[ -d "/Users/manu/Desktop/Arantxa Translate PRO" ]]; then
  echo "▶️ Iniciando Arantxa Translate PRO"
  (cd "/Users/manu/Desktop/Arantxa Translate PRO" && npm install && npm run start:translate &)
fi 
fi

# 5️⃣ TaskFlowPro
if [[ -d taskflow_pro_src ]]; then
  echo "▶️ Iniciando TaskFlowPro"
  (cd taskflow_pro_src && npm install && npm run dev &) 
fi

wait

echo "✅ Todos los servicios están corriendo."

echo "🔗 Accesos locales:"
cat <<EOF
- Arantxa Translate PRO → http://localhost:5173
- DOHLER               → http://localhost:3000
- IAPuta OS (frontend) → http://localhost:8080
- LIVEKIT (frontend)  → http://localhost:5174
- TaskFlowPro          → http://localhost:8887
EOF
