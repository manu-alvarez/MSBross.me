# 📜 NORMAS INQUEBRANTABLES DE DESARROLLO Y DESPLIEGUE (IAPUTA OS & VPS)

Todo agente, modelo, desarrollador o script que interactúe con este proyecto de forma local o remota vinculada al VPS (`51.91.108.173`) **DEBE** acatar estrictamente las siguientes directrices sin excepción. Cualquier desviación es considerada un fallo crítico.

## 1. HIGIENE DEL CÓDIGO (CLEAN CODE) ABSOLUTA
- **Prohibido el código muerto:** Todas las funciones, componentes, importaciones o variables que no se utilicen de forma activa deben ser eliminadas. No se comentan bloques obsoletos "por si acaso". Se borran. Git es el único mecanismo de retorno.
- **Prohibido el código monolítico:** Todo archivo que exceda un umbral de complejidad razonable debe modularizarse de inmediato (ej. UI en `components/`, funciones de utilidad en `utils/`, lógica de negocio en `services/`).
- **Nomenclatura estricta:** `snake_case` para backend (Python/Scripts) y `camelCase`/`PascalCase` para frontend (JavaScript/React).
- **Prohibidos los duplicados:** DRY (Don't Repeat Yourself). Si una lógica, interfaz o diseño existe, se importa y se reutiliza, jamás se duplica.

## 2. BLINDAJE DE SEGURIDAD (CERO CREDENCIALES EXUESTAS)
- **Ninguna llave en el código:** Jamás se escribirá una API Key, Token, Usuario, Contraseña, o webhook confidencial directamente en el código fuente.
- **Punto único de verdad:** Toda credencial se cargará desde variables de entorno. En desarrollo desde `.env`, en producción de forma inyectada. 
- **Control de versión:** Los archivos de variables de entorno, tokens (ej. `.json` de autenticación) y volcados de bases de datos temporales estarán SIEMPRE en `.gitignore`.

## 3. LIMPIEZA ESTRUCTURAL DE CARPETAS Y ARCHIVOS TEMPORALES
- **Prohibida la basura temporal:** No existirán carpetas de imágenes, audios o cachés temporales en subida al repositorio o en producción de forma persistente. Toda carpeta o buffer temporal como `temp_audio/` o `temp_vision/` debe limpiarse automáticamente o estar estrictamente ignorada.
- **Sin archivos de redundancia:** Se prohíben archivos tipo `config_old.txt`, `App2.jsx`, `main_bak.py`. 

## 4. HIGIENE Y MANTENIMIENTO DEL VPS Y DOCKER
- **Imágenes, Volúmenes y Redes:** Al momento de un despliegue, el VPS debe purgarse (`docker system prune -a -f --volumes`). No se tolerarán GigaBytes de basura acumulada por versiones anteriores.
- **Sincronización Estricta (Rsync --delete):** Las subidas de archivos al servidor o contenedor deben eliminar lo viejo (archivos muertos que ya no existen en local). El servidor siempre será el reflejo idéntico exacto del entorno local estable.

## 5. RESTRICCIÓN DE IA Y HERRAMIENTAS
- Ninguna IA reemplazará, modificará o alterará código lógico en uso sin validación de su impacto global.  
- Si se añade un "modelo, herramienta o mierda nueva", debe seguir escrupulosamente esta arquitectura de carpetas y estas normas. Ninguna instalación ensucia la raíz del proyecto.
