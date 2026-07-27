import re
from dataclasses import dataclass
from pathlib import Path

CHAPTER_HEADING_RE = re.compile(
    r"^\s*(chapter|part|book|section)\s+([ivxlcdm0-9]+)\b.*$", re.IGNORECASE
)
WORDS_PER_CHAPTER_FALLBACK = 3000


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


def parse_txt(path: Path) -> ParsedBook:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()

    heading_indices = [i for i, line in enumerate(lines) if CHAPTER_HEADING_RE.match(line)]

    chapters: list[ParsedChapter] = []

    if len(heading_indices) >= 2:
        for i, start in enumerate(heading_indices):
            end = heading_indices[i + 1] if i + 1 < len(heading_indices) else len(lines)
            title = lines[start].strip()
            body = "\n".join(lines[start + 1 : end]).strip()
            if len(body) < 50:
                continue
            chapters.append(ParsedChapter(index=len(chapters) + 1, title=title, text=body))

    if not chapters:
        # No detectable headings: split into fixed-size word chunks.
        words = raw.split()
        for i in range(0, len(words), WORDS_PER_CHAPTER_FALLBACK):
            chunk = " ".join(words[i : i + WORDS_PER_CHAPTER_FALLBACK])
            chapters.append(
                ParsedChapter(index=len(chapters) + 1, title=f"Part {len(chapters) + 1}", text=chunk)
            )

    if not chapters:
        raise ValueError("This TXT file appears to be empty")

    return ParsedBook(title=path.stem, author="Unknown", chapters=chapters, cover_bytes=None, cover_ext=None)
