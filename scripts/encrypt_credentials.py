#!/usr/bin/env python3
"""
Encrypt/Decrypt credentials.json for secure distribution.

Run this script to encrypt your credentials.json file.
The encrypted file (credentials.enc) can be safely distributed.
Share the password separately via WhatsApp, email, or phone.

Usage:
    python encrypt_credentials.py                    # Encrypt credentials.json
    python encrypt_credentials.py --decrypt          # Decrypt credentials.enc
    python encrypt_credentials.py --decrypt -f path  # Decrypt custom file
"""

import os
import sys
import base64
import argparse
import getpass
import json

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


# Encryption settings
SALT_LENGTH = 16
PBKDF2_ITERATIONS = 480000

# Default file paths (relative to project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, "credentials.json")
DEFAULT_ENCRYPTED_FILE = os.path.join(PROJECT_ROOT, "credentials.enc")


def encrypt_credentials(password: str, input_file: str = None, output_file: str = None) -> None:
    """
    Encrypt credentials.json using Fernet encryption.

    Args:
        password: Password to encrypt the file
        input_file: Path to input file (default: credentials.json)
        output_file: Path to output file (default: credentials.enc)
    """
    input_file = input_file or DEFAULT_CREDENTIALS_FILE
    output_file = output_file or DEFAULT_ENCRYPTED_FILE

    # Generate random salt
    salt = os.urandom(SALT_LENGTH)

    # Derive encryption key from password using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

    # Create Fernet cipher
    f = Fernet(key)

    # Read input file
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        print("Please ensure credentials.json is in the project directory.")
        return

    with open(input_file, 'rb') as file:
        original_data = file.read()

    # Encrypt the data
    encrypted_data = f.encrypt(original_data)

    # Save encrypted file (salt + encrypted data)
    with open(output_file, 'wb') as file:
        file.write(salt + encrypted_data)

    print(f"✓ {output_file} created successfully")
    print()
    print("Next steps:")
    print(f"  1. Distribute {output_file} to users")
    print("  2. Share the password via a SEPARATE channel (WhatsApp, email, phone)")
    print(f"  3. Optionally delete {input_file} for security")
    print()
    print("Security note:")
    print("  - The encrypted file can be safely shared")
    print("  - Never share the password in the same message as the file")
    print("  - Users will only need to enter the password once")


def decrypt_credentials(password: str, input_file: str = None) -> None:
    """
    Decrypt credentials.enc and print the content.

    Args:
        password: Password to decrypt the file
        input_file: Path to encrypted file (default: credentials.enc)
    """
    input_file = input_file or DEFAULT_ENCRYPTED_FILE

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return

    # Read encrypted file
    with open(input_file, 'rb') as f:
        file_data = f.read()

    # Extract salt (first 16 bytes) and encrypted data
    salt = file_data[:SALT_LENGTH]
    encrypted_data = file_data[SALT_LENGTH:]

    # Derive key and decrypt
    key = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    ).derive(password.encode())
    
    f = Fernet(base64.urlsafe_b64encode(key))

    try:
        decrypted_data = f.decrypt(encrypted_data)
    except Exception as e:
        print("Error: Incorrect password or corrupted file!")
        return

    # Parse and pretty-print JSON
    try:
        creds_data = json.loads(decrypted_data.decode('utf-8'))
        print("Decrypted credentials:")
        print("=" * 50)
        print(json.dumps(creds_data, indent=2))
        print("=" * 50)
    except json.JSONDecodeError:
        print("Decrypted content (not valid JSON):")
        print("=" * 50)
        print(decrypted_data.decode('utf-8'))
        print("=" * 50)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Encrypt or decrypt credentials for IMS Gmail Automation"
    )
    parser.add_argument(
        "--decrypt",
        action="store_true",
        help="Decrypt credentials.enc instead of encrypting"
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        help="Path to input file (credentials.json for encrypt, credentials.enc for decrypt)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Path to output file (only for encrypt mode, default: credentials.enc)"
    )
    parser.add_argument(
        "password",
        nargs="?",
        help="Encryption/decryption password (if not provided, will prompt)"
    )

    args = parser.parse_args()

    print("IMS Gmail Automation - Credential Management")
    print("=" * 50)
    print()

    # Get password
    if args.password:
        password = args.password
    else:
        password = getpass.getpass("Enter password: ")
        if args.decrypt:
            # No confirmation needed for decrypt
            pass
        else:
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Error: Passwords do not match!")
                return

            if len(password) < 8:
                print("Warning: Password is less than 8 characters.")
                response = input("Continue anyway? (y/n): ")
                if response.lower() != 'y':
                    return

    print()

    if args.decrypt:
        # Decrypt mode
        input_file = args.file or DEFAULT_ENCRYPTED_FILE
        decrypt_credentials(password, input_file)
    else:
        # Encrypt mode
        input_file = args.file or DEFAULT_CREDENTIALS_FILE
        output_file = args.output or DEFAULT_ENCRYPTED_FILE
        encrypt_credentials(password, input_file, output_file)


if __name__ == "__main__":
    main()
