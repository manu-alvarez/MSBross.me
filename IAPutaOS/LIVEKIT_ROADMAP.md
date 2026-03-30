# LiveKit (Nikolina) — Roadmap y Plan de Comparación

> Creado: 20/03/2026 — Ejecutar al cambiar workspace a LIVEKIT

---

## 🎯 Contexto

Último trabajo conocido (17/03/2026): Gemini Native Realtime deployment con Gemini 1.5 Flash y Gemini 1.5 Flash-8B para audio/visión nativo en LiveKit. Se desplegó al VPS.

**Algo fue mal** → Necesitamos detectar qué pasó.

---

## 📋 Plan de Ejecución

### Fase 1: Auditoría Local
1. Explorar estructura completa de `/Users/manu/Desktop/LIVEKIT`
2. Leer todos los archivos fuente (agents, configs, Docker, requirements)
3. `git log --oneline -20` — Ver últimos commits
4. `git status` — Archivos sin commitear
5. `git branch -a` — Ramas locales y remotas
6. `git remote -v` — URLs configuradas

### Fase 2: Comparación con GitHub
7. `git fetch origin` — Traer últimas refs
8. `git diff HEAD origin/main --stat` — Diferencias
9. `git log HEAD..origin/main --oneline` — Commits que faltan localmente
10. `git log origin/main..HEAD --oneline` — Commits locales no subidos

### Fase 3: Comparación con VPS
11. SSH al VPS → `cd` al proyecto LiveKit
12. `git status`, `git log --oneline -10`
13. `docker ps`, `docker compose ps` — Estado de containers
14. `docker logs` — Logs del agente
15. Comparar `.env` del VPS con local

### Fase 4: Diagnóstico y Resolución
16. Identificar fuente de verdad (¿local, VPS o GitHub?)
17. Resolver discrepancias (merge/reset)
18. Confirmar que el agente funciona en VPS

---

## ⚡ Tareas Pendientes del Proyecto LiveKit

Basado en la conversación anterior:
- [ ] Verificar que Gemini Native Realtime funciona
- [ ] Confirmar que el agente de LiveKit sigue activo en VPS
- [ ] Revisar configuración de audio/visión nativo
- [ ] Verificar tokens y API keys en VPS
- [ ] Comprobar logs de errores del agente
- [ ] Sincronizar código local ↔ VPS ↔ GitHub

---

*Listo para ejecutar al cambiar de workspace.*
