import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Book(Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False, default="Unknown")
    format: Mapped[str] = mapped_column(String, nullable=False)  # epub | pdf | txt
    status: Mapped[str] = mapped_column(String, nullable=False, default="ready")
    source_path: Mapped[str] = mapped_column(String, nullable=False)
    cover_path: Mapped[str | None] = mapped_column(String, nullable=True)
    current_chapter_id: Mapped[str | None] = mapped_column(String, nullable=True)
    voice_id: Mapped[str | None] = mapped_column(String, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    chapters: Mapped[list["Chapter"]] = relationship(
        back_populates="book", cascade="all, delete-orphan", order_by="Chapter.index"
    )


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id"), nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    text_path: Mapped[str] = mapped_column(String, nullable=False)  # extracted plain text on disk
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    audio_status: Mapped[str] = mapped_column(String, nullable=False, default="not_generated")
    audio_path: Mapped[str | None] = mapped_column(String, nullable=True)
    progress_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    # generation progress (segments synthesized so far / total), so the
    # UI can show real progress instead of an indefinite spinner during
    # what can be a long CPU-bound generation
    generation_segments_done: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generation_segments_total: Mapped[int | None] = mapped_column(Integer, nullable=True)

    book: Mapped["Book"] = relationship(back_populates="chapters")


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id"), nullable=False)
    chapter_id: Mapped[str] = mapped_column(ForeignKey("chapters.id"), nullable=False)
    position_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Voice(Base):
    __tablename__ = "voices"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str] = mapped_column(String, nullable=False, default="English")
    source_path: Mapped[str] = mapped_column(String, nullable=False)
    source_minutes: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    # untrained -> training -> ready, or -> failed
    status: Mapped[str] = mapped_column(String, nullable=False, default="untrained")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # path to the saved conditioning-latents artifact once cloning succeeds
    model_path: Mapped[str | None] = mapped_column(String, nullable=True)
    is_default: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
