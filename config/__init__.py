"""Configuration package for Gmail automation."""

from .settings import (
    SCOPES,
    SENDER_DOMAINS,
    CACHE_DIR,
    CACHE_EXPIRY_HOURS,
    CHILDREN,
    GRADE_DIVISIONS,
    calculate_grade,
    get_division,
    get_division_range,
    get_children_info,
    SUMMARIZE_PROMPT,
)

__all__ = [
    "SCOPES",
    "SENDER_DOMAINS",
    "CACHE_DIR",
    "CACHE_EXPIRY_HOURS",
    "CHILDREN",
    "GRADE_DIVISIONS",
    "calculate_grade",
    "get_division",
    "get_division_range",
    "get_children_info",
    "SUMMARIZE_PROMPT",
]
