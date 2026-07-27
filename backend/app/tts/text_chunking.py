import re

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

# XTTS v2 handles roughly a sentence or two per call reliably; longer
# inputs get truncated or degrade in quality, so chapters are synthesized
# in segments and the resulting WAV files are concatenated.
MAX_SEGMENT_CHARS = 250


def chunk_text(text: str, max_chars: int = MAX_SEGMENT_CHARS) -> list[str]:
    sentences = SENTENCE_SPLIT_RE.split(text.strip())
    segments: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                segments.append(current)
            if len(sentence) <= max_chars:
                current = sentence
            else:
                # A single sentence longer than the limit: hard-split on
                # words so nothing is silently dropped.
                words = sentence.split()
                piece = ""
                for word in words:
                    candidate_piece = f"{piece} {word}".strip() if piece else word
                    if len(candidate_piece) <= max_chars:
                        piece = candidate_piece
                    else:
                        segments.append(piece)
                        piece = word
                current = piece

    if current:
        segments.append(current)

    return segments
