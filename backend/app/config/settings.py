import os
import secrets
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

# Resolve .env path relative to THIS file (backend/app/config/settings.py → backend/.env)
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "omni_copilot"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    NOTION_TOKEN: str = ""

    ENCRYPTION_KEY: str = ""
    SECRET_KEY: str = ""

    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    TIMEZONE: str = "Asia/Kolkata"

    class Config:
        env_file = str(_ENV_PATH)
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Ensure .env GROQ_API_KEY wins over any stale system env var
        try:
            from dotenv import dotenv_values
            env_vars = dotenv_values(str(_ENV_PATH))
            env_groq_key = env_vars.get("GROQ_API_KEY", "").strip()
            sys_groq_key = os.environ.get("GROQ_API_KEY", "").strip()
            if env_groq_key and env_groq_key != sys_groq_key:
                print(f"[INFO] Using GROQ_API_KEY from .env (overrides system env).")
                self.GROQ_API_KEY = env_groq_key
        except Exception as e:
            print(f"[WARNING] Could not read .env for GROQ key override: {e}")

        if not self.ENCRYPTION_KEY:
            self.ENCRYPTION_KEY = secrets.token_hex(32)
            print("[WARNING] ENCRYPTION_KEY not set — generated ephemeral key. Set it in .env for persistence.")
        if not self.SECRET_KEY:
            self.SECRET_KEY = secrets.token_hex(32)
            print("[WARNING] SECRET_KEY not set — generated ephemeral key. Set it in .env for persistence.")


settings = Settings()
