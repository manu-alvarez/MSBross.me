# IAPuta OS - BLUEPRINT & ADRs

Este documento define las reglas irrompibles y directrices estratégicas de **IAPuta OS**.

## 1. Arquitectura y Código (Clean Architecture & SOLID)
- **Backend (Excepción)**: Por ser un OS centrado en Inteligencia Artificial y dependencias locales de TTS/Vision, se mantiene en **Python (FastAPI)**.
- **Clean Architecture (Ports & Adapters)**:
  - `Domain`: Lógica de negocio pura (Entidades, Interfaces Ocultas).
  - `Application`: Casos de uso (Servicios Orquestadores).
  - `Infrastructure`: Adaptadores externos (APIs de Groq, Google, Edge-TTS, Base de datos).
  - `Presentation`: FastAPI Routers (Endpoints REST).
- **SOLID**: Obligatorio. Uso de Inyección de Dependencias e Interfaces claras en Python (Type Hinting).
- **The Twelve-Factor App**: Configuraciones separadas del código (vía `.env`), stateless predeterminado para escalabilidad y logging por `stdout`.

## 2. Estándares de Datos y Comunicación
- **OpenAPI**: Todo endpoint debe estar fuertemente tipado con `pydantic` para generar documentación automática `/docs`.
- **JSON:API**: Respuestas estructuradas uniformemente (`{"data": {...}, "meta": {...}}`).
- **Autenticación (Futuro próximo)**: Integración planificada con OAuth 2.0 / JWT para accesos diferenciados.

## 3. Calidad y Estabilidad (QA)
- **Testing Pyramid**:
  - `pytest` para pruebas Unitarias (Domain/Application) y de Integración (Infrastructure).
  - `Playwright` o similar para pruebas End-to-End del Frontend.
- **TDD obligatoria**: Siempre que se escriba lógica core, se acompañará de su respectivo test unitario fallido, seguido de su implementación y refactorización.
- **Git**: `Conventional Commits` (feat:, fix:, chore:, refactor:, test:).

## 4. Infraestructura y Operaciones (DevOps)
- **Containerization**: `Dockerfile` e imagen preparada para evitar el problema "Funciona en mi máquina".
- **CI/CD**: `Github Actions` validará tests y lints antes de mezclar código a Main.

## 5. Diseño y Accesibilidad (UX/UI Avanzado)
- **Frontend Stack**: Se abandona la arquitectura estática (`index.html` monolítico). El nuevo dashboard operará bajo **React + Vite** y se usará **Material UI M3 (Material Design 3)**.
- **WCAG**: Contraste correcto, etiquetas ARIA, y full responsivity Desktop/Tablet/Mobile.

## 6. Seguridad y Legalidad
- Cero contraseñas hardcoreadas.
- Cumplimiento OWASP en enrutamiento (CORS restrictivo una vez pasemos a pre-prod, no en local-dev).

---
*Este documento actuará como la guía principal para la refactorización actual en curso.*
