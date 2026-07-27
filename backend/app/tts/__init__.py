from app.config import get_settings
from app.tts.base import VoiceCloningEngine


def get_engine() -> VoiceCloningEngine:
    settings = get_settings()
    if settings.tts_engine == "dummy":
        from app.tts.dummy_engine import DummyEngine

        return DummyEngine()

    if settings.tts_engine == "xtts_remote":
        from app.tts.xtts_remote_engine import XTTSRemoteEngine

        return XTTSRemoteEngine()

    from app.tts.xtts_engine import XTTSEngine

    return XTTSEngine()
