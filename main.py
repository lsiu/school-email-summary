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
import os
import sys
from datetime import datetime, timedelta

from config import (
    get_cache_expiry_hours,
    get_children_info,
    get_config,
    get_sender_domains,
    load_config,
)
from services.gmail_auth import get_gmail_service
from services.gmail_client import read_messages
from services.qwen_summarizer import summarize_with_qwen
from utils.cache import (
    load_from_cache,
    save_to_cache,
)
from utils.message_parser import format_messages_for_summary


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Read and summarize school emails from IMS and Veracross"
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force refresh from Gmail API, bypassing cache",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to search back (default: 30)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Max results per domain (default: 50)",
    )
    parser.add_argument(
        "--show-config", action="store_true", help="Show loaded configuration and exit"
    )
    return parser.parse_args()


def show_config():
    """Display loaded configuration."""
    config = get_config()
    children_info = get_children_info()

    print("=" * 60)
    print("LOADED CONFIGURATION")
    print("=" * 60)

    print(f"\nSchool: {config.get('school', {}).get('name', 'Unknown')}")

    print(f"\nChildren ({len(children_info)}):")
    for key, child in children_info.items():
        print(f"  - {child['name']}")
        print(f"      Class: {child['class']}")
        print(f"      Current Grade: {child['grade']} ({child['school_year']})")
        print(f"      Division: {child['division']}")

    print("\nEmail Settings:")
    print(f"  Sender domains: {', '.join(get_sender_domains())}")
    print(f"  Cache expiry: {get_cache_expiry_hours()} hours")

    print("\n" + "=" * 60)


def main():
    """Main function to read, summarize, and highlight action items."""
    args = parse_arguments()

    try:
        # Load configuration from config.yaml
        load_config()

        # Show configuration if requested
        if args.show_config:
            show_config()
            return

        # Try to load from cache
        messages = None
        if not args.force_refresh:
            print(
                f"\nChecking cache (expires after {get_cache_expiry_hours()} hours)..."
            )
            messages = load_from_cache()

        # Fetch from API if cache miss or force refresh
        if messages is None:
            if args.force_refresh:
                print("\nForce refresh - fetching from Gmail API...")
            else:
                print("\nCache miss - fetching from Gmail API...")

            print("Connecting to Gmail...")
            service = get_gmail_service()
            messages = read_messages(
                service, days=args.days, max_results_per_domain=args.max_results
            )
            save_to_cache(messages)

        if not messages:
            print("\nNo messages found from " + ", ".join(get_sender_domains()))
            return

        print(f"\nProcessing {len(messages)} message(s)")
        print(format_messages_for_summary(messages))

        print("\n" + "=" * 60)
        print("AI SUMMARY & ACTION ITEMS")
        print("=" * 60 + "\n")

        summary = summarize_with_qwen(messages)
        print(summary)

        # Save summary to file
        summary_dir = "summary"
        os.makedirs(summary_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = os.path.join(summary_dir, f"summary_{timestamp}.md")

        try:
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write("# IMS Email Summary\n\n")
                f.write(
                    f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )
                f.write(f"**Emails processed:** {len(messages)}\n\n")
                f.write("---\n\n")
                f.write(summary)
                f.write("\n\n---\n\n")
                f.write(
                    f"**Cache valid until:** {(datetime.now() + timedelta(hours=get_cache_expiry_hours())).strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
            print(f"\n✓ Summary saved to: {summary_file}")
        except Exception as e:
            print(f"\nWarning: Could not save summary to file: {e}")

        print("\n" + "=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if not args.force_refresh:
            print(
                f"Cache valid until: {(datetime.now() + timedelta(hours=get_cache_expiry_hours())).strftime('%Y-%m-%d %H:%M:%S')}"
            )
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(
            "\nHint: Copy 'config.yaml.example' to 'config.yaml' and edit with your family's information."
        )
        sys.exit(1)
    except ImportError as e:
        print(f"Error: {e}")
        print("\nHint: Install required packages with: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
