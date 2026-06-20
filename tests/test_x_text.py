from finding_memeland.social.x_text import (
    MAX_NAME_LEN,
    sanitize_bio,
    sanitize_name,
    sanitize_x_text,
)


def test_strips_forbidden_brackets():
    assert sanitize_x_text("hello [world] <x>") == "hello world x"


def test_preserves_safe_punctuation():
    text = "Maybe the next big thing in crypto. Stay tuned!"
    assert sanitize_x_text(text) == text


def test_collapses_spaces_but_keeps_newlines():
    assert sanitize_x_text("a   b\nc  d") == "a b\nc d"


def test_name_truncated_and_single_line():
    long = "x" * 80
    out = sanitize_name(long + "\nmore")
    assert len(out) <= MAX_NAME_LEN
    assert "\n" not in out


def test_bio_reserves_room_for_claim_code():
    out = sanitize_bio("y" * 200)
    assert len(out) <= 160 - 16
