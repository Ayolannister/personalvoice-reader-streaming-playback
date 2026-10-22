import hashlib
import json
import os
import time
import wave
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session


from app.config import get_settings
from app.database import SessionLocal, get_db
from app.models import Book, Chapter, Voice
from app.schemas import GenerateRequest
from app.tts import get_engine
from app.tts.audio_utils import concat_wavs_to_mp3
from app.tts.text_chunking import chunk_text

router = APIRouter()
settings = get_settings()

# CPU inference for a full chapter can take a long time (minutes to well
# over an hour). Rather than making the person wait for every segment
# before they can press play, publish a playable checkpoint after the
# very first segment, then again every CHECKPOINT_EVERY segments, so
# listening can start almost immediately while the rest keeps generating
# in the background. "partial" = playable now, more still coming;
# "cached" = fully done, terminal state.
CHECKPOINT_EVERY = 5


def _resolve_voice_id(book: Book, requested_voice_id: str | None) -> str:
    voice_id = requested_voice_id or book.voice_id
    if not voice_id:
        raise HTTPException(
            status_code=400,
            detail="This book has no voice assigned. Choose a voice first, or pass voiceId.",
        )
    return voice_id


def _publish_checkpoint(chapter: Chapter, segment_paths: list[Path], output_path: Path, is_final: bool) -> float:
    """
    Re-encodes everything synthesized so far into the chapter's audio
    file and atomically swaps it in, so a client mid-read never sees a
    half-written file. Returns the resulting duration in seconds.
    """
    tmp_path = output_path.with_suffix(f".tmp{os.getpid()}.mp3")
    duration = concat_wavs_to_mp3(segment_paths, tmp_path)
    os.replace(tmp_path, output_path)  # atomic on the same filesystem

    chapter.audio_path = str(output_path)
    chapter.duration_seconds = duration
    chapter.audio_status = "cached" if is_final else "partial"
    return duration


def _segment_is_complete(path: Path) -> bool:
    """A segment WAV left over from an earlier run, fully written and readable."""
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() > 0
    except Exception:
        return False


def _prepare_work_dir(work_dir: Path, segments: list[str], voice_id: str) -> None:
    """
    Segment WAVs are kept in work_dir until the chapter is fully done, so an
    interrupted generation can resume instead of starting over. They are only
    reusable if they came from the same text split and the same voice, so a
    manifest records both; on a mismatch the old segments are discarded.
    """
    fingerprint = hashlib.sha256(
        json.dumps({"voice": voice_id, "segments": segments}).encode("utf-8")
    ).hexdigest()
    manifest = work_dir / "manifest.json"
    work_dir.mkdir(parents=True, exist_ok=True)
    try:
        previous = json.loads(manifest.read_text()).get("fingerprint")
    except Exception:
        previous = None
    if previous != fingerprint:
        for old in work_dir.glob("segment_*.wav"):
            old.unlink(missing_ok=True)
        manifest.write_text(json.dumps({"fingerprint": fingerprint}))


def _run_generation(book_id: str, chapter_id: str, voice_id: str):
    """Runs after the response is sent; opens its own DB session."""
    db = SessionLocal()
    try:
        chapter = db.get(Chapter, chapter_id)
        voice = db.get(Voice, voice_id)
        if not chapter or not voice:
            return

        try:
            engine = get_engine()
            text = Path(chapter.text_path).read_text(encoding="utf-8")
            segments = chunk_text(text)
            if not segments:
                raise ValueError("This chapter has no text to synthesize")

            chapter.generation_segments_done = 0
            chapter.generation_segments_total = len(segments)
            db.commit()

            work_dir = settings.audio_dir / f"{book_id}_{chapter_id}_segments"
            _prepare_work_dir(work_dir, segments, voice_id)
            output_path = settings.audio_dir / f"{chapter_id}.mp3"
            segment_paths = []
            published_this_run = False

            for i, segment in enumerate(segments):
                seg_path = work_dir / f"segment_{i:04d}.wav"
                reused = _segment_is_complete(seg_path)

                if reused:
                    print(f"Reusing chunk {i + 1}/{len(segments)} from an earlier run", flush=True)
                else:
                    start = time.time()
                    print(f"\nGenerating chunk {i + 1}/{len(segments)}", flush=True)
                    # Write to a temp name and rename, so a stop mid-write
                    # never leaves a truncated segment that looks finished.
                    tmp_seg = seg_path.with_suffix(".partial.wav")
                    engine.synthesize(segment, Path(voice.model_path), tmp_seg)
                    os.replace(tmp_seg, seg_path)
                    print(f"Chunk {i + 1} finished in {time.time() - start:.2f} seconds", flush=True)

                segment_paths.append(seg_path)
                chapter.generation_segments_done = i + 1

                is_last = i == len(segments) - 1
                is_checkpoint = is_last or (
                    not reused and (not published_this_run or (i + 1) % CHECKPOINT_EVERY == 0)
                )
                if is_checkpoint:
                    checkpoint_start = time.time()
                    _publish_checkpoint(chapter, segment_paths, output_path, is_final=is_last)
                    published_this_run = True
                    print(
                        f"Published checkpoint through segment {i + 1} "
                        f"({chapter.duration_seconds:.1f}s of audio) in "
                        f"{time.time() - checkpoint_start:.2f}s",
                        flush=True,
                    )

                db.commit()

            for p in work_dir.iterdir():
                p.unlink(missing_ok=True)
            work_dir.rmdir()
        except Exception:
            chapter.audio_status = "not_generated"
            raise
        finally:
            db.commit()
    finally:
        db.close()


@router.post("/books/{book_id}/chapters/{chapter_id}/generate")
def generate_chapter_audio(
    book_id: str,
    chapter_id: str,
    payload: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    chapter = db.get(Chapter, chapter_id)
    if not chapter or chapter.book_id != book_id:
        raise HTTPException(status_code=404, detail="Chapter not found")
    if chapter.audio_status in ("generating", "partial"):
        raise HTTPException(status_code=409, detail="This chapter is already generating")
    if chapter.audio_status == "cached" and Path(chapter.audio_path or "").exists():
        return {"status": "cached"}  # already generated, nothing to do

    voice_id = _resolve_voice_id(book, payload.voiceId)
    voice = db.get(Voice, voice_id)
    if not voice or voice.status != "ready":
        raise HTTPException(status_code=400, detail="The assigned voice isn't trained yet")

    chapter.audio_status = "generating"
    db.commit()

    background_tasks.add_task(_run_generation, book_id, chapter_id, voice_id)
    return {"status": "generating"}


@router.get("/books/{book_id}/chapters/{chapter_id}/audio")
def stream_chapter_audio(book_id: str, chapter_id: str, db: Session = Depends(get_db)):
    chapter = db.get(Chapter, chapter_id)
    if not chapter or chapter.book_id != book_id:
        raise HTTPException(status_code=404, detail="Chapter not found")
    # "partial" is playable too — a checkpoint has already been published,
    # even though more segments are still generating in the background.
    if chapter.audio_status not in ("cached", "partial") or not chapter.audio_path or not Path(chapter.audio_path).exists():
        raise HTTPException(status_code=404, detail="Audio for this chapter hasn't been generated yet")

    # FileResponse supports HTTP Range requests, which real <audio>
    # elements rely on for seeking/scrubbing without downloading the
    # whole file first.
    return FileResponse(chapter.audio_path, media_type="audio/mpeg")
