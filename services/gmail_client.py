"""
Gmail API client for reading messages.

Provides functions to search and retrieve Gmail messages from
specified sender domains within a given time range.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

from googleapiclient.errors import HttpError

from config import get_sender_domains
from utils.message_parser import decode_message


def read_messages(
    service,
    days: int = 30,
    max_results_per_domain: int = 50
) -> List[Dict[str, Any]]:
    """
    Read messages from specified sender domains within the last N days.

    Args:
        service: Authorized Gmail API service object
        days: Number of days to search back (default: 30)
        max_results_per_domain: Maximum results per domain (default: 50)

    Returns:
        List of decoded message dictionaries
    """
    messages = []
    sender_domains = get_sender_domains()
    date_filter = f"after:{(datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')}"

    for domain in sender_domains:
        query = f"from:{domain} {date_filter}"
        print(f"  Searching: {query}")
        try:
            results = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results_per_domain)
                .execute()
            )

            message_list = results.get("messages", [])
            print(f"  Found {len(message_list)} message(s) from {domain}")

            for msg in message_list:
                full_message = (
                    service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="raw")
                    .execute()
                )
                decoded = decode_message(full_message)
                messages.append(decoded)

        except HttpError as error:
            print(f"Error fetching messages from {domain}: {error}")

    return messages
