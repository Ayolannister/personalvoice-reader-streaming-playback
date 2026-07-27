from app.tts.text_chunking import chunk_text


def test_chunk_text_groups_short_sentences():
    text = "This is one. This is two. This is three."
    segments = chunk_text(text, max_chars=40)
    assert all(len(s) <= 40 for s in segments)
    assert "".join(segments).replace(" ", "") != ""


def test_chunk_text_splits_long_single_sentence():
    long_sentence = "word " * 100
    segments = chunk_text(long_sentence.strip(), max_chars=50)
    assert all(len(s) <= 50 for s in segments)
    assert len(segments) > 1


def test_chunk_text_handles_empty_input():
    assert chunk_text("") == []


def test_chunk_text_preserves_all_words():
    text = "Alpha beta gamma. Delta epsilon zeta. Eta theta iota."
    segments = chunk_text(text, max_chars=1000)
    rejoined = " ".join(segments)
    for word in ["Alpha", "beta", "gamma", "Delta", "epsilon", "zeta", "Eta", "theta", "iota"]:
        assert word in rejoined
