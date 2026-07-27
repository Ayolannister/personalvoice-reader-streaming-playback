# TTS service

A standalone Coqui XTTS v2 cloning service, isolated in its own Python
3.11 container because coqui-tts (and its pinned torch/torchaudio
versions) doesn't support Python 3.12 — which the main backend runs on.

The backend talks to this over HTTP instead of importing TTS in-process.
See `backend/app/tts/xtts_remote_engine.py` for the client side.

## API

- `GET /health` — `{"status": "ok", "model_loaded": bool}`
- `POST /clone` — multipart file upload (a reference recording). Returns
  a `voice_profile.pt` file containing the XTTS v2 conditioning latents.
  Stateless: this service doesn't persist anything itself.

## Run with Docker

```bash
docker build -t personalvoice-tts .
docker run -p 8001:8001 -v xtts-models:/root/.local/share/tts personalvoice-tts
```

First request downloads the ~2GB model from Hugging Face — the volume
mount keeps it cached across restarts so that only happens once.

## Run without Docker (if you have Python 3.11 available directly)

```bash
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8001
```

## Wiring it into the backend

In `backend/.env`:

```
TTS_ENGINE=xtts_remote
TTS_SERVICE_URL=http://localhost:8001
```

(`http://tts-service:8001` when both run under the same `docker-compose`
network — see `docker/docker-compose.yml`.)
