"""Services package for Gmail automation."""

from .gmail_auth import get_gmail_service
from .gmail_client import read_messages
from .ollama_summarizer import summarize_with_ollama

__all__ = [
    "get_gmail_service",
    "read_messages",
    "summarize_with_ollama",
]
