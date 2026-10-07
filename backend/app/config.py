"""App settings — env vars with the `WA_` prefix. Mirrors lawtrack-ai's `app/config.py`: a
gitignored `.env` is loaded manually (pydantic-settings' own env-file support isn't used so the
same loader can run standalone from `pipeline/` scripts)."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parents[1]


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and val:
            os.environ.setdefault(key, val)


_load_env_file(_BACKEND_DIR / ".env")

_DEV_JWT_SECRET = "change-me-in-production"


class Settings(BaseSettings):
    database_url: str = "sqlite:///./whatsapp_assistant.db"
    jwt_secret: str = _DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    seed_on_startup: bool = True
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3002"]
    storage_dir: str = "./storage"
    log_level: str = "info"

    model_config = {"env_prefix": "WA_"}

    @property
    def jwt_is_dev_default(self) -> bool:
        return self.jwt_secret == _DEV_JWT_SECRET


@lru_cache
def get_settings() -> Settings:
    return Settings()
