"""
Qwen CLI summarization service.

Provides functions to summarize Gmail messages using Qwen CLI.
Handles prompt preparation, cache integration, and OS-specific command execution.
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from config import CACHE_DIR, get_summarize_prompt
from utils.cache import ensure_cache_dir


def summarize_with_qwen(
    messages: List[Dict[str, Any]],
    cache_key: Optional[str] = None
) -> str:
    """
    Use Qwen CLI to summarize messages and extract action items.

    Args:
        messages: List of decoded message dictionaries
        cache_key: Optional cache key for saving the prompt

    Returns:
        Summary text from Qwen CLI or error message
    """
    # Calculate dates for the prompt
    today = datetime.now()
    today_date = today.strftime("%Y-%m-%d")
    seven_days_from_now = (today + timedelta(days=7)).strftime("%Y-%m-%d")

    # Get the prompt template (dynamically generated from config)
    prompt_template = get_summarize_prompt()

    # Format the prompt with dates
    prompt = prompt_template.format(
        today_date=today_date,
        seven_days_from_now=seven_days_from_now,
    )

    # Prepare email content
    email_content = ""
    for i, msg in enumerate(messages, 1):
        email_content += f"\n--- Email {i} ---\n"
        email_content += f"From: {msg['from']}\n"
        email_content += f"Subject: {msg['subject']}\n"
        email_content += f"Date: {msg['date']}\n"
        email_content += f"Body:\n{msg['body']}\n"

    prompt = prompt + email_content

    # Save prompt to cache first (before calling Qwen)
    if not cache_key:
        cache_key = "temp"

    prompt_file = os.path.join(CACHE_DIR, f"{cache_key}.prompt.txt")
    ensure_cache_dir()

    try:
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print(f"  Prompt saved to {prompt_file}")
    except Exception as e:
        return f"Error saving prompt file: {e}"

    # Determine qwen command based on OS
    # Windows uses qwen.cmd, Linux/Mac uses qwen
    qwen_cmd = "qwen.cmd" if sys.platform == "win32" else "qwen"
    print(f"  Using Qwen command: {qwen_cmd}")

    # Short instruction to read the prompt file
    short_instruction = f"Please read the file at {prompt_file} and execute the instructions in it."

    try:
        # Call Qwen CLI with short instruction (avoids command line length limit)
        # Using: qwen [query..] - defaults to one-shot mode
        result = subprocess.run(
            [qwen_cmd, short_instruction],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"\n[DEBUG] Qwen CLI stderr:\n{result.stderr}")
            print(f"\n[DEBUG] Qwen CLI stdout:\n{result.stdout}")
            return f"Error from Qwen CLI (returncode={result.returncode}): {result.stderr}"

    except FileNotFoundError:
        return f"Qwen CLI not found. Please install it with: npm install -g @qwen-code/qwen-code"
    except subprocess.TimeoutExpired:
        return "Qwen CLI timed out. The request may be too long."
    except Exception as e:
        return f"Error calling Qwen CLI: {e}"
