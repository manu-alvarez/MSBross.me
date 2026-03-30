# LiveKit Project — Plan de Comparación Local vs VPS vs GitHub

> Creado: 20/03/2026 — Para ejecutar al cambiar al workspace LIVEKIT

---

## 🎯 Objetivo
Determinar qué ha pasado con el proyecto LiveKit: comparar el estado local (`/Users/manu/Desktop/LIVEKIT`) con lo que hay en el VPS y en GitHub para identificar discrepancias, commits perdidos o conflictos.

---

## 📋 Plan de Ejecución (paso a paso)

### Fase 1: Auditoría Local
1. **Explorar estructura completa** del directorio `/Users/manu/Desktop/LIVEKIT`
2. **Leer todos los archivos fuente** (Python agents, configs, requirements, Docker)
3. **Revisar git log** local: `git log --oneline -20`
4. **Revisar git status**: archivos sin commitear, cambios no staged
5. **Revisar ramas**: `git branch -a` para ver branches locales y remotos
6. **Revisar remotes**: `git remote -v` para confirmar URLs

### Fase 2: Comparación con GitHub
7. **Fetch del remoto**: `git fetch origin` para traer últimas refs
8. **Diff local vs origin**: `git diff HEAD origin/main --stat` (o la rama principal)
9. **Comparar commits**: `git log HEAD..origin/main --oneline` y `git log origin/main..HEAD --oneline`
10. **Identificar conflictos potenciales**: archivos modificados en ambos lados

### Fase 3: Comparación con VPS
11. **Conectar al VPS** via SSH
12. **Revisar estado en VPS**: `git status`, `git log --oneline -10`
13. **Comparar Docker containers**: `docker ps`, `docker logs`
14. **Verificar si el agente está corriendo**: `systemctl status` o `docker compose ps`
15. **Comparar .env del VPS** con .env local (sin exponer secretos)

### Fase 4: Diagnóstico
16. **Identificar la fuente de verdad**: ¿Cuál versión es la correcta?
17. **Documentar discrepancias** encontradas
18. **Proponer resolución**: merge, reset, o restructuración

---

## ⚠️ Contexto del Último Trabajo Conocido

Según la conversación `2a47ccce-6b5f-4cff-9a2f-164e4cf7f326` (17/03/2026):
- Se trabajó en **Gemini Native Realtime** con LiveKit
- Se configuró el agente para **Gemini 1.5 Flash** y **Gemini 1.5 Flash-8B**
- Se desplegó al VPS
- Eran modelos para procesamiento nativo de audio y visión en realtime

### Preguntas Clave a Responder:
1. ¿El deploy al VPS fue exitoso y se mantuvo?
2. ¿Hubo cambios locales después del deploy que no se subieron?
3. ¿Alguien (o algo) modificó el VPS directamente sin commit?
4. ¿El agent de LiveKit en el VPS sigue corriendo o se cayó?

---

## 🔧 Herramientas Necesarias
- Acceso SSH al VPS
- `git` (local y remoto)
- `docker` / `docker compose` (en VPS)
- Credenciales del repositorio GitHub

---

*Este plan se ejecutará al cambiar al workspace LIVEKIT.*
