# IAPuta OS - Modular Deployment Guide

Este proyecto ha sido refactorizado aplicando **Clean Architecture (Ports & Adapters)**, integrado con React/Vite/MUI M3 en el frontend, y dockerizado para su despliegue inmutable en **VPS Producción**.

## Puertos de Acceso
- **Frontend (HTTP)**: http://localhost:8080
- **Frontend (HTTPS)**: https://localhost:8443 (requiere certificados)
- **Backend API**: http://localhost:8000

## Requisitos Previos (VPS)
- Docker y Docker Compose instalados.
- Un servidor VPS con Linux (Ubuntu Server recomendado).
- Git.

## Pasos para Despliegue Automatizado
1. **Clonar el repositorio**:
   ```bash
   git clone <URL_DEL_REPO> iaputa-os
   cd iaputa-os
   ```

2. **Configurar Entorno**:
   El proyecto es 100% seguro (secrets expurgados). Necesitas crear el `.env`:
   ```bash
   cp .env.example .env
   # Edita el archivo con nano o vim e inserta tus Tokens reales de Groq, Tavily, etc.
   nano .env
   ```

3. **Caché y Permisos de Github**:
   Comprueba que los entornos Python no están corrompiendo la carga local, usando los hooks configurados de `.gitignore` los cuales excluyen todas aquellas claves y contraseñas tuyas.

4. **Levantar el Servicio**:
   Gracias al estándar de **Twelve-Factor App**, el despliegue es en un comando:
   ```bash
   docker-compose up -d --build
   ```

5. **Acceder a la Aplicación**:
   - **Frontend**: Abre http://localhost:8080 en tu navegador
   - **API Health**: http://localhost:8000/health
   - **Logs del Backend**:
   ```bash
   docker-compose logs -f iaputa-backend
   ```

## Pipeline CI/CD Actual
Si usas Github, los tests de unidad (`pytest` para domain/use cases) y el lint correrán automáticamente cada vez que empujes a main, previniendo fallos en producción.
