"""
Gmail OAuth authentication service.

Handles authentication with the Gmail API using OAuth 2.0 credentials.
Manages token refresh and initial authentication flow.
"""

import os
import sys
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config.settings import SCOPES


def get_gmail_service():
    """
    Authenticate and build the Gmail API service.

    Returns:
        Authorized Gmail API service object

    Raises:
        FileNotFoundError: If credentials.json is missing
        ValueError: If credentials.json contains placeholder values
        SystemExit: If OAuth flow fails in headless environment
    """
    creds = None
    token_path = "token.json"
    credentials_path = "credentials.json"

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
