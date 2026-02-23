from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    GEMINI_MODEL: str = "gemini-flash-latest"
    GEMINI_FALLBACK_MODELS: str = "gemini-2.0-flash,gemini-1.5-pro-latest"
    GEMINI_MAX_RETRIES: int = 0
    SERPAPI_API_KEY: str = ""

    # External API keys (optional — agent degrades gracefully without them)
    OPENWEATHER_API_KEY: str = ""
    NEWS_API_KEY: str = ""         # newsapi.org free tier

    # Agent
    MAX_ITERATIONS: int = 8        # prevent infinite loops
    AGENT_VERBOSE: bool = True

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
