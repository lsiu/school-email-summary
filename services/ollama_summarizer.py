"""
Ollama summarization service.

Summarizes Gmail messages using a local Ollama model.
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from typing import Any, Dict, List

from config import CACHE_DIR, get_summarize_prompt
from utils.cache import ensure_cache_dir

DEFAULT_MODEL = "llama3.2:1b"
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_TIMEOUT_SECONDS = 300


def summarize_with_ollama(
    messages: List[Dict[str, Any]],
    *,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_BASE_URL,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """
    Summarize messages and extract action items using a local Ollama model.

    Args:
        messages: List of decoded message dictionaries
        model: Ollama model name (default: llama3.2:1b)
        base_url: Ollama API base URL
        timeout_seconds: Request timeout in seconds

    Returns:
        Summary text from Ollama or an error message
    """
    today = datetime.now()
    today_date = today.strftime("%Y-%m-%d")
    seven_days_from_now = (today + timedelta(days=7)).strftime("%Y-%m-%d")

    prompt_template = get_summarize_prompt()
    prompt = prompt_template.format(
        today_date=today_date,
        seven_days_from_now=seven_days_from_now,
    )

    email_content = ""
    for i, msg in enumerate(messages, 1):
        email_content += f"\n--- Email {i} ---\n"
        email_content += f"From: {msg['from']}\n"
        email_content += f"Subject: {msg['subject']}\n"
        email_content += f"Date: {msg['date']}\n"
        email_content += f"Body:\n{msg['body']}\n"

    prompt = prompt + email_content

    prompt_file = os.path.join(CACHE_DIR, "temp.prompt.txt")
    ensure_cache_dir()

    try:
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)
        print(f"  Prompt saved to {prompt_file}")
    except Exception as e:
        return f"Error saving prompt file: {e}"

    print(f"  Using Ollama model: {model}")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }

    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            result = json.loads(response.read().decode("utf-8"))

        content = (result.get("message") or {}).get("content", "").strip()
        if content:
            return content

        return f"Error from Ollama: empty response ({result})"

    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), TimeoutError):
            return "Ollama request timed out. The request may be too long."
        return (
            f"Could not connect to Ollama at {base_url}. "
            "Make sure Ollama is running (ollama serve)."
        )
    except json.JSONDecodeError as e:
        return f"Error parsing Ollama response: {e}"
    except Exception as e:
        return f"Error calling Ollama: {e}"
