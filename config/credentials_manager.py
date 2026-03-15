"""
Credentials manager for encrypted Gmail OAuth credentials.

Handles encryption, decryption, and password management for
distributed credentials.json files.

Security Model:
- credentials.enc: Encrypted with Fernet (AES 128-bit)
- Password: Shared separately via WhatsApp/email
- .key file: Base64-encoded password (gitignored, not shared)
"""

import os
import base64
import getpass
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# File paths
CREDENTIALS_ENC_PATH = "credentials.enc"
KEY_FILE_PATH = ".key"

# Encryption settings
SALT_LENGTH = 16
PBKDF2_ITERATIONS = 480000


def get_or_prompt_password() -> str:
    """
    Get password from .key file or prompt user.
    
    Returns:
        Password string
    """
    # Try to load stored password
    if os.path.exists(KEY_FILE_PATH):
        try:
            with open(KEY_FILE_PATH, 'r') as f:
                stored_password = base64.b64decode(f.read().strip()).decode('utf-8')
            return stored_password
        except Exception:
            # If loading fails, prompt for new password
            pass
    
    # Prompt for password
    print("Enter credentials password: ", end="")
    password = getpass.getpass("")
    
    # Store password for future runs
    try:
        with open(KEY_FILE_PATH, 'w') as f:
            f.write(base64.b64encode(password.encode('utf-8')).decode('utf-8'))
        print("Password saved for future runs.")
    except Exception as e:
        print(f"Warning: Could not save password: {e}")
    
    return password


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive encryption key from password using PBKDF2.
    
    Args:
        password: User password
        salt: Random salt from encrypted file
        
    Returns:
        Fernet-compatible key
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def decrypt_credentials(password: str) -> dict:
    """
    Decrypt credentials.enc and return the credentials dictionary.
    
    This returns the OAuth client configuration (like credentials.json),
    NOT authorized user credentials. The OAuth flow still needs to run.

    Args:
        password: Decryption password

    Returns:
        Dictionary containing OAuth client configuration

    Raises:
        FileNotFoundError: If credentials.enc not found
        ValueError: If password is incorrect
    """
    if not os.path.exists(CREDENTIALS_ENC_PATH):
        raise FileNotFoundError(
            f"Encrypted credentials file not found: {CREDENTIALS_ENC_PATH}\n"
            "Please download credentials.enc and place it in the project folder."
        )

    # Read encrypted file
    with open(CREDENTIALS_ENC_PATH, 'rb') as f:
        file_data = f.read()

    # Extract salt (first 16 bytes) and encrypted data
    salt = file_data[:SALT_LENGTH]
    encrypted_data = file_data[SALT_LENGTH:]

    # Derive key and decrypt
    key = derive_key(password, salt)
    fernet = Fernet(key)

    try:
        decrypted_data = fernet.decrypt(encrypted_data)
    except Exception as e:
        raise ValueError(
            "Incorrect password. Please contact the administrator for the correct password."
        ) from e

    # Parse credentials JSON
    import json
    return json.loads(decrypted_data.decode('utf-8'))


def is_encrypted_setup() -> bool:
    """
    Check if encrypted credentials setup is in use.
    
    Returns:
        True if credentials.enc exists
    """
    return os.path.exists(CREDENTIALS_ENC_PATH)
