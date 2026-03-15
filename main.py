#!/usr/bin/env python3
"""
Gmail Automation - Main Entry Point

Read Gmail messages from specific senders (@ims.edu.hk or @veracross.com)
using the Gmail API. Summarizes messages using Qwen CLI and highlights
action items for parents in the next 7 days.

Results are cached for 12 hours to avoid excessive API calls.
Use --force-refresh to bypass cache.
"""

import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

from config.settings import CACHE_EXPIRY_HOURS
from services.gmail_auth import get_gmail_service
from services.gmail_client import read_messages
from services.qwen_summarizer import summarize_with_qwen
from utils.cache import get_cache_key, load_from_cache, save_to_cache
from utils.message_parser import format_messages_for_summary

# Load environment variables from .env file
load_dotenv()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Read and summarize school emails from IMS and Veracross"
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force refresh from Gmail API, bypassing cache"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to search back (default: 30)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Max results per domain (default: 50)"
    )
    return parser.parse_args()


def main():
    """Main function to read, summarize, and highlight action items."""
    args = parse_arguments()

    try:
        print("Connecting to Gmail...")
        service = get_gmail_service()

        # Generate cache key
        cache_key = get_cache_key(args.days, args.max_results)

        # Try to load from cache
        messages = None
        if not args.force_refresh:
            print(f"\nChecking cache (expires after {CACHE_EXPIRY_HOURS} hours)...")
            messages = load_from_cache(cache_key)

        # Fetch from API if cache miss or force refresh
        if messages is None:
            if args.force_refresh:
                print(f"\nForce refresh - fetching from Gmail API...")
            else:
                print(f"\nCache miss - fetching from Gmail API...")
            messages = read_messages(service, days=args.days, max_results_per_domain=args.max_results)
            save_to_cache(cache_key, messages)

        if not messages:
            print("\nNo messages found from @ims.edu.hk or @veracross.com")
            return

        print(f"\nProcessing {len(messages)} message(s)")
        print(format_messages_for_summary(messages))

        print("\n" + "="*60)
        print("AI SUMMARY & ACTION ITEMS")
        print("="*60 + "\n")

        summary = summarize_with_qwen(messages, cache_key)
        print(summary)

        print("\n" + "="*60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if not args.force_refresh:
            print(f"Cache valid until: {(datetime.now() + timedelta(hours=CACHE_EXPIRY_HOURS)).strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
