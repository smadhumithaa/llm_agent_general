"""
Tool 2 — Weather  (OpenWeatherMap)
Tool 3 — News     (NewsAPI)
Both degrade gracefully if API keys are missing.
"""
import httpx
from langchain.tools import tool
from app.core.config import get_settings

settings = get_settings()


# ── Weather ───────────────────────────────────────────────────────────────────
@tool
def get_weather(city: str) -> str:
    """
    Get the current weather for a city.
    Input: city name (e.g. "London" or "New York,US").
    Returns temperature, conditions, humidity, and wind speed.
    """
    if not settings.OPENWEATHER_API_KEY:
        return "Weather tool unavailable: OPENWEATHER_API_KEY not set."

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        name    = data["name"]
        country = data["sys"]["country"]
        temp    = data["main"]["temp"]
        feels   = data["main"]["feels_like"]
        desc    = data["weather"][0]["description"].capitalize()
        humidity= data["main"]["humidity"]
        wind    = data["wind"]["speed"]

        return (
            f"Weather in {name}, {country}:\n"
            f"  🌡  Temperature: {temp}°C (feels like {feels}°C)\n"
            f"  ☁️  Conditions: {desc}\n"
            f"  💧 Humidity: {humidity}%\n"
            f"  💨 Wind: {wind} m/s"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"City '{city}' not found. Try a different spelling."
        return f"Weather API error: {e}"
    except Exception as e:
        return f"Weather tool failed: {str(e)}"


# ── News ──────────────────────────────────────────────────────────────────────
@tool
def get_news(topic: str) -> str:
    """
    Get the latest news headlines for a topic.
    Input: a topic or keyword (e.g. "AI regulation", "stock market").
    Returns up to 5 recent headlines with descriptions.
    """
    if not settings.NEWS_API_KEY:
        return "News tool unavailable: NEWS_API_KEY not set."

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": topic,
        "apiKey": settings.NEWS_API_KEY,
        "pageSize": 5,
        "sortBy": "publishedAt",
        "language": "en",
    }

    try:
        resp = httpx.get(url, params=params, timeout=10)
        if resp.status_code == 401:
            return "News tool unavailable: NEWS_API_KEY is invalid or inactive."
        resp.raise_for_status()
        articles = resp.json().get("articles", [])

        if not articles:
            return f"No recent news found for '{topic}'."

        lines = [f"Latest news on '{topic}':\n"]
        for i, a in enumerate(articles, 1):
            title  = a.get("title", "No title")
            source = a.get("source", {}).get("name", "Unknown")
            desc   = a.get("description") or ""
            url_   = a.get("url", "")
            lines.append(
                f"{i}. [{source}] {title}\n"
                f"   {desc[:120]}...\n"
                f"   {url_}"
            )
        return "\n\n".join(lines)

    except Exception as e:
        return f"News tool failed: {str(e)}"
