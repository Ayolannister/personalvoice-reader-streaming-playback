# Backend

FastAPI service, SQLite for local dev (Postgres-ready — see `app/database.py`).

**System dependency:** `ffmpeg` must be on PATH (used to concatenate and
encode generated chapter audio). `apt install ffmpeg` / `brew install
ffmpeg`. Already included in `Dockerfile`.

## Built so far

- Book upload/list/detail/delete: EPUB via `ebooklib` + BeautifulSoup,
  PDF via PyMuPDF, TXT direct, all with chapter/cover/author extraction
- Progress tracking and bookmark endpoints
- Voice upload, cloning ("training"), status, retry, set-default
- Chapter-by-chapter audio generation: assign a voice to a book, then
  generate one chapter at a time (never the whole book up front). Text
  is chunked into TTS-sized segments (`app/tts/text_chunking.py`),
  synthesized individually, and concatenated + encoded to MP3 with
  ffmpeg (`app/tts/audio_utils.py` — **ffmpeg must be on PATH**).
  Generated audio is cached: re-requesting an already-cached chapter is
  a no-op. Streamed back via `GET .../audio` with HTTP Range support for
  scrubbing.
  - **Playable before it's fully done:** CPU inference for a whole
    chapter can take a long time, so generation publishes a playable
    checkpoint after the first segment, then again every
    `CHECKPOINT_EVERY` segments (`app/routers/generation.py`), instead
    of making the person wait for the entire chapter. `audio_status`
    goes `not_generated` → `generating` (first segment still rendering)
    → `partial` (playable, more still coming) → `cached` (fully done).
    Each checkpoint publish is atomic (`os.replace`), so a client mid-read
    never sees a half-written file.
- Three pluggable cloning/synthesis engines (`app/tts/`), picked via
  `TTS_ENGINE`:
  - `xtts` — in-process Coqui XTTS v2. Needs `requirements-tts.txt`
    installed (~5GB: torch, transformers, spacy, etc.) — works fine on
    Python 3.12, `coqui-tts==0.24.2` supports 3.9-3.12
  - `xtts_remote` — calls the dockerized TTS service instead
    (`../worker/tts-service`), keeping that ~5GB dependency stack out of
    the backend's own environment entirely. Set `TTS_SERVICE_URL` to
    point at it. **Recommended regardless of Python version** — this is
    about dependency isolation, not Python compatibility.
  - `dummy` — fake profile/silent audio for developing/testing the
    pipeline without either of the above

Run with Docker (backend + tts-service together): `cd ../docker && docker compose up --build`

See `../frontend/src/types/index.ts` for the response shapes the UI
expects (`Book`, `Chapter`, `Voice`) — kept in sync with the backend
schema so the frontend swap from mock data to live data was a
data-source change only, not a rewrite.
