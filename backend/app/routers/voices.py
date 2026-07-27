import shutil
import subprocess
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal, get_db
from app.models import Voice
from app.schemas import VoiceOut
from app.tts import get_engine

router = APIRouter()
settings = get_settings()

SUPPORTED_AUDIO = {"wav", "mp3", "flac"}
MIN_RECOMMENDED_MINUTES = 45

# XTTS v2's get_conditioning_latents defaults to a 30-second reference
# window (max_ref_length=30) — anything beyond that is discarded anyway.
# Cloning against the full source recording (routinely 45-90 minutes per
# the app's own upload guidance) means loading and resampling all of it
# into memory first, which is wasteful and can OOM on memory-constrained
# environments (many Docker setups default to 2-4GB). Trimming to a
# short clip up front avoids that entirely.
CLONE_REFERENCE_SECONDS = 90


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _audio_minutes(path: Path) -> float:
    try:
        from mutagen import File as MutagenFile

        audio = MutagenFile(path)
        if audio is not None and audio.info is not None:
            return audio.info.length / 60
    except Exception:
        pass
    return 0.0


@router.get("/voices", response_model=list[VoiceOut])
def list_voices(db: Session = Depends(get_db)):
    voices = db.execute(select(Voice)).scalars().all()
    return [VoiceOut.from_model(v) for v in voices]


@router.get("/voices/{voice_id}", response_model=VoiceOut)
def get_voice(voice_id: str, db: Session = Depends(get_db)):
    voice = db.get(Voice, voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    return VoiceOut.from_model(voice)


@router.post("/voices", response_model=VoiceOut, status_code=201)
async def upload_voice(
    file: UploadFile,
    name: str = Form(...),
    language: str = Form("English"),
    db: Session = Depends(get_db),
):
    ext = _extension(file.filename or "")
    if ext not in SUPPORTED_AUDIO:
        raise HTTPException(status_code=400, detail=f"Unsupported audio type: .{ext}. Use WAV, MP3, or FLAC.")

    voice_id = str(uuid.uuid4())
    voice_dir = settings.voices_dir / voice_id
    voice_dir.mkdir(parents=True, exist_ok=True)
    dest_path = voice_dir / f"source.{ext}"
    with dest_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    minutes = _audio_minutes(dest_path)

    is_first_voice = db.execute(select(Voice)).first() is None

    voice = Voice(
        id=voice_id,
        name=name,
        language=language,
        source_path=str(dest_path),
        source_minutes=minutes,
        status="untrained",
        is_default=is_first_voice,
    )
    db.add(voice)
    db.commit()
    db.refresh(voice)
    return VoiceOut.from_model(voice)


def _trim_reference_audio(source_path: Path, output_path: Path, seconds: int = CLONE_REFERENCE_SECONDS) -> Path:
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(source_path),
                "-t", str(seconds),
                "-ac", "1",  # mono — halves memory vs. loading original stereo
                str(output_path),
            ],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg is not installed or not on PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Couldn't trim the reference recording: {exc.stderr.decode(errors='replace')[-500:]}") from exc
    return output_path


def _run_cloning(voice_id: str):
    """Runs after the response is sent. Opens its own DB session since the
    request-scoped one is closed by then."""
    db = SessionLocal()
    try:
        voice = db.get(Voice, voice_id)
        if not voice:
            return
        try:
            voice_dir = settings.voices_dir / voice_id
            trimmed_path = voice_dir / "clone_reference.wav"
            _trim_reference_audio(Path(voice.source_path), trimmed_path)

            engine = get_engine()
            result = engine.clone(trimmed_path, voice_dir / "profile")
            voice.status = "ready"
            voice.model_path = result.artifact_path
            voice.error_message = None
        except Exception as exc:
            voice.status = "failed"
            voice.error_message = str(exc)[:500]
        db.commit()
    finally:
        db.close()


@router.post("/voices/{voice_id}/train", response_model=VoiceOut)
def train_voice(voice_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    voice = db.get(Voice, voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    if voice.status == "training":
        raise HTTPException(status_code=409, detail="This voice is already training")

    voice.status = "training"
    voice.error_message = None
    db.commit()
    db.refresh(voice)

    background_tasks.add_task(_run_cloning, voice_id)
    return VoiceOut.from_model(voice)


@router.patch("/voices/{voice_id}/default", response_model=VoiceOut)
def set_default_voice(voice_id: str, db: Session = Depends(get_db)):
    voice = db.get(Voice, voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    if voice.status != "ready":
        raise HTTPException(status_code=400, detail="Only a trained voice can be set as default")

    db.query(Voice).update({Voice.is_default: False})
    voice.is_default = True
    db.commit()
    db.refresh(voice)
    return VoiceOut.from_model(voice)


@router.delete("/voices/{voice_id}", status_code=204)
def delete_voice(voice_id: str, db: Session = Depends(get_db)):
    voice = db.get(Voice, voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    voice_dir = settings.voices_dir / voice_id
    if voice_dir.exists():
        shutil.rmtree(voice_dir, ignore_errors=True)
    db.delete(voice)
    db.commit()
