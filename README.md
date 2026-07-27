# PersonalVoice Reader

A personal, local-first audiobook app: upload a book you have the right
to read, clone a voice from someone who's given consent (including your
own), and listen — generated chapter by chapter, cached so nothing
regenerates twice. Single user, no accounts, no marketplace, no sharing.

## Status

- [x] **Milestone 1 — UI shell.** Next.js app shell, design system,
      navigation, and every core screen built against fixture data.
      See `frontend/README.md`.
- [x] **Milestone 2 — Book uploads.** FastAPI backend: EPUB/PDF/TXT
      upload, parsing, chapter/cover/author extraction, SQLite
      (Postgres-ready). See `backend/README.md`.
- [x] **Milestone 3 — Voice cloning.** Voice upload, cloning pipeline,
      training-status reporting, retry-on-failure, set-default. Coqui
      XTTS v2 runs either in-process or in its own Python 3.11 Docker
      container (`worker/tts-service`) — the latter needed because
      coqui-tts doesn't yet support Python 3.12. See `backend/README.md`
      and `worker/tts-service/README.md`.
- [x] **Milestone 4 — Playback.** Assign a voice to a book, generate
      audio chapter by chapter on demand (chunked, synthesized, and
      concatenated to MP3 with ffmpeg), cache it, and stream it to a
      real `<audio>`-backed player: seek, skip ±15s, speed, working
      sleep timer, resume position saved to the backend.
- [ ] **Milestone 5 — Local packaging.** Full docker-compose (adds
      Postgres, Redis, frontend to the backend + tts-service pair
      already in `docker/docker-compose.yml`) for one-command local
      setup.

Each milestone is built and verified on its own before the next starts.

## Repo layout

```
frontend/            Next.js app (built — see frontend/README.md)
backend/              FastAPI service (built — see backend/README.md)
worker/tts-service/   Dockerized XTTS v2 cloning service (Python 3.11)
docker/               docker-compose (backend + tts-service so far)
infra/                env templates, bootstrap scripts (Milestone 5)
docs/                 architecture notes, API contracts
models/               local TTS model weights (not committed)
```

## Consent

This app assumes every uploaded voice recording comes from someone who
has explicitly agreed to have their voice cloned for your personal use.
There is no sharing, export, or marketplace feature by design — cloned
voices stay on your device.
