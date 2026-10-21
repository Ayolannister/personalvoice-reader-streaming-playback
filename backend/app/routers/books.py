import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Book, Chapter, Voice
from app.parsers.epub_parser import parse_epub
from app.parsers.pdf_parser import parse_pdf
from app.parsers.txt_parser import parse_txt
from app.schemas import BookOut, ProgressUpdate, VoiceAssign

router = APIRouter()
settings = get_settings()

SUPPORTED_FORMATS = {"epub", "pdf", "txt"}


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _display_title(parsed_title: str, book_id: str, original_filename: str | None) -> str:
    """
    Parsers fall back to the file's stem when a book has no title metadata
    (always for TXT, sometimes for PDF). The stored file is named after the
    book's UUID, so that fallback would title the book with its internal ID.
    Use the name of the file the person actually uploaded instead.
    """
    title = (parsed_title or "").strip()
    if title and title != book_id:
        return title
    if original_filename:
        stem = original_filename.rsplit(".", 1)[0].strip()
        if stem:
            return stem
    return "Untitled"


@router.get("/books", response_model=list[BookOut])
def list_books(db: Session = Depends(get_db)):
    books = db.execute(select(Book)).scalars().all()
    return [BookOut.from_model(b) for b in books]


@router.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: str, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookOut.from_model(book)


@router.post("/books", response_model=BookOut, status_code=201)
async def upload_book(file: UploadFile, db: Session = Depends(get_db)):
    ext = _extension(file.filename or "")
    if ext not in SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}. Use EPUB, PDF, or TXT.")

    book_id = str(uuid.uuid4())
    dest_path = settings.books_dir / f"{book_id}.{ext}"
    with dest_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    try:
        if ext == "epub":
            parsed = parse_epub(dest_path)
        elif ext == "pdf":
            parsed = parse_pdf(dest_path)
        else:
            parsed = parse_txt(dest_path)
    except Exception as exc:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Couldn't parse this file: {exc}") from exc

    cover_path = None
    if parsed.cover_bytes:
        cover_path = settings.covers_dir / f"{book_id}.{parsed.cover_ext or 'png'}"
        cover_path.write_bytes(parsed.cover_bytes)

    book = Book(
        id=book_id,
        title=_display_title(parsed.title, book_id, file.filename),
        author=parsed.author.strip() or "Unknown",
        format=ext,
        status="ready",
        source_path=str(dest_path),
        cover_path=str(cover_path) if cover_path else None,
    )

    for pc in parsed.chapters:
        text_path = settings.books_dir / f"{book_id}_ch{pc.index}.txt"
        text_path.write_text(pc.text, encoding="utf-8")
        book.chapters.append(
            Chapter(
                index=pc.index,
                title=pc.title,
                text_path=str(text_path),
            )
        )

    book.current_chapter_id = None  # set once the first chapter is opened
    db.add(book)
    db.commit()
    db.refresh(book)

    # Resume pointer defaults to the first chapter once chapter ids exist.
    if book.chapters:
        book.current_chapter_id = book.chapters[0].id
        db.commit()
        db.refresh(book)

    return BookOut.from_model(book)


@router.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: str, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    Path(book.source_path).unlink(missing_ok=True)
    if book.cover_path:
        Path(book.cover_path).unlink(missing_ok=True)
    for chapter in book.chapters:
        Path(chapter.text_path).unlink(missing_ok=True)
        if chapter.audio_path:
            Path(chapter.audio_path).unlink(missing_ok=True)
    db.delete(book)
    db.commit()


@router.patch("/books/{book_id}/voice", response_model=BookOut)
def assign_voice(book_id: str, payload: VoiceAssign, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    voice = db.get(Voice, payload.voiceId)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    if voice.status != "ready":
        raise HTTPException(status_code=400, detail="This voice hasn't finished training yet")

    book.voice_id = voice.id
    db.commit()
    db.refresh(book)
    return BookOut.from_model(book)


@router.patch("/books/{book_id}/chapters/{chapter_id}/progress")
def update_progress(book_id: str, chapter_id: str, update: ProgressUpdate, db: Session = Depends(get_db)):
    chapter = db.get(Chapter, chapter_id)
    if not chapter or chapter.book_id != book_id:
        raise HTTPException(status_code=404, detail="Chapter not found")
    chapter.progress_seconds = update.positionSeconds

    book = db.get(Book, book_id)
    book.current_chapter_id = chapter_id

    db.commit()
    return {"ok": True}


@router.get("/covers/{book_id}")
def get_cover(book_id: str, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book or not book.cover_path or not Path(book.cover_path).exists():
        raise HTTPException(status_code=404, detail="No cover for this book")
    return FileResponse(book.cover_path)
