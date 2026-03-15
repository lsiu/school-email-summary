"""
Gmail OAuth authentication service.

Handles authentication with the Gmail API using either:
- Encrypted credentials (credentials.enc)
- Standard credentials file (credentials.json)

Manages token refresh and OAuth flow.
"""

import os
import sys
import json
import tempfile
from typing import Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config.credentials_manager import (
    is_encrypted_setup,
    get_or_prompt_password,
    decrypt_credentials,
)


def _get_gmail_service_from_client_config(creds_data: Dict[str, Any]) -> Any:
    """
    Shared OAuth flow - works with any OAuth client config.
    
    This function handles:
    1. Loading/creating SCOPES
    2. Checking for existing token.json
    3. Refreshing expired tokens
    4. Running OAuth flow if needed
    5. Building and returning Gmail API service
    
    Args:
        creds_data: OAuth client configuration dictionary
                    (same format as credentials.json)
        
    Returns:
        Authorized Gmail API service object
        
    Raises:
        SystemExit: If OAuth flow fails in headless environment
    """
    # Import SCOPES
    try:
        from config.settings import SCOPES
    except ImportError:
        SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    
    token_path = "token.json"
    creds = None
    
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
            # Write credentials to temp file for OAuth flow
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(creds_data, f)
                temp_creds_path = f.name
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(temp_creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"Error: Could not complete OAuth flow: {e}")
                print("\nIn a headless environment, run the script on your local machine first")
                print("to generate token.json, then copy it to this environment.")
                sys.exit(1)
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_creds_path)
                except:
                    pass
            
            # Save credentials for future use
            with open(token_path, "w") as token:
                token.write(creds.to_json())
    
    # Build and return service
    return build("gmail", "v1", credentials=creds)


def get_gmail_service():
    """
    Authenticate and build the Gmail API service.
    
    Automatically detects and uses:
    1. Encrypted credentials (credentials.enc) - if present
    2. Standard credentials (credentials.json) - fallback
    
    Returns:
        Authorized Gmail API service object
        
    Raises:
        FileNotFoundError: If no credentials file found
        ValueError: If credentials contain placeholder values
        SystemExit: If OAuth flow fails in headless environment
    """
    # Check if using encrypted credentials
    if is_encrypted_setup():
        # Get password and decrypt
        password = get_or_prompt_password()
        creds_data = decrypt_credentials(password)
        return _get_gmail_service_from_client_config(creds_data)
    
    # Fall back to standard credentials.json
    credentials_path = "credentials.json"
    
    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"Credentials file not found. Please provide either:\n"
            f"  - credentials.enc (encrypted, contact administrator)\n"
            f"  - credentials.json (from Google Cloud Console)"
        )
    
    # Load and validate credentials
    with open(credentials_path, 'r') as f:
        creds_data = json.load(f)
    
    client_id = creds_data.get('web', {}).get('client_id', '')
    if 'YOUR_CLIENT_ID' in client_id or not client_id:
        raise ValueError(
            "credentials.json contains placeholder values. "
            "Please obtain valid credentials from the administrator."
        )
    
    return _get_gmail_service_from_client_config(creds_data)
