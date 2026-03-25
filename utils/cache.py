"""
Cache management for Gmail API results.

Provides functions to cache API responses and prompts to avoid
excessive API calls. Cache expires after a configurable time period.
"""

import hashlib
import json
import os
from datetime import datetime, timedelta

from config import CACHE_DIR, get_cache_expiry_hours, get_sender_domains


def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def get_cache_key(days: int, max_results: int) -> str:
    """
    Generate a cache key based on search parameters.

    Args:
        days: Number of days to search back
        max_results: Maximum results per domain

    Returns:
        MD5 hash of the search parameters
    """
    params = f"{get_sender_domains()}-{days}-{max_results}"
    return hashlib.md5(params.encode()).hexdigest()


def load_from_cache(cache_key: str):
    """
    Load messages from cache if available and not expired.

    Args:
        cache_key: The cache key to load from

    Returns:
        List of cached messages or None if cache miss/expired
    """
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")

    if not os.path.exists(cache_file):
        return None

    try:
        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        # Check if cache is expired
        cached_time = datetime.fromisoformat(cache_data["timestamp"])
        if datetime.now() - cached_time > timedelta(hours=get_cache_expiry_hours()):
            print(f"  Cache expired (older than {get_cache_expiry_hours()} hours)")
            return None

        print(f"  Loaded from cache ({len(cache_data['messages'])} messages)")
        return cache_data["messages"]

    except Exception as e:
        print(f"  Warning: Could not load cache: {e}")
        return None


def save_to_cache(cache_key: str, messages: list, prompt: str | None = None):
    """
    Save messages and optional prompt to cache.

    Args:
        cache_key: The cache key to save to
        messages: List of message dictionaries to cache
        prompt: Optional prompt text to save
    """
    ensure_cache_dir()
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")

    cache_data = {"timestamp": datetime.now().isoformat(), "messages": messages}

    # Save prompt if provided
    if prompt:
        prompt_file = os.path.join(CACHE_DIR, f"{cache_key}.prompt.txt")
        try:
            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(prompt)
            cache_data["prompt_file"] = prompt_file
        except Exception as e:
            print(f"  Warning: Could not save prompt: {e}")

    try:
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)
        print(f"  Cached to {cache_file}")
    except Exception as e:
        print(f"  Warning: Could not save cache: {e}")
