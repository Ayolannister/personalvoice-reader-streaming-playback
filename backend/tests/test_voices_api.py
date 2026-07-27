import os
import tempfile
import wave

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mktemp(suffix='.db')}")
os.environ["TTS_ENGINE"] = "dummy"

from app.config import get_settings

get_settings.cache_clear()  # earlier test-module imports may have cached settings without TTS_ENGINE set

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_wav(path, seconds=2, framerate=16000):
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(framerate)
        f.writeframes(b"\x00\x00" * framerate * seconds)


def test_upload_voice_and_train_with_dummy_engine(tmp_path):
    had_existing_voices = len(client.get("/voices").json()) > 0

    wav_path = tmp_path / "sample.wav"
    _make_wav(wav_path, seconds=3)

    with wav_path.open("rb") as f:
        resp = client.post(
            "/voices",
            data={"name": "Test voice", "language": "English"},
            files={"file": ("sample.wav", f, "audio/wav")},
        )
    assert resp.status_code == 201, resp.text
    voice = resp.json()
    assert voice["status"] == "untrained"
    # Only the very first voice in the whole DB auto-becomes default —
    # other test files sharing this DB may have already created one.
    assert voice["isDefault"] is (not had_existing_voices)
    assert voice["sourceMinutes"] > 0

    train_resp = client.post(f"/voices/{voice['id']}/train")
    assert train_resp.status_code == 200
    assert train_resp.json()["status"] == "training"

    # BackgroundTasks in TestClient run synchronously before the response
    # is returned to the caller, so status should already reflect the
    # outcome on the next GET.
    get_resp = client.get(f"/voices/{voice['id']}")
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["status"] == "ready"
    assert body["errorMessage"] is None


def test_train_rejects_double_submission(tmp_path):
    wav_path = tmp_path / "sample2.wav"
    _make_wav(wav_path, seconds=2)

    with wav_path.open("rb") as f:
        resp = client.post(
            "/voices",
            data={"name": "Second voice"},
            files={"file": ("sample2.wav", f, "audio/wav")},
        )
    voice_id = resp.json()["id"]

    # First train call completes synchronously in TestClient, so simulate
    # an in-flight state directly to test the guard.
    from app.database import SessionLocal
    from app.models import Voice

    db = SessionLocal()
    v = db.get(Voice, voice_id)
    v.status = "training"
    db.commit()
    db.close()

    resp = client.post(f"/voices/{voice_id}/train")
    assert resp.status_code == 409


def test_upload_rejects_unsupported_audio_format():
    resp = client.post(
        "/voices",
        data={"name": "Bad format"},
        files={"file": ("clip.ogg", b"irrelevant", "audio/ogg")},
    )
    assert resp.status_code == 400


def test_set_default_requires_ready_status(tmp_path):
    wav_path = tmp_path / "sample3.wav"
    _make_wav(wav_path, seconds=1)

    with wav_path.open("rb") as f:
        resp = client.post(
            "/voices",
            data={"name": "Untrained voice"},
            files={"file": ("sample3.wav", f, "audio/wav")},
        )
    voice_id = resp.json()["id"]

    resp = client.patch(f"/voices/{voice_id}/default")
    assert resp.status_code == 400


def test_long_reference_recording_gets_trimmed_before_cloning(tmp_path):
    """
    Regression test: cloning against the full source file (this app
    recommends 45-90 minute uploads) means loading the whole thing into
    memory before the engine trims it internally to ~30s, which can OOM
    on memory-constrained environments. The router should trim to a
    short clip on disk first.
    """
    long_wav_path = tmp_path / "long_sample.wav"
    _make_wav(long_wav_path, seconds=150, framerate=8000)  # ~2.5 min fixture, keeps the test fast

    with long_wav_path.open("rb") as f:
        resp = client.post(
            "/voices",
            data={"name": "Long recording voice"},
            files={"file": ("long_sample.wav", f, "audio/wav")},
        )
    assert resp.status_code == 201
    voice_id = resp.json()["id"]

    train_resp = client.post(f"/voices/{voice_id}/train")
    assert train_resp.status_code == 200

    voice = client.get(f"/voices/{voice_id}").json()
    assert voice["status"] == "ready", voice.get("errorMessage")

    from app.config import get_settings

    trimmed_path = get_settings().voices_dir / voice_id / "clone_reference.wav"
    assert trimmed_path.exists()

    import wave as wave_module

    with wave_module.open(str(trimmed_path), "rb") as f:
        trimmed_seconds = f.getnframes() / f.getframerate()
    assert trimmed_seconds <= 90.5  # CLONE_REFERENCE_SECONDS + small ffmpeg rounding tolerance
