#!/bin/bash
# Navegar siempre al directorio de este script (raíz del proyecto)
cd "$(dirname "$0")"

echo "===Iniciando IAPuta OS Modular Core==="
echo "Detectando entorno y dependencias..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
