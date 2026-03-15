"""Configuration package for Gmail automation."""

from .settings import (
    SCOPES,
    SENDER_DOMAINS,
    CACHE_DIR,
    CACHE_EXPIRY_HOURS,
    CHILDREN,
    SUMMARIZE_PROMPT,
)

__all__ = [
    "SCOPES",
    "SENDER_DOMAINS",
    "CACHE_DIR",
    "CACHE_EXPIRY_HOURS",
    "CHILDREN",
    "SUMMARIZE_PROMPT",
]
