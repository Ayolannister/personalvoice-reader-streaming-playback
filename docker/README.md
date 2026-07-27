# Docker

`docker-compose.yml` here wires up the backend + the dockerized TTS
service (`worker/tts-service`) — built early, ahead of the rest of
Milestone 5, because coqui-tts doesn't support the backend's Python
3.12, so the cloning step needed its own Python 3.11 container from the
start.

```bash
cd docker
docker compose up --build
```

Frontend still runs separately with `npm run dev` for now — the full
one-command local stack (Postgres, Redis, MinIO, frontend included)
is the rest of Milestone 5.
