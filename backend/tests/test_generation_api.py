import os
import tempfile
import time
import wave

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mktemp(suffix='.db')}")
os.environ["TTS_ENGINE"] = "dummy"

from app.config import get_settings

get_settings.cache_clear()

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_wav(path, seconds=2, framerate=16000):
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(framerate)
        f.writeframes(b"\x00\x00" * framerate * seconds)


def _upload_book(tmp_path):
    content = (
        "Chapter 1\n" + ("Once upon a time in a small town. " * 15) +
        "\n\nChapter 2\n" + ("The story continued for a while. " * 15)
    ).encode("utf-8")
    resp = client.post("/books", files={"file": ("gen_test_book.txt", content, "text/plain")})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _upload_and_train_voice(tmp_path):
    wav_path = tmp_path / "gen_test_voice.wav"
    _make_wav(wav_path, seconds=3)
    with wav_path.open("rb") as f:
        resp = client.post(
            "/voices",
            data={"name": "Gen test voice"},
            files={"file": ("gen_test_voice.wav", f, "audio/wav")},
        )
    assert resp.status_code == 201, resp.text
    voice = resp.json()
    train_resp = client.post(f"/voices/{voice['id']}/train")
    assert train_resp.status_code == 200
    return client.get(f"/voices/{voice['id']}").json()


def test_generate_chapter_audio_end_to_end(tmp_path):
    book = _upload_book(tmp_path)
    voice = _upload_and_train_voice(tmp_path)
    assert voice["status"] == "ready"

    assign_resp = client.patch(f"/books/{book['id']}/voice", json={"voiceId": voice["id"]})
    assert assign_resp.status_code == 200
    assert assign_resp.json()["voiceId"] == voice["id"]

    chapter_id = book["chapters"][0]["id"]

    gen_resp = client.post(f"/books/{book['id']}/chapters/{chapter_id}/generate", json={})
    assert gen_resp.status_code == 200
    assert gen_resp.json()["status"] == "generating"

    # BackgroundTasks in TestClient complete before the response returns,
    # so the chapter should already be cached on the next fetch.
    book_after = client.get(f"/books/{book['id']}").json()
    chapter_after = next(c for c in book_after["chapters"] if c["id"] == chapter_id)
    assert chapter_after["audioStatus"] == "cached"
    assert chapter_after["durationSeconds"] and chapter_after["durationSeconds"] > 0
    assert chapter_after["generationSegmentsTotal"] is not None
    assert chapter_after["generationSegmentsDone"] == chapter_after["generationSegmentsTotal"]

    audio_resp = client.get(f"/books/{book['id']}/chapters/{chapter_id}/audio")
    assert audio_resp.status_code == 200
    assert audio_resp.headers["content-type"] == "audio/mpeg"
    assert len(audio_resp.content) > 0

    # <audio> seeking depends on HTTP Range support (206 Partial Content).
    # Starlette < 0.39 silently ignored Range and always sent the whole file.
    range_resp = client.get(
        f"/books/{book['id']}/chapters/{chapter_id}/audio", headers={"Range": "bytes=0-99"}
    )
    assert range_resp.status_code == 206
    assert len(range_resp.content) == 100
    assert range_resp.content == audio_resp.content[:100]


def test_generate_requires_a_voice(tmp_path):
    book = _upload_book(tmp_path)
    chapter_id = book["chapters"][0]["id"]

    resp = client.post(f"/books/{book['id']}/chapters/{chapter_id}/generate", json={})
    assert resp.status_code == 400
    assert "no voice assigned" in resp.json()["detail"]


def test_generate_rejects_double_submission(tmp_path):
    book = _upload_book(tmp_path)
    voice = _upload_and_train_voice(tmp_path)
    client.patch(f"/books/{book['id']}/voice", json={"voiceId": voice["id"]})

    chapter_id = book["chapters"][1]["id"]

    # Simulate an in-flight generation directly, since TestClient's
    # background tasks otherwise complete synchronously before we could
    # observe the "generating" state.
    from app.database import SessionLocal
    from app.models import Chapter

    db = SessionLocal()
    ch = db.get(Chapter, chapter_id)
    ch.audio_status = "generating"
    db.commit()
    db.close()

    resp = client.post(f"/books/{book['id']}/chapters/{chapter_id}/generate", json={})
    assert resp.status_code == 409


def test_audio_streaming_404s_before_generation(tmp_path):
    book = _upload_book(tmp_path)
    chapter_id = book["chapters"][0]["id"]

    resp = client.get(f"/books/{book['id']}/chapters/{chapter_id}/audio")
    assert resp.status_code == 404
