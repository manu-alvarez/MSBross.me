"""
Search tools — Unified search across multiple engines.
Default: Tavily (best for real-time). Fallback: DuckDuckGo.
"""

import logging
import asyncio
from datetime import datetime
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
from app.core.config import settings

logger = logging.getLogger(__name__)


async def unified_search(query: str, engine: str = "tavily") -> str:
    """
    Search across multiple engines.
    engine: 'tavily' (default, best quality), 'ddg' (DuckDuckGo free fallback)
    """
    logger.info(f"Unified search: '{query}' engine={engine}")

    # Detect if the query is time-sensitive
    live_keywords = [
        "partido", "fútbol", "resultado", "en directo", "hoy", "ahora", "noticias", 
        "live", "score", "clima", "tiempo", "precio", "bolsa", "bitcoin", "sucede",
        "última hora", "quién es el actual", "quién ha ganado", "está jugando", "once",
        "nba", "champions", "europa league", "uefa", "liga", "premier"
    ]
    is_live = any(k in query.lower() for k in live_keywords) or " de 202" in query

    # Try Tavily first (default and best)
    if engine == "tavily" or (engine != "ddg" and settings.TAVILY_API_KEY):
        tavily_result = await _search_tavily(query, is_live)
        if tavily_result and "Error" not in tavily_result:
            return tavily_result
        # Fall through to DDG if Tavily fails
        logger.warning(f"Tavily failed or returned error, falling back to DDG")

    # DuckDuckGo fallback
    return await _search_ddg(query, is_live)


async def _search_tavily(query: str, is_live: bool) -> str:
    """Search using Tavily API (best for current events)."""
    if not settings.TAVILY_API_KEY:
        return "Error: TAVILY_API_KEY no configurada."
    
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "api_key": settings.TAVILY_API_KEY,
                "query": query,
                "search_depth": "advanced" if is_live else "basic",
                "include_answer": True
            }
            resp = await client.post("https://api.tavily.com/search", json=payload, timeout=15.0)
            if resp.status_code != 200:
                return f"Error Tavily API: {resp.status_code}"
            
            data = resp.json()
            results = [f"Resultados Tavily para '{query}':", f"Respuesta AI: {data.get('answer', 'N/A')}"]
            for r in data.get("results", [])[:5]:
                results.append(f"[{r.get('title')}]({r.get('url')}): {r.get('content')}")
            
            return "\n\n".join(results)
    except Exception as e:
        logger.error(f"Tavily API error: {e}")
        return f"Error Tavily: {e}"


async def _search_ddg(query: str, is_live: bool) -> str:
    """Search using DuckDuckGo (free fallback)."""
    def _search(q):
        try:
            t_limit = 'd' if is_live else None
            return list(DDGS().text(q, max_results=7, timelimit=t_limit))
        except Exception:
            return []
            
    try:
        result = await asyncio.to_thread(_search, query)
        
        # Temporal window: early morning fallback to yesterday
        hour = datetime.now().hour
        if (not result or is_live) and hour < 10:
            logger.info("Early morning. Trying 'yesterday' search.")
            query_fallback = query.replace("hoy", "ayer") + " resultados ayer"
            fallback_res = await asyncio.to_thread(_search, query_fallback)
            if fallback_res:
                result = result + fallback_res

        if not result:
            return f"No se encontraron resultados para: {query}. Intenta ser más específico."
            
        formatted = ["Información obtenida (DDG):"]
        for r in result[:10]:
            formatted.append(f"- {r.get('title')}: {r.get('body')} (Fuente: {r.get('href')})")
            
        return "\n\n".join(formatted)
    except Exception as e:
        return f"Error en búsqueda DDG: {e}"
