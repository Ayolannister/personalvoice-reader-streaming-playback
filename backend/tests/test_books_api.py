import os
import tempfile

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mktemp(suffix='.db')}")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_upload_txt_book_and_list():
    content = (
        "Chapter 1\n" + ("Once upon a time in a small town. " * 15) +
        "\n\nChapter 2\n" + ("The story continued for a while. " * 15)
    ).encode("utf-8")

    resp = client.post(
        "/books",
        files={"file": ("mybook.txt", content, "text/plain")},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["format"] == "txt"
    assert len(body["chapters"]) == 2
    assert body["currentChapterId"] == body["chapters"][0]["id"]
    # titled after the uploaded file, not the internal storage ID
    assert body["title"] == "mybook"

    list_resp = client.get("/books")
    assert list_resp.status_code == 200
    assert any(b["id"] == body["id"] for b in list_resp.json())


def test_upload_rejects_unsupported_format():
    resp = client.post(
        "/books",
        files={"file": ("notes.docx", b"irrelevant", "application/octet-stream")},
    )
    assert resp.status_code == 400
