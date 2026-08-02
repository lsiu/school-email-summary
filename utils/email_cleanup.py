"""
Email body cleanup for AI summarization.

Strips HTML conversion artifacts and boilerplate so small local models
can focus on actionable content.
"""

import re

_TRACKING_URL_RE = re.compile(
    r"https?://email\.mail\d*\.veracross\.com/\S+",
    re.IGNORECASE,
)
_GENERIC_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|[\s|\-:]+\|\s*$", re.MULTILINE)
_IMS_FOOTER_RE = re.compile(
    r"---\s*\nTHE INTERNATIONAL MONTESSORI SCHOOL.*",
    re.DOTALL | re.IGNORECASE,
)
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def clean_email_body(body: str, *, max_chars: int = 6000) -> str:
    """
    Normalize email body text before sending it to a local model.

    Args:
        body: Raw decoded email body
        max_chars: Maximum characters to retain

    Returns:
        Cleaned body text
    """
    if not body:
        return ""

    text = body.replace("\r\n", "\n").replace("\r", "\n")
    text = _TABLE_SEPARATOR_RE.sub("\n", text)
    text = _TRACKING_URL_RE.sub("[link]", text)
    text = _GENERIC_URL_RE.sub("[link]", text)
    text = _IMS_FOOTER_RE.sub("", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = _BLANK_LINES_RE.sub("\n\n", text)
    text = text.strip()

    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "\n\n[truncated]"

    return text
