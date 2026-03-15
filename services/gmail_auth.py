"""
Gmail OAuth authentication service.

Handles authentication with the Gmail API using encrypted OAuth 2.0 credentials.
Manages token refresh and password-based decryption.
"""

import sys

from config.credentials_manager import get_gmail_service as get_encrypted_gmail_service, is_encrypted_setup


def get_gmail_service():
    """
    Authenticate and build the Gmail API service.
    
    Uses encrypted credentials (credentials.enc) if available,
    otherwise falls back to standard credentials.json flow.
    
    Returns:
        Authorized Gmail API service object
        
    Raises:
        FileNotFoundError: If credentials file is missing
        ValueError: If password is incorrect (for encrypted setup)
        SystemExit: If OAuth flow fails in headless environment
    """
    # Check if using encrypted credentials
    if is_encrypted_setup():
        return get_encrypted_gmail_service()
    
    # Fall back to standard credentials.json flow
    return _get_standard_gmail_service()


def _get_standard_gmail_service():
    """
    Standard Gmail API authentication using credentials.json.
    
    Returns:
        Authorized Gmail API service object
    """
    import os
    import json
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    
    # Import SCOPES from settings
    try:
        from config.settings import SCOPES
    except ImportError:
        SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    
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
                    f"Credentials file not found. Please provide either:\n"
                    f"  - credentials.enc (encrypted, contact administrator)\n"
                    f"  - credentials.json (from Google Cloud Console)"
                )
            
            # Validate credentials.json has real values
            with open(credentials_path, 'r') as f:
                creds_data = json.load(f)
            client_id = creds_data.get('web', {}).get('client_id', '')
            if 'YOUR_CLIENT_ID' in client_id or not client_id:
                raise ValueError(
                    "credentials.json contains placeholder values. "
                    "Please obtain valid credentials from the administrator."
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
