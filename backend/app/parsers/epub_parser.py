from dataclasses import dataclass
from pathlib import Path

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub


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


def _clean_text(html: bytes) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _chapter_title(item, fallback_index: int, text: str) -> str:
    soup = BeautifulSoup(item.get_content(), "lxml")
    heading = soup.find(["h1", "h2", "h3"])
    if heading and heading.get_text(strip=True):
        return heading.get_text(strip=True)
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    if first_line and len(first_line) < 80:
        return first_line
    return f"Chapter {fallback_index}"


def parse_epub(path: Path) -> ParsedBook:
    book = epub.read_epub(str(path))

    title = book.get_metadata("DC", "title")
    title = title[0][0] if title else path.stem

    author = book.get_metadata("DC", "creator")
    author = author[0][0] if author else "Unknown"

    cover_bytes = None
    cover_ext = None
    for item in book.get_items_of_type(ebooklib.ITEM_COVER):
        cover_bytes = item.get_content()
        cover_ext = item.get_name().split(".")[-1]
        break
    if cover_bytes is None:
        # Fall back to the first image in the manifest, a common pattern
        # when a book doesn't set an explicit cover-image property.
        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            cover_bytes = item.get_content()
            cover_ext = item.get_name().split(".")[-1]
            break

    chapters: list[ParsedChapter] = []
    index = 0
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        text = _clean_text(item.get_content())
        if len(text) < 200:
            # Skip cover pages, title pages, and other near-empty documents.
            continue
        index += 1
        chapters.append(
            ParsedChapter(index=index, title=_chapter_title(item, index, text), text=text)
        )

    if not chapters:
        raise ValueError("No readable chapters found in this EPUB")

    return ParsedBook(title=title, author=author, chapters=chapters, cover_bytes=cover_bytes, cover_ext=cover_ext)
