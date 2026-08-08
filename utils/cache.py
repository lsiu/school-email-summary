"""
Cache management for Gmail API results.

Provides functions to cache API responses and prompts to avoid
excessive API calls. Cache expires after a configurable time period.
Cache files include timestamp in filename for expiry determination.
"""

import hashlib
import json
import os
import re
from datetime import datetime, timedelta

from config import CACHE_DIR, get_cache_expiry_hours


def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def get_cache_filename(timestamp: datetime) -> str:
    """
    Generate cache filename with embedded timestamp.

    Args:
        timestamp: The timestamp to embed in filename

    Returns:
        Cache filename with format: {timestamp}.json
    """
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    return f"{timestamp_str}.json"


def parse_cache_filename(filename: str) -> datetime | None:
    """
    Parse cache filename to extract the embedded timestamp.

    Args:
        filename: Cache filename to parse

    Returns:
        datetime object parsed from the filename, or None if invalid format
    """
    # Pattern: {YYYYMMDD_HHMMSS}.json
    pattern = r"^(\d{8}_\d{6})\.json$"
    match = re.match(pattern, filename)
    if not match:
        return None

    timestamp_str = match.group(1)
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        return timestamp
    except ValueError:
        return None


def find_valid_cache() -> str | None:
    """

    Find a valid (non-expired) cache file.
    Lists cache directory, sorts by filename descending (most recent first),
    and checks each file's timestamp for expiry.

    Returns:
        Path to a valid cache file, or None if no valid cache is found.
    """
    if not os.path.exists(CACHE_DIR):
        return None

    expiry_cutoff = datetime.now() - timedelta(hours=get_cache_expiry_hours())

    try:
        # Get all JSON files and sort by filename descending (most recent first)
        cache_files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".json")]
        cache_files.sort(reverse=True)

        for filename in cache_files:
            timestamp = parse_cache_filename(filename)
            if not timestamp:
                continue

            # Check if cache is expired based on filename timestamp
            if timestamp < expiry_cutoff:
                continue

            # Found a valid cache file
            cache_file = os.path.join(CACHE_DIR, filename)
            return cache_file
    except Exception as e:
        print(f"  Warning: Error scanning cache directory: {e}")

    return None


def load_from_cache():
    """
    Load messages from cache if available and not expired.
    Cache expiry is determined from timestamp in filename.
    Lists cache directory and sorts by filename descending to find
    the most recent valid cache.

    Returns:
        List of cached messages or None if cache miss/expired
    """
    cache_file = find_valid_cache()

    if cache_file is None:
        return None

    try:
        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        messages = cache_data.get("messages", [])
        print(f"  Loaded from cache ({len(messages)} messages)")
        return messages

    except Exception as e:
        print(f"  Warning: Could not load cache: {e}")
        return None


def save_to_cache(messages: list):
    """
    Save messages to cache.
    Cache filename includes timestamp for expiry determination.

    Args:
        messages: List of message dictionaries to cache
    """
    ensure_cache_dir()
    timestamp = datetime.now()
    cache_file = os.path.join(CACHE_DIR, get_cache_filename(timestamp))

    cache_data = {"messages": messages}

    try:
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)
        print(f"  Cached to {cache_file}")
    except Exception as e:
        print(f"  Warning: Could not save cache: {e}")


def get_data_cache_filename(timestamp: datetime, cache_type: str, key: str) -> str:
    """
    Generate cache filename for typed data with embedded timestamp and key.

    Args:
        timestamp: The timestamp to embed in filename
        cache_type: Type of cached data (e.g., 'extractions', 'merge')
        key: Cache key identifying the data (e.g., message hash)

    Returns:
        Cache filename with format: {timestamp}_{cache_type}_{key}.json
    """
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    return f"{timestamp_str}_{cache_type}_{key}.json"


def parse_data_cache_filename(filename: str):
    """
    Parse typed cache filename to extract timestamp, type, and key.

    Args:
        filename: Cache filename to parse

    Returns:
        Tuple of (datetime, cache_type, key), or None if invalid format
    """
    # Pattern: {YYYYMMDD_HHMMSS}_{type}_{key}.json
    pattern = r"^(\d{8}_\d{6})_([a-z]+)_([a-z0-9]+)\.json$"
    match = re.match(pattern, filename)
    if not match:
        return None

    timestamp_str, cache_type, key = match.groups()
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        return timestamp, cache_type, key
    except ValueError:
        return None


def find_valid_data_cache(cache_type: str, key: str) -> str | None:
    """
    Find a valid (non-expired) typed cache file matching type and key.

    Args:
        cache_type: Type of cached data
        key: Cache key identifying the data

    Returns:
        Path to a valid cache file, or None if no valid cache is found.
    """
    if not os.path.exists(CACHE_DIR):
        return None

    expiry_cutoff = datetime.now() - timedelta(hours=get_cache_expiry_hours())

    try:
        cache_files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".json")]
        cache_files.sort(reverse=True)

        for filename in cache_files:
            parsed = parse_data_cache_filename(filename)
            if not parsed:
                continue

            timestamp, file_type, file_key = parsed
            if file_type != cache_type or file_key != key:
                continue

            if timestamp < expiry_cutoff:
                continue

            return os.path.join(CACHE_DIR, filename)
    except Exception as e:
        print(f"  Warning: Error scanning cache directory: {e}")

    return None


def load_data_from_cache(cache_type: str, key: str):
    """
    Load typed data from cache if available and not expired.

    Args:
        cache_type: Type of cached data
        key: Cache key identifying the data

    Returns:
        Cached data or None if cache miss/expired
    """
    cache_file = find_valid_data_cache(cache_type, key)

    if cache_file is None:
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)

        data = cache_data.get("data")
        print(f"  Loaded {cache_type} from cache ({cache_file})")
        return data

    except Exception as e:
        print(f"  Warning: Could not load {cache_type} cache: {e}")
        return None


def save_data_to_cache(data, cache_type: str, key: str) -> None:
    """
    Save typed data to cache with timestamp and key in filename.

    Args:
        data: Data to cache
        cache_type: Type of cached data
        key: Cache key identifying the data
    """
    ensure_cache_dir()
    timestamp = datetime.now()
    cache_file = os.path.join(
        CACHE_DIR, get_data_cache_filename(timestamp, cache_type, key)
    )

    cache_data = {"data": data}

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)
        print(f"  Cached {cache_type} to {cache_file}")
    except Exception as e:
        print(f"  Warning: Could not save {cache_type} cache: {e}")