from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


@dataclass
class ParsedChapter:
    index: int
    title: str
    text: str


@dataclass
class ParsedBook:
    title: str
    author: str
    chapters: list[ParsedChapter]
    cover_bytes: bytes | None
    cover_ext: str | None


PAGES_PER_CHAPTER_FALLBACK = 15


def _page_range_text(doc: fitz.Document, start: int, end: int) -> str:
    parts = []
    for p in range(start, end):
        parts.append(doc[p].get_text("text"))
    return "\n".join(parts).strip()


def parse_pdf(path: Path) -> ParsedBook:
    doc = fitz.open(str(path))
    meta = doc.metadata or {}
    title = meta.get("title") or path.stem
    author = meta.get("author") or "Unknown"

    cover_bytes = None
    cover_ext = None
    if doc.page_count > 0:
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        cover_bytes = pix.tobytes("png")
        cover_ext = "png"

    toc = doc.get_toc(simple=True)  # [[level, title, page], ...], 1-indexed pages
    chapters: list[ParsedChapter] = []

    top_level = [t for t in toc if t[0] == 1] if toc else []

    if top_level:
        for i, (_, chap_title, start_page) in enumerate(top_level):
            start = start_page - 1
            end = (top_level[i + 1][2] - 1) if i + 1 < len(top_level) else doc.page_count
            start = max(0, min(start, doc.page_count - 1))
            end = max(start + 1, min(end, doc.page_count))
            text = _page_range_text(doc, start, end)
            if len(text) < 100:
                continue
            chapters.append(ParsedChapter(index=len(chapters) + 1, title=chap_title.strip() or f"Chapter {len(chapters) + 1}", text=text))

    if not chapters:
        # No usable outline: fall back to fixed-size page chunks.
        page = 0
        while page < doc.page_count:
            end = min(page + PAGES_PER_CHAPTER_FALLBACK, doc.page_count)
            text = _page_range_text(doc, page, end)
            if len(text) >= 100:
                chapters.append(
                    ParsedChapter(
                        index=len(chapters) + 1,
                        title=f"Pages {page + 1}\u2013{end}",
                        text=text,
                    )
                )
            page = end

    doc.close()

    if not chapters:
        raise ValueError("No readable text found in this PDF")

    return ParsedBook(title=title, author=author, chapters=chapters, cover_bytes=cover_bytes, cover_ext=cover_ext)
