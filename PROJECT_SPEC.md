# 📜 MSBross Ecosystem Specification (OpenSpec)
**Versión:** 1.0.0 · **Estado:** Producción · **Metodología:** Spec-Driven Development

---

## 1. Visión General
`msbross.me` es un centro de control unificado para aplicaciones de Inteligencia Artificial de alto rendimiento, gestionado mediante una arquitectura serverless delegada en PHP y despliegues en VPS externos para servicios en tiempo real.

## 2. Pila Tecnológica (SOTA 2026)
| Capa | Tecnología | Estándar |
|------|------------|----------|
| **Núcleo API** | PHP 8.x + cURL | RESTful Serverless |
| **Frontend Hub** | HTML5 + CSS3 (Glassmorphism) | WCAG 2.2 AAA |
| **Aplicaciones** | React + Vite + MUI / Tailwind | Clean Architecture |
| **IA Backend** | Python + LiveKit + Gemini Realtime | Native Multimodal |
| **Persistencia** | JSON File-based / SQLite | Zero DB Management |

---

## 3. Estándares Técnicos Obligatorios

### ⚡ Performance: Core Web Vitals
Para garantizar una experiencia fluida, el sistema debe cumplir con los siguientes umbrales:
- **LCP (Largest Contentful Paint):** < 2.5s (optimizado via `link rel="preload"`).
- **INP (Interaction to Next Paint):** < 200ms (optimización de manejadores de eventos).
- **CLS (Cumulative Layout Shift):** < 0.1 (estructuras con reserved space).

### ♿ Accesibilidad: WCAG 2.2
Cumplimiento con el **European Accessibility Act**:
- **Landmarks:** Uso de `role="navigation"`, `role="main"`, `role="complementary"`.
- **Interacción:** Todos los elementos interactivos poseen `aria-label` descriptivo.
- **Visibilidad:** Contraste mínimo 4.5:1 (AA) para texto normal, 3:1 (A) para componentes UI.
- **Semántica:** Ocultación de elementos decorativos via `aria-hidden="true"`.

### 🔒 Seguridad: Resiliencia de Red
Implementación de cabeceras de seguridad en todas las respuestas de `api.php`:
- **CSP (Content Security Policy):** Directivas estrictas para scripts y conexiones.
- **HSTS:** Forzado de HTTPS en todas las subconexiones.
- **Security Headers:** `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`.
- **Secrets:** API Keys aisladas en servidor, nunca expuestas en cliente.

---

## 4. Arquitectura de Aplicaciones

### IAPuta OS
- **Paradigma:** Clean Architecture (Domain-driven).
- **Core:** React + Three.js Orb.
- **Backend:** FastAPI (Local/VPS) y Proxy PHP (Producción).

### Nikolina AI
- **Modo Audio:** Gemini Realtime (Native Audio).
- **Infraestructura:** LiveKit SDK + Python Agent.
- **Interfaz:** React Components + Voice Visualization.

### COMBIPRO
- **Motor:** The Odds API logic.
- **Seguridad:** Fetch delegados via `api.php?action=combipro`.
- **Riesgo:** Perfiles Conservador / Equilibrado / Agresivo.

---

## 5. Protocolo de Despliegue (Clean Deploy)
El despliegue se realiza exclusivamente a través de `vps_mirror_deploy.py`:
1.  **Validación:** `npm run lint` y `npm run build`.
2.  **Sincronización:** Mirror exacto de `dist/` a la ruta remota `/www/`.
3.  **Cleanup:** Eliminación de archivos temporales post-despliegue.

## 6. Mantenimiento (Linting & Clean Code)
- **Linter:** ESLint con reglas de React/AirBnB.
- **Formatter:** Prettier (2 space indentation, no semicolons).
- **Code Style:** Funciones puras, inmutabilidad, y tipado estricto donde sea posible.
