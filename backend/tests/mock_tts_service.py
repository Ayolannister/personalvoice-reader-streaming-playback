"""
Stand-in for worker/tts-service with the same HTTP API (/health, /clone,
/synthesize) but no model. Lets the backend's xtts_remote engine be
tested end to end without the ~5GB torch/XTTS stack.

/synthesize returns a real WAV (a quiet 440Hz tone sized to the text),
so downstream ffmpeg concatenation and MP3 encoding get exercised on
actual audio, not empty files.

Run standalone:  uvicorn mock_tts_service:app --port 8001  (from tests/)
"""
import io
import math
import struct
import wave

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI(title="Mock TTS service")

PROFILE_PREFIX = b"FAKE_TORCH_TENSOR_BYTES:"
SAMPLE_RATE = 24000  # matches the real service's XTTS output rate
WORDS_PER_SECOND = 2.5


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": True}


@app.post("/clone")
async def clone(file: UploadFile):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty reference audio")
    return Response(PROFILE_PREFIX + str(len(data)).encode(), media_type="application/octet-stream")


@app.post("/synthesize")
async def synthesize(text: str = Form(...), profile: UploadFile | None = None):
    if profile is None or not (await profile.read()).startswith(PROFILE_PREFIX):
        raise HTTPException(status_code=400, detail="Missing or invalid voice profile")

    seconds = max(0.5, len(text.split()) / WORDS_PER_SECOND)
    n = int(seconds * SAMPLE_RATE)
    frames = b"".join(
        struct.pack("<h", int(3000 * math.sin(2 * math.pi * 440 * i / SAMPLE_RATE))) for i in range(n)
    )
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(frames)
    return Response(buf.getvalue(), media_type="audio/wav")
