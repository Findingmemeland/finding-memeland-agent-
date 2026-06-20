"""X profile text constraints — limits and sanitization.

Pure module (no tweepy), so it's safe to import anywhere and easy to unit-test.

Learned empirically (2026-06-19): X's v1.1 account/update_profile rejects some
characters in the description with error 120 "Description can't include invalid
characters". Square brackets were confirmed to trigger it. We conservatively
strip the whole bracket/markup family; plain text (letters, digits, spaces and
common punctuation like . , ! ? ' " - :) passes.
"""

from __future__ import annotations

# X field limits.
MAX_NAME_LEN = 50
MAX_BIO_LEN = 160

# Room a hunt claim code needs at the end of the bio: "\ncode: XXXXXXXX".
CLAIM_CODE_BIO_RESERVE = 16

# Characters to strip from any text written to an X profile field.
# Confirmed bad: [ ]. The rest are stripped defensively (markup-ish chars most
# likely to trip X's filter); expand this set if new rejections show up.
BIO_FORBIDDEN_CHARS = frozenset("[]<>{}|\\^`~")


def sanitize_x_text(text: str) -> str:
    """Remove characters X rejects; collapse stray whitespace; trim ends.
    Newlines are preserved (the dresser uses one before the claim code)."""
    cleaned = "".join(ch for ch in text if ch not in BIO_FORBIDDEN_CHARS)
    # Collapse runs of spaces/tabs (but keep newlines) and trim each line.
    lines = [" ".join(line.split()) for line in cleaned.splitlines()]
    return "\n".join(lines).strip()


def sanitize_name(text: str) -> str:
    """X-safe display name, truncated to the limit."""
    return sanitize_x_text(text).replace("\n", " ")[:MAX_NAME_LEN].strip()


def sanitize_bio(text: str, *, reserve_for_claim_code: bool = True) -> str:
    """X-safe bio. By default leaves room for the claim code suffix."""
    limit = MAX_BIO_LEN - (CLAIM_CODE_BIO_RESERVE if reserve_for_claim_code else 0)
    return sanitize_x_text(text)[:limit].strip()
