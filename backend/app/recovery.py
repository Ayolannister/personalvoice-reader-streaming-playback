"""
Cleans up work that was in flight when the app last stopped.

Voice cloning and chapter generation run as background tasks inside the
backend process. If the process stops (docker compose down, a crash, a
reboot) while one is running, its database row is left saying
"training" / "generating" / "partial" forever: nothing will ever finish
it, and the API refuses to restart it because it looks busy.

Runs once at startup, before any request is served, so nothing can
actually be in flight yet.
"""
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Chapter, Voice

INTERRUPTED_TRAINING_MESSAGE = (
    "Training was interrupted because the app stopped before it finished. "
    "Retry to train this voice again."
)


def recover_interrupted_jobs(db: Session) -> dict[str, int]:
    voices = db.execute(
        update(Voice)
        .where(Voice.status == "training")
        .values(status="failed", error_message=INTERRUPTED_TRAINING_MESSAGE)
    ).rowcount

    # The segments synthesized before the stop are still on disk, and the
    # next Generate picks up from them (see generation._run_generation), so
    # resetting the status loses no finished work.
    chapters = db.execute(
        update(Chapter)
        .where(Chapter.audio_status.in_(("generating", "partial")))
        .values(audio_status="not_generated")
    ).rowcount

    db.commit()
    return {"voices": voices or 0, "chapters": chapters or 0}
