from pathlib import Path

from app.parsers.txt_parser import parse_txt


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_parse_txt_splits_on_chapter_headings(tmp_path):
    content = (
        "Chapter 1\n"
        + ("Some opening text. " * 20)
        + "\n\nChapter 2\n"
        + ("More narrative text. " * 20)
    )
    path = _write(tmp_path, "book.txt", content)

    result = parse_txt(path)

    assert len(result.chapters) == 2
    assert result.chapters[0].title == "Chapter 1"
    assert result.chapters[1].title == "Chapter 2"
    assert "opening text" in result.chapters[0].text


def test_parse_txt_falls_back_to_word_chunks_without_headings(tmp_path):
    content = "word " * 7000
    path = _write(tmp_path, "plain.txt", content)

    result = parse_txt(path)

    assert len(result.chapters) == 3  # 7000 words / 3000-word chunks, rounded up
    assert result.chapters[0].title == "Part 1"


def test_parse_txt_raises_on_empty_file(tmp_path):
    path = _write(tmp_path, "empty.txt", "")

    try:
        parse_txt(path)
        assert False, "expected ValueError"
    except ValueError:
        pass
