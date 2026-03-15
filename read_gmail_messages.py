#!/usr/bin/env python3
"""
Read Gmail messages from specific senders (@ims.edu.hk or @veracross.com)
using the Gmail API. Summarizes messages using Qwen CLI and highlights
action items for parents in the next 7 days.

Results are cached for 12 hours to avoid excessive API calls.
Use --force-refresh to bypass cache.
"""

import os
import sys
import base64
import subprocess
import json
import hashlib
import argparse
from datetime import datetime, timedelta
from email import message_from_bytes
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables from .env file
load_dotenv()

# Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Sender domains to filter
SENDER_DOMAINS = ["@ims.edu.hk", "@veracross.com"]

# Cache settings
CACHE_DIR = ".cache"
CACHE_EXPIRY_HOURS = 12

# Prompt for Qwen CLI to summarize and extract action items
SUMMARIZE_PROMPT = """
You are helping a parent track school-related action items from IMS (International Montessori School) emails.

There are TWO children:
- **Leona Siu** - Class: **Indus**
- **Leonidas Siu** - Class: **Bauhinia**

Use the class names (Indus/Bauhinia) to help classify which emails are for which child.

TODAY'S DATE: {today_date}

Analyze the following email(s) and provide SEPARATE summaries for EACH child:

---

## For LEONA SIU (Class: Indus):

### SUMMARY
Brief overview of emails relevant to Leona (look for "Indus" class references)

### ACTION ITEMS (Next 7 Days)
List any actions the parent needs to take within the next 7 days for Leona:
- What needs to be done
- Deadline (if specified)
- Any relevant details (links, forms, payments, etc.)
- Mark **URGENT** if deadline is within 48 hours
- Only include action items with deadlines from {today_date} to {seven_days_from_now}

### UPCOMING EVENTS
Events, meetings, or important dates for Leona that are **in the future** (after {today_date}).
Do NOT include events that have already passed.
Include the event date if mentioned.

### OTHER INFO
Any other relevant information for Leona

---

## For LEONIDAS SIU (Class: Bauhinia):

### SUMMARY
Brief overview of emails relevant to Leonidas (look for "Bauhinia" class references)

### ACTION ITEMS (Next 7 Days)
List any actions the parent needs to take within the next 7 days for Leonidas:
- What needs to be done
- Deadline (if specified)
- Any relevant details (links, forms, payments, etc.)
- Mark **URGENT** if deadline is within 48 hours
- Only include action items with deadlines from {today_date} to {seven_days_from_now}

### UPCOMING EVENTS
Events, meetings, or important dates for Leonidas that are **in the future** (after {today_date}).
Do NOT include events that have already passed.
Include the event date if mentioned.

---

## GENERAL (Both Children)
Any information that applies to both children

---

**IMPORTANT:**
- Only include events that are **after {today_date}** in the UPCOMING EVENTS sections
- If an event date has already passed, do NOT list it as "upcoming"
- If there are NO action items in the next 7 days for a child, clearly state "No action items in the next 7 days" for that child
- Use class names (Indus = Leona, Bauhinia = Leonidas) to classify emails even when child names are not mentioned

---
EMAILS:
"""


def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def get_cache_key(days, max_results):
    """Generate a cache key based on search parameters."""
    params = f"{SENDER_DOMAINS}-{days}-{max_results}"
    return hashlib.md5(params.encode()).hexdigest()


def load_from_cache(cache_key):
    """Load messages from cache if available and not expired."""
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        # Check if cache is expired
        cached_time = datetime.fromisoformat(cache_data['timestamp'])
        if datetime.now() - cached_time > timedelta(hours=CACHE_EXPIRY_HOURS):
            print(f"  Cache expired (older than {CACHE_EXPIRY_HOURS} hours)")
            return None
        
        print(f"  Loaded from cache ({len(cache_data['messages'])} messages)")
        return cache_data['messages']
    
    except Exception as e:
        print(f"  Warning: Could not load cache: {e}")
        return None


def save_to_cache(cache_key, messages, prompt=None):
    """Save messages and optional prompt to cache."""
    ensure_cache_dir()
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'messages': messages
    }
    
    # Save prompt if provided
    if prompt:
        prompt_file = os.path.join(CACHE_DIR, f"{cache_key}.prompt.txt")
        try:
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt)
            cache_data['prompt_file'] = prompt_file
        except Exception as e:
            print(f"  Warning: Could not save prompt: {e}")
    
    try:
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        print(f"  Cached to {cache_file}")
    except Exception as e:
        print(f"  Warning: Could not save cache: {e}")


def get_gmail_service():
    """Authenticate and build the Gmail API service."""
    creds = None
    token_path = "token.json"
    credentials_path = "credentials.json"

    # Load API key from environment
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("Warning: API_KEY not found in .env file (optional for OAuth flow)")

    # Check for existing token
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"Warning: Could not load token.json: {e}")
            creds = None

    # Refresh or obtain new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Warning: Could not refresh credentials: {e}")
                creds = None

        if not creds or not creds.valid:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"Credentials file '{credentials_path}' not found. "
                    "Please download it from Google Cloud Console."
                )

            # Validate credentials.json has real values
            with open(credentials_path, 'r') as f:
                creds_data = json.load(f)
            client_id = creds_data.get('web', {}).get('client_id', '')
            if 'YOUR_CLIENT_ID' in client_id or not client_id:
                raise ValueError(
                    "credentials.json contains placeholder values. "
                    "Please replace with real credentials from Google Cloud Console."
                )

            try:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"Error: Could not complete OAuth flow: {e}")
                print("\nIn a headless environment, run the script on your local machine first")
                print("to generate token.json, then copy it to this environment.")
                sys.exit(1)

            # Save credentials for future use
            with open(token_path, "w") as token:
                token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def decode_message(message):
    """Decode a Gmail message and extract its content."""
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


def read_messages(service, days=30, max_results_per_domain=50):
    """Read messages from specified sender domains within the last N days."""
    messages = []
    date_filter = f"after:{(datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')}"

    for domain in SENDER_DOMAINS:
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


def summarize_with_qwen(messages, cache_key=None):
    """Use Qwen CLI to summarize messages and extract action items."""
    # Calculate dates for the prompt
    today = datetime.now()
    today_date = today.strftime("%Y-%m-%d")
    seven_days_from_now = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Format the prompt with actual dates
    prompt_template = SUMMARIZE_PROMPT.format(
        today_date=today_date,
        seven_days_from_now=seven_days_from_now
    )
    
    # Prepare email content
    email_content = ""
    for i, msg in enumerate(messages, 1):
        email_content += f"\n--- Email {i} ---\n"
        email_content += f"From: {msg['from']}\n"
        email_content += f"Subject: {msg['subject']}\n"
        email_content += f"Date: {msg['date']}\n"
        email_content += f"Body:\n{msg['body']}\n"

    prompt = prompt_template + email_content

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


def format_messages_for_summary(messages):
    """Format messages for display before Qwen summary."""
    output = []
    for i, msg in enumerate(messages, 1):
        output.append(f"\n{'='*60}")
        output.append(f"Message {i}:")
        output.append(f"  From:    {msg['from']}")
        output.append(f"  Subject: {msg['subject']}")
        output.append(f"  Date:    {msg['date']}")
        output.append(f"{'='*60}")
    return "\n".join(output)


def main():
    """Main function to read, summarize, and highlight action items."""
    # Parse command line arguments
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
    args = parser.parse_args()

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
