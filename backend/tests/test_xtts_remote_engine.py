import os
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mktemp(suffix='.db')}")
os.environ["TTS_SERVICE_URL"] = "http://127.0.0.1:8901"

from app.config import get_settings

get_settings.cache_clear()

from app.tts.xtts_remote_engine import XTTSRemoteEngine


@pytest.fixture(scope="module")
def mock_tts_server():
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mock_tts_service:app", "--port", "8901"],
        cwd=str(Path(__file__).resolve().parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        try:
            httpx.get("http://127.0.0.1:8901/health", timeout=1)
            break
        except httpx.RequestError:
            time.sleep(0.2)
    yield
    proc.terminate()
    proc.wait(timeout=5)


def _make_wav(path):
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(b"\x01\x02" * 1000)


def test_remote_engine_clone_roundtrip(mock_tts_server, tmp_path):
    wav_path = tmp_path / "source.wav"
    _make_wav(wav_path)

    engine = XTTSRemoteEngine()
    result = engine.clone(wav_path, tmp_path / "profile")

    assert result.engine == "xtts_remote"
    artifact = Path(result.artifact_path)
    assert artifact.exists()
    assert artifact.read_bytes().startswith(b"FAKE_TORCH_TENSOR_BYTES:")


def test_remote_engine_raises_clear_error_when_unreachable(tmp_path):
    os.environ["TTS_SERVICE_URL"] = "http://127.0.0.1:9999"  # nothing listening here
    get_settings.cache_clear()

    wav_path = tmp_path / "source2.wav"
    _make_wav(wav_path)

    engine = XTTSRemoteEngine()
    with pytest.raises(RuntimeError, match="Couldn't reach the TTS service"):
        engine.clone(wav_path, tmp_path / "profile2")

    os.environ["TTS_SERVICE_URL"] = "http://127.0.0.1:8901"
    get_settings.cache_clear()
