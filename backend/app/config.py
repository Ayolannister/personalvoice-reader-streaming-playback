from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # SQLite for local dev now; swap to a Postgres DSN later without code
    # changes elsewhere, since we only use SQLAlchemy-portable types.
    database_url: str = f"sqlite:///{BASE_DIR / 'app' / 'storage' / 'voicereader.db'}"

    storage_dir: Path = BASE_DIR / "app" / "storage"
    books_dir: Path = BASE_DIR / "app" / "storage" / "books"
    covers_dir: Path = BASE_DIR / "app" / "storage" / "covers"
    audio_dir: Path = BASE_DIR / "app" / "storage" / "audio"
    voices_dir: Path = BASE_DIR / "app" / "storage" / "voices"

    cors_origins: list[str] = ["http://localhost:3000"]

    # "xtts" for in-process Coqui XTTS v2 (needs requirements-tts.txt —
    # works fine on Python 3.12, coqui-tts 0.24.2 supports 3.9-3.12).
    # "xtts_remote" calls out to the dockerized TTS service instead, so
    # the ~5GB dependency stack stays out of the backend's environment.
    # "dummy" computes a lightweight fake profile for pipeline dev/tests.
    tts_engine: str = "xtts"
    tts_service_url: str = "http://localhost:8001"

    # XTTS v2 on CPU is genuinely slow (often well under real-time), so
    # these default high — a timeout here doesn't speed anything up, it
    # just determines when "still working" gets misreported as "down".
    tts_clone_timeout_seconds: int = 900
    tts_synthesize_timeout_seconds: int = 900


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    for d in (settings.storage_dir, settings.books_dir, settings.covers_dir, settings.audio_dir, settings.voices_dir):
        d.mkdir(parents=True, exist_ok=True)
    return settings
