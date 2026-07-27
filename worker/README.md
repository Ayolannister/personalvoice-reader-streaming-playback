# Worker

`tts-service/` — built. A standalone Python 3.11 container running
Coqui XTTS v2 cloning, talked to over HTTP by the backend
(`app/tts/xtts_remote_engine.py`). Exists because coqui-tts doesn't
support Python 3.12, which the backend runs on. See its own README for
API details and how to run it.

A general Celery/RQ background worker for book parsing and chapter
audio generation is still Milestone 4 — for now, voice training and
(later) chapter generation run as FastAPI BackgroundTasks in the main
backend process, which is enough for a single-user app doing one job
at a time. Revisit if that stops being true.
