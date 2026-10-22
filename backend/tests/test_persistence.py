"""
Work survives the app stopping: stuck statuses are reset on startup, and
an interrupted chapter resumes from the segments it already synthesized
instead of starting over.
"""
import os
import tempfile
import wave
from pathlib import Path

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mktemp(suffix='.db')}")
os.environ["TTS_ENGINE"] = "dummy"

from app.config import get_settings

get_settings.cache_clear()

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Chapter, Voice
from app.recovery import recover_interrupted_jobs
from app.routers import generation
from app.tts.dummy_engine import DummyEngine

client = TestClient(app)
settings = get_settings()


def _make_wav(path, seconds=2, rate=16000):
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"\x00\x00" * rate * seconds)


def _book_with_ready_voice(tmp_path, name):
    # Long enough to split into several TTS segments.
    body = " ".join(f"Sentence number {i} goes on for a little while longer." for i in range(60))
    content = f"Chapter 1\n{body}\n\nChapter 2\n{body}\n".encode()
    book = client.post("/books", files={"file": (f"{name}.txt", content, "text/plain")}).json()

    wav = tmp_path / f"{name}.wav"
    _make_wav(wav)
    with wav.open("rb") as f:
        voice = client.post("/voices", data={"name": name}, files={"file": (wav.name, f, "audio/wav")}).json()
    client.post(f"/voices/{voice['id']}/train")
    client.patch(f"/books/{book['id']}/voice", json={"voiceId": voice["id"]})
    return book, voice


class CountingEngine(DummyEngine):
    """Dummy engine that counts calls and can 'crash' at a given segment."""

    def __init__(self, crash_on_call=None):
        self.calls = 0
        self.crash_on_call = crash_on_call

    def synthesize(self, text, voice_profile_path, output_wav_path):
        self.calls += 1
        if self.crash_on_call is not None and self.calls == self.crash_on_call:
            raise RuntimeError("simulated stop")
        super().synthesize(text, voice_profile_path, output_wav_path)


def _set_status(model, obj_id, **fields):
    with SessionLocal() as db:
        row = db.get(model, obj_id)
        for k, v in fields.items():
            setattr(row, k, v)
        db.commit()


def _chapter(book_id, chapter_id):
    return next(c for c in client.get(f"/books/{book_id}").json()["chapters"] if c["id"] == chapter_id)


def test_startup_recovery_unsticks_voices_and_chapters(tmp_path):
    book, voice = _book_with_ready_voice(tmp_path, "recovery")
    ch1, ch2 = book["chapters"][0]["id"], book["chapters"][1]["id"]

    # What the database looks like after a stop mid-way through each job.
    _set_status(Voice, voice["id"], status="training")
    _set_status(Chapter, ch1, audio_status="generating")
    _set_status(Chapter, ch2, audio_status="partial")

    # Stuck: the API refuses to restart either job.
    assert client.post(f"/voices/{voice['id']}/train").status_code == 409
    assert client.post(f"/books/{book['id']}/chapters/{ch1}/generate", json={}).status_code == 409

    with SessionLocal() as db:
        counts = recover_interrupted_jobs(db)
    assert counts["voices"] >= 1 and counts["chapters"] >= 2

    v = client.get(f"/voices/{voice['id']}").json()
    assert v["status"] == "failed"
    assert "interrupted" in v["errorMessage"]
    assert _chapter(book["id"], ch1)["audioStatus"] == "not_generated"
    assert _chapter(book["id"], ch2)["audioStatus"] == "not_generated"

    # Both can be started again.
    assert client.post(f"/voices/{voice['id']}/train").status_code == 200
    assert client.post(f"/books/{book['id']}/chapters/{ch1}/generate", json={}).status_code == 200


def test_interrupted_generation_resumes_without_redoing_segments(tmp_path, monkeypatch):
    book, voice = _book_with_ready_voice(tmp_path, "resume")
    chapter_id = book["chapters"][0]["id"]

    # First run "crashes" on its 4th segment: 3 segments are finished.
    first = CountingEngine(crash_on_call=4)
    monkeypatch.setattr(generation, "get_engine", lambda: first)
    try:
        client.post(f"/books/{book['id']}/chapters/{chapter_id}/generate", json={})
    except RuntimeError:
        pass  # TestClient re-raises background task errors
    total = _chapter(book["id"], chapter_id)["generationSegmentsTotal"]
    assert total > 4, "fixture text should split into more than 4 segments"
    assert _chapter(book["id"], chapter_id)["audioStatus"] == "not_generated"

    # Second run only synthesizes what's missing.
    second = CountingEngine()
    monkeypatch.setattr(generation, "get_engine", lambda: second)
    client.post(f"/books/{book['id']}/chapters/{chapter_id}/generate", json={})

    after = _chapter(book["id"], chapter_id)
    assert after["audioStatus"] == "cached"
    assert second.calls == total - 3
    assert client.get(f"/books/{book['id']}/chapters/{chapter_id}/audio").status_code == 200
    # Work files are cleaned up once the chapter is complete.
    assert not (settings.audio_dir / f"{book['id']}_{chapter_id}_segments").exists()


def test_truncated_segment_is_regenerated_not_reused(tmp_path, monkeypatch):
    book, voice = _book_with_ready_voice(tmp_path, "truncated")
    chapter_id = book["chapters"][0]["id"]

    first = CountingEngine(crash_on_call=3)
    monkeypatch.setattr(generation, "get_engine", lambda: first)
    try:
        client.post(f"/books/{book['id']}/chapters/{chapter_id}/generate", json={})
    except RuntimeError:
        pass
    total = _chapter(book["id"], chapter_id)["generationSegmentsTotal"]

    # Simulate a stop mid-write: segment 2 is a corrupt half-file.
    seg = settings.audio_dir / f"{book['id']}_{chapter_id}_segments" / "segment_0001.wav"
    seg.write_bytes(b"RIFF\x00\x00")

    second = CountingEngine()
    monkeypatch.setattr(generation, "get_engine", lambda: second)
    client.post(f"/books/{book['id']}/chapters/{chapter_id}/generate", json={})
    assert _chapter(book["id"], chapter_id)["audioStatus"] == "cached"
    assert second.calls == total - 1  # only segment 1 reused


def test_changing_voice_discards_old_segments(tmp_path, monkeypatch):
    book, voice = _book_with_ready_voice(tmp_path, "voiceswap")
    chapter_id = book["chapters"][0]["id"]

    first = CountingEngine(crash_on_call=4)
    monkeypatch.setattr(generation, "get_engine", lambda: first)
    try:
        client.post(f"/books/{book['id']}/chapters/{chapter_id}/generate", json={})
    except RuntimeError:
        pass
    total = _chapter(book["id"], chapter_id)["generationSegmentsTotal"]

    # Switch the book to a different voice, then generate again.
    wav = tmp_path / "other.wav"
    _make_wav(wav)
    with wav.open("rb") as f:
        other = client.post("/voices", data={"name": "other"}, files={"file": ("other.wav", f, "audio/wav")}).json()
    client.post(f"/voices/{other['id']}/train")
    client.patch(f"/books/{book['id']}/voice", json={"voiceId": other["id"]})

    second = CountingEngine()
    monkeypatch.setattr(generation, "get_engine", lambda: second)
    client.post(f"/books/{book['id']}/chapters/{chapter_id}/generate", json={})
    assert second.calls == total  # nothing from the old voice was mixed in
