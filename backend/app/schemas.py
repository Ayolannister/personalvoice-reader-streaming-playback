from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChapterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    index: int
    title: str
    durationSeconds: float | None
    audioStatus: str
    progressSeconds: float
    generationSegmentsDone: int
    generationSegmentsTotal: int | None

    @classmethod
    def from_model(cls, chapter):
        return cls(
            id=chapter.id,
            index=chapter.index,
            title=chapter.title,
            durationSeconds=chapter.duration_seconds,
            audioStatus=chapter.audio_status,
            progressSeconds=chapter.progress_seconds,
            generationSegmentsDone=chapter.generation_segments_done,
            generationSegmentsTotal=chapter.generation_segments_total,
        )


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    author: str
    coverUrl: str | None
    format: str
    status: str
    currentChapterId: str | None
    voiceId: str | None
    addedAt: datetime
    chapters: list[ChapterOut]

    @classmethod
    def from_model(cls, book):
        return cls(
            id=book.id,
            title=book.title,
            author=book.author,
            coverUrl=f"/covers/{book.id}" if book.cover_path else None,
            format=book.format,
            status=book.status,
            currentChapterId=book.current_chapter_id,
            voiceId=book.voice_id,
            addedAt=book.added_at,
            chapters=[ChapterOut.from_model(c) for c in book.chapters],
        )


class VoiceAssign(BaseModel):
    voiceId: str


class GenerateRequest(BaseModel):
    voiceId: str | None = None  # falls back to the book's assigned voice if omitted


class ProgressUpdate(BaseModel):
    positionSeconds: float


class BookmarkCreate(BaseModel):
    chapterId: str
    positionSeconds: float
    label: str | None = None
    note: str | None = None


class BookmarkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bookId: str
    chapterId: str
    positionSeconds: float
    label: str | None
    note: str | None
    createdAt: datetime

    @classmethod
    def from_model(cls, bm):
        return cls(
            id=bm.id,
            bookId=bm.book_id,
            chapterId=bm.chapter_id,
            positionSeconds=bm.position_seconds,
            label=bm.label,
            note=bm.note,
            createdAt=bm.created_at,
        )


class VoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    language: str
    sourceMinutes: float
    status: str
    errorMessage: str | None
    isDefault: bool
    createdAt: datetime

    @classmethod
    def from_model(cls, voice):
        return cls(
            id=voice.id,
            name=voice.name,
            language=voice.language,
            sourceMinutes=round(voice.source_minutes, 1),
            status=voice.status,
            errorMessage=voice.error_message,
            isDefault=voice.is_default,
            createdAt=voice.created_at,
        )
