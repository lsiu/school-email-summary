"""
Message parsing and formatting utilities for Gmail messages.

Handles both plain text and HTML emails, converting HTML to readable text.
"""

import base64
import html2text
from email import message_from_bytes
from typing import Dict, List, Any, Optional


def decode_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decode a Gmail message and extract its content.
    
    Handles both text/plain and text/html emails. For HTML emails,
    converts to plain text using html2text library.

    Args:
        message: Raw Gmail message dictionary with 'id' and 'raw' fields

    Returns:
        Dictionary with decoded message fields: id, from, to, subject, date, body
    """
    try:
        msg_bytes = base64.urlsafe_b64decode(message["raw"])
        msg = message_from_bytes(msg_bytes)

        subject = msg.get("Subject", "")
        text_body = ""
        html_body = ""

        # Get body content - collect both text and HTML parts
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                try:
                    payload = part.get_payload(decode=True)
                    if payload is None:
                        continue

                    if content_type == "text/plain":
                        text_body = payload.decode()
                    elif content_type == "text/html":
                        html_body = payload.decode()
                except Exception:
                    pass
        else:
            # Non-multipart message
            try:
                body = msg.get_payload(decode=True)
                if body:
                    content_type = msg.get_content_type()
                    if content_type == "text/html":
                        html_body = body.decode()
                    else:
                        text_body = body.decode()
            except Exception:
                pass

        # Prefer text/plain if available and non-empty
        if text_body.strip():
            body = text_body
        elif html_body.strip():
            # Convert HTML to text using html2text
            body = html_to_text(html_body)
        else:
            body = ""

        return {
            "id": message["id"],
            "from": msg.get("From", ""),
            "to": msg.get("To", ""),
            "subject": subject,
            "date": msg.get("Date", ""),
            "body": body,
        }
    except Exception as e:
        return {
            "id": message.get("id", "unknown"),
            "from": "",
            "to": "",
            "subject": "",
            "date": "",
            "body": f"Error decoding message: {e}",
        }


def html_to_text(html: str) -> str:
    """
    Convert HTML content to plain text.
    
    Args:
        html: HTML string to convert
        
    Returns:
        Plain text extracted from HTML
    """
    if not html:
        return ""
    
    try:
        # Configure html2text for cleaner output
        h = html2text.HTML2Text()
        h.ignore_links = False  # Keep links for reference
        h.ignore_images = True  # Skip images
        h.ignore_emphasis = False  # Keep emphasis markers
        h.body_width = 0  # Don't wrap text
        
        return h.handle(html)
    except Exception:
        # Fallback: simple tag stripping if html2text fails
        import re
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text


def format_messages_for_summary(messages: List[Dict[str, Any]]) -> str:
    """
    Format messages for display before AI summary.

    Args:
        messages: List of decoded message dictionaries

    Returns:
        Formatted string with message summaries
    """
    output = []
    for i, msg in enumerate(messages, 1):
        output.append(f"\n{'='*60}")
        output.append(f"Message {i}:")
        output.append(f"  From:    {msg['from']}")
        output.append(f"  Subject: {msg['subject']}")
        output.append(f"  Date:    {msg['date']}")
        output.append(f"{'='*60}")
    return "\n".join(output)
