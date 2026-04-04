from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Google OAuth settings
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    # Google AI (Gemini) settings
    google_generative_ai_api_key: Optional[str] = None

    # MongoDB settings
    mongo_uri: str
    mongo_db_name: str

    # Trigger.dev settings
    trigger_api_key: Optional[str] = None
    trigger_api_url: str = "https://api.trigger.dev"
    trigger_webhook_secret: Optional[str] = None

    # Self-hosted worker settings (Trigger.dev replacement)
    worker_url: Optional[str] = None
    worker_secret: Optional[str] = None
    
    # Backend URL (for Trigger.dev callbacks)
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    # Optional settings
    debug: bool = False
    log_level: str = "INFO"

    # Scraper project directory (relative to Lead-contact or absolute)
    scraper_dir: str = "../Scraper"

    # Python executable used to launch the scraper subprocess
    scraper_python: str = "python"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
