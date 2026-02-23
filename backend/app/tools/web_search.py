"""
Tool 1 — Web Search
Uses DuckDuckGo (no API key required).
Returns top-5 results as a formatted string.
"""
from langchain.tools import tool
from duckduckgo_search import DDGS
from app.core.config import get_settings
import httpx

settings = get_settings()


@tool
def web_search(query: str) -> str:
    """
    Search the web for current information.
    Use this for news, recent events, factual lookups, or anything
    that requires up-to-date information.
    Input: a search query string.
    """
    # Prefer SerpAPI if key provided (more reliable than DDG and avoids 202 rate limit)
    if settings.SERPAPI_API_KEY:
        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": settings.SERPAPI_API_KEY,
                "num": 5,
            }
            resp = httpx.get("https://serpapi.com/search", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("organic_results", [])[:5]
            if not results:
                return "No results found for that query."
            out = []
            for i, r in enumerate(results, 1):
                out.append(
                    f"{i}. **{r.get('title', 'No title')}**\n"
                    f"   {r.get('snippet', '')}\n"
                    f"   Source: {r.get('link', '')}"
                )
            return "\n\n".join(out)
        except Exception as e:
            # fall through to DDG
            pass

    # DuckDuckGo fallback (no key)
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5, backend="api"))

        if not results:
            return "No results found for that query."

        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(
                f"{i}. **{r.get('title', 'No title')}**\n"
                f"   {r.get('body', '')}\n"
                f"   Source: {r.get('href', '')}"
            )
        return "\n\n".join(formatted)

    except Exception as e:
        return "Web search temporarily rate-limited; try again in 1-2 minutes or set SERPAPI_API_KEY."
