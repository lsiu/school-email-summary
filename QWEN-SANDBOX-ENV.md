# Qwen Sandbox Environment

This document describes the sandbox environment for the Qwen Code assistant.

## System Information

- **OS**: Debian 12 (bookworm)
- **Architecture**: x86_64
- **User**: root
- **Working Directory**: `/d/src/family-automation`

## Python Environment

- **Python Version**: 3.11.2
- **Python Command**: `python3` (not `python`)
- **pip Command**: `pip3`
- **Installation Method**: System-wide with `--break-system-packages` flag

### Installing Dependencies

```bash
# In Qwen Sandbox (as root, safe to install system-wide)
pip3 install --break-system-packages -r requirements.txt

# On Windows (in .venv)
.venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

### Installed Packages

Core packages for Gmail API:
- `google-auth>=2.49.1`
- `google-auth-oauthlib>=1.3.0`
- `google-api-python-client>=2.192.0`
- `python-dotenv>=1.2.2`

## Important Notes

1. **No `python` command**: Use `python3` instead
2. **No `pip` command**: Use `pip3` instead
3. **Running as root**: Commands don't need `sudo`
4. **Virtual environments**: 
   - Windows `.venv` is incompatible (platform-specific binaries like `cryptography`)
   - In Qwen sandbox: always use `pip3 install --break-system-packages` (safe in isolated container)
5. **Package installation**: Requires `--break-system-packages` flag for pip in this Debian environment

## File Structure

```
/d/src/family-automation/
├── read_gmail_messages.py    # Gmail API script
├── requirements.txt          # Python dependencies
├── QWEN-SANDBOX-ENV.md      # This file
├── .venv/                    # Windows virtual environment (incompatible)
├── .cache/                   # Cache directory for API results and prompts
└── .env                      # Environment variables (API_KEY)
```

## Running the Gmail Script

### First-time Setup (on your local machine with a browser)

```bash
# Windows (with .venv activated)
.venv/Scripts/Activate.ps1
python read_gmail_messages.py
# This will open a browser for OAuth authorization
# After successful auth, token.json will be created
```

### In this Sandbox (headless)

```bash
# System-wide installation (already configured)
cd /d/src/family-automation
python3 read_gmail_messages.py

# Copy token.json from your local machine to this sandbox if needed
```

### Command Line Options

```bash
# Normal run (uses cache if < 12 hours old)
python3 read_gmail_messages.py

# Force refresh from Gmail API
python3 read_gmail_messages.py --force-refresh

# Custom search range
python3 read_gmail_messages.py --days 7 --max-results 20
```

## Prerequisites for Gmail API

1. **Create `.env` file** (optional - API_KEY is not used in current implementation):
   ```
   API_KEY=your_api_key_here
   ```

2. **Download `credentials.json`** from Google Cloud Console:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create/select a project
   - Enable **Gmail API**
   - Go to **APIs & Services → Credentials**
   - Create **OAuth 2.0 Client ID** (Web application)
   - Add `http://localhost:8080` to authorized redirect URIs
   - Download the JSON and save as `credentials.json`

3. **First run requires a browser** for OAuth authorization:
   - Run the script on your local machine (Windows/Mac/Linux with GUI)
   - Complete the OAuth flow in the browser
   - This creates `token.json` for future use
   - Copy `token.json` to use in headless environments (like this sandbox)

## Qwen CLI Integration

The script uses Qwen CLI to summarize emails. Install on Windows:

```powershell
npm install -g @qwen-code/qwen-code
```

The script calls `qwen.cmd` with a short instruction to read the prompt from `.cache/{cache_key}.prompt.txt`.
