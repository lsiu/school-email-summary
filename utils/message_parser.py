"""
Message parsing and formatting utilities for Gmail messages.
"""

import base64
from email import message_from_bytes
from typing import Dict, List, Any


def decode_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decode a Gmail message and extract its content.
    
    Args:
        message: Raw Gmail message dictionary with 'id' and 'raw' fields
        
    Returns:
        Dictionary with decoded message fields: id, from, to, subject, date, body
    """
    try:
        msg_bytes = base64.urlsafe_b64decode(message["raw"])
        msg = message_from_bytes(msg_bytes)

        subject = msg.get("Subject", "")
        body = ""

        # Get body content
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except Exception:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode()
            except Exception:
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
