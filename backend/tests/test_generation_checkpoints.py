import wave
from pathlib import Path

from app.models import Chapter
from app.routers.generation import _publish_checkpoint


def _make_wav(path: Path, seconds: float, framerate: int = 8000):
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(framerate)
        f.writeframes(b"\x00\x00" * int(framerate * seconds))


def test_publish_checkpoint_marks_partial_when_not_final(tmp_path):
    seg1 = tmp_path / "seg1.wav"
    _make_wav(seg1, seconds=2)

    chapter = Chapter(id="c1", book_id="b1", index=1, title="Ch 1", text_path="unused")
    output_path = tmp_path / "chapter.mp3"

    duration = _publish_checkpoint(chapter, [seg1], output_path, is_final=False)

    assert chapter.audio_status == "partial"
    assert chapter.audio_path == str(output_path)
    assert output_path.exists()
    assert abs(duration - 2.0) < 0.05


def test_publish_checkpoint_marks_cached_when_final(tmp_path):
    seg1 = tmp_path / "seg1.wav"
    seg2 = tmp_path / "seg2.wav"
    _make_wav(seg1, seconds=2)
    _make_wav(seg2, seconds=3)

    chapter = Chapter(id="c1", book_id="b1", index=1, title="Ch 1", text_path="unused")
    output_path = tmp_path / "chapter.mp3"

    duration = _publish_checkpoint(chapter, [seg1, seg2], output_path, is_final=True)

    assert chapter.audio_status == "cached"
    assert abs(duration - 5.0) < 0.1


def test_publish_checkpoint_is_atomic_no_partial_file_visible(tmp_path):
    """The output path should never exist in a half-written state — the
    helper writes to a temp path and atomically renames it into place."""
    seg1 = tmp_path / "seg1.wav"
    _make_wav(seg1, seconds=1)

    chapter = Chapter(id="c1", book_id="b1", index=1, title="Ch 1", text_path="unused")
    output_path = tmp_path / "chapter.mp3"

    _publish_checkpoint(chapter, [seg1], output_path, is_final=False)

    # No leftover .tmp* files should remain after a successful publish
    leftover_tmp_files = list(tmp_path.glob("chapter.tmp*"))
    assert leftover_tmp_files == []
