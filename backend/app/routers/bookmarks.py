from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Bookmark, Chapter
from app.schemas import BookmarkCreate, BookmarkOut

router = APIRouter()


@router.get("/books/{book_id}/bookmarks", response_model=list[BookmarkOut])
def list_bookmarks(book_id: str, db: Session = Depends(get_db)):
    bookmarks = db.execute(select(Bookmark).where(Bookmark.book_id == book_id)).scalars().all()
    return [BookmarkOut.from_model(b) for b in bookmarks]


@router.post("/books/{book_id}/bookmarks", response_model=BookmarkOut, status_code=201)
def create_bookmark(book_id: str, payload: BookmarkCreate, db: Session = Depends(get_db)):
    chapter = db.get(Chapter, payload.chapterId)
    if not chapter or chapter.book_id != book_id:
        raise HTTPException(status_code=404, detail="Chapter not found")

    bookmark = Bookmark(
        book_id=book_id,
        chapter_id=payload.chapterId,
        position_seconds=payload.positionSeconds,
        label=payload.label,
        note=payload.note,
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return BookmarkOut.from_model(bookmark)


@router.delete("/bookmarks/{bookmark_id}", status_code=204)
def delete_bookmark(bookmark_id: str, db: Session = Depends(get_db)):
    bookmark = db.get(Bookmark, bookmark_id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    db.delete(bookmark)
    db.commit()
