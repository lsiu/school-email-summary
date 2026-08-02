"""
Ollama summarization service.

Uses a map-reduce pipeline tuned for small local models:
1. Extract facts from each email individually
2. Merge extractions into the per-child summary format
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from typing import Any, Dict, List

from config import CACHE_DIR, get_children_info
from utils.cache import ensure_cache_dir
from utils.email_cleanup import clean_email_body

DEFAULT_MODEL = "llama3.2:1b"
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_TIMEOUT_SECONDS = 300
EXTRACT_TIMEOUT_SECONDS = 120
MERGE_TIMEOUT_SECONDS = 180

DEFAULT_OPTIONS = {
    "temperature": 0.1,
    "num_ctx": 8192,
}

EXTRACT_OPTIONS = {
    **DEFAULT_OPTIONS,
    "num_predict": 1536,
}

MERGE_OPTIONS = {
    **DEFAULT_OPTIONS,
    "num_predict": 4096,
}


def _call_ollama(
    prompt: str,
    *,
    model: str,
    base_url: str,
    timeout_seconds: int,
    options: Dict[str, Any],
) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": options,
    }

    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        result = json.loads(response.read().decode("utf-8"))

    content = (result.get("message") or {}).get("content", "").strip()
    if not content:
        raise ValueError(f"empty response ({result})")
    return content


def _children_context() -> str:
    lines = []
    for child in get_children_info().values():
        first_name = child["name"].split()[0]
        lines.append(
            f"- {child['name']} ({first_name}): class {child['class']}, "
            f"grade {child['grade']}, {child['division']}"
        )
    return "\n".join(lines)


def _build_extract_prompt(
    msg: Dict[str, Any],
    *,
    index: int,
    total: int,
    today_date: str,
    seven_days_from_now: str,
) -> str:
    body = clean_email_body(msg["body"])
    return f"""You extract facts from school emails for a parent.

Rules:
- Copy dates, deadlines, and requirements exactly as written
- List EVERY date, deadline, event, and parent action in the email
- Use ONLY information from the email below
- Do NOT invent or guess

Children at this school:
{_children_context()}

Today's date: {today_date}
Action item window (deadlines between these dates only): {today_date} to {seven_days_from_now}

Email {index} of {total}:
From: {msg['from']}
Subject: {msg['subject']}
Date: {msg['date']}

Body:
{body}

Reply with these exact section headers and bullet points under each:

APPLIES TO:
ACTION ITEMS:
EVENTS:
KEY FACTS:

Section rules:
- APPLIES TO: all children, or specific child names, or "None"
- ACTION ITEMS: parent tasks with deadlines inside the action item window only, or "None"
- EVENTS: future dates after {today_date}, or "None"
- KEY FACTS: all other important details including past/near deadlines, links, locations, or "None"
"""


def _merge_output_sections(today_date: str, seven_days_from_now: str) -> str:
    sections = []
    for child in get_children_info().values():
        sections.append(
            f"""## For {child['name'].upper()} (Class: {child['class']}, Grade {child['grade']}, {child['division']}):

### SUMMARY

### ACTION ITEMS (Next 7 Days)

### UPCOMING EVENTS

### OTHER INFO
"""
        )

    return (
        f"""Write a parent report using ONLY the extracted facts below.
Do NOT repeat these instructions. Fill in each section with bullet points or short text.
If a section has no relevant facts, write "None" or "No action items in the next 7 days".

Today: {today_date}
Action item window: {today_date} to {seven_days_from_now}

Use this exact structure:

"""
        + "\n".join(sections)
        + """
## GENERAL (All Children)
"""
    )


def _build_merge_prompt(
    extractions: str,
    *,
    today_date: str,
    seven_days_from_now: str,
) -> str:
    return (
        _merge_output_sections(today_date, seven_days_from_now)
        + """
EXTRACTED FACTS:
"""
        + extractions
        + """

Write the completed report now.
"""
    )


def _summary_looks_valid(summary: str) -> bool:
    if "Brief overview of emails relevant to" in summary:
        return False

    for child in get_children_info().values():
        if child["name"].upper() not in summary.upper():
            return False

    return bool(summary.strip())


def _format_extraction_block(index: int, subject: str, extraction: str) -> str:
    return f"--- Extraction {index}: {subject} ---\n{extraction.strip()}\n"


def _save_debug_artifact(filename: str, content: str) -> None:
    ensure_cache_dir()
    path = os.path.join(CACHE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def summarize_with_ollama(
    messages: List[Dict[str, Any]],
    *,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_BASE_URL,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """
    Summarize messages using map-reduce over a local Ollama model.

    Args:
        messages: List of decoded message dictionaries
        model: Ollama model name (default: llama3.2:1b)
        base_url: Ollama API base URL
        timeout_seconds: Unused legacy parameter kept for compatibility

    Returns:
        Summary text from Ollama or an error message
    """
    del timeout_seconds

    if not messages:
        return "No messages to summarize."

    today = datetime.now()
    today_date = today.strftime("%Y-%m-%d")
    seven_days_from_now = (today + timedelta(days=7)).strftime("%Y-%m-%d")

    print(f"  Using Ollama model: {model} (map-reduce)")

    extraction_blocks: List[str] = []
    failed_extractions: List[str] = []

    for index, msg in enumerate(messages, 1):
        subject = msg.get("subject") or "(no subject)"
        print(f"  Extracting email {index}/{len(messages)}: {subject[:70]}")

        prompt = _build_extract_prompt(
            msg,
            index=index,
            total=len(messages),
            today_date=today_date,
            seven_days_from_now=seven_days_from_now,
        )

        try:
            extraction = _call_ollama(
                prompt,
                model=model,
                base_url=base_url,
                timeout_seconds=EXTRACT_TIMEOUT_SECONDS,
                options=EXTRACT_OPTIONS,
            )
            extraction_blocks.append(
                _format_extraction_block(index, subject, extraction)
            )
        except Exception as e:
            failed_extractions.append(f"Email {index} ({subject}): {e}")

    if not extraction_blocks:
        return "Error extracting email facts:\n" + "\n".join(failed_extractions)

    extractions = "\n".join(extraction_blocks)
    _save_debug_artifact("temp.extractions.txt", extractions)

    merge_prompt = _build_merge_prompt(
        extractions,
        today_date=today_date,
        seven_days_from_now=seven_days_from_now,
    )
    _save_debug_artifact("temp.merge.prompt.txt", merge_prompt)

    print(f"  Merging {len(extraction_blocks)} extraction(s)...")

    try:
        summary = _call_ollama(
            merge_prompt,
            model=model,
            base_url=base_url,
            timeout_seconds=MERGE_TIMEOUT_SECONDS,
            options=MERGE_OPTIONS,
        )

        if not _summary_looks_valid(summary):
            print("  Merge output looked incomplete, retrying with simplified prompt...")
            retry_prompt = (
                "Combine these school email facts into a short parent report.\n"
                "Use bullet points. Include both children: "
                + ", ".join(child["name"] for child in get_children_info().values())
                + ".\n\n"
                + extractions
            )
            summary = _call_ollama(
                retry_prompt,
                model=model,
                base_url=base_url,
                timeout_seconds=MERGE_TIMEOUT_SECONDS,
                options=MERGE_OPTIONS,
            )
    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), TimeoutError):
            return "Ollama merge request timed out."
        return (
            f"Could not connect to Ollama at {base_url}. "
            "Make sure Ollama is running (ollama serve)."
        )
    except json.JSONDecodeError as e:
        return f"Error parsing Ollama response: {e}"
    except Exception as e:
        return f"Error merging extractions: {e}"

    if failed_extractions:
        summary += "\n\n---\n\n**Note:** Some emails could not be extracted:\n"
        summary += "\n".join(f"- {item}" for item in failed_extractions)

    return summary
