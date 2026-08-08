# Setup Guide for IMS Parents

Step-by-step instructions to set up the IMS Gmail Automation tool.

## Overview

This tool helps you:
- Automatically read school emails from IMS
- Get summaries of important information
- See action items for each child separately
- Never miss a deadline or event

**Time to set up:** About 15-20 minutes

---

## Step 1: Install Python

### Windows

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. ✅ **Important:** Check "Add Python to PATH" during installation
4. Click "Install Now"

### Verify Installation

Open Command Prompt and type:
```bash
python --version
```

You should see something like `Python 3.11.x` or higher.

---

## Step 2: Download the Project

### Option A: Download as ZIP

1. Click the "Code" button on the project page
2. Click "Download ZIP"
3. Extract the ZIP file to a folder (e.g., `C:\ims-gmail-automation`)

### Option B: Clone with Git

```bash
git clone <repository-url>
cd ims-gmail-automation
```

---

## Step 3: Install Dependencies

Open Command Prompt (Windows) or Terminal (Mac/Linux):

```bash
# Navigate to the project folder
cd path/to/ims-gmail-automation

# Install required packages
pip install -r requirements.txt
```

This installs:
- Gmail API libraries
- Email parsing tools
- Configuration loader
- Testing framework

---

## Step 4: Create Your Configuration

### Copy the Example Config

**Windows (Command Prompt):**
```bash
copy config.yaml.example config.yaml
```

**Mac/Linux:**
```bash
cp config.yaml.example config.yaml
```

### Edit config.yaml

Open `config.yaml` in any text editor (Notepad, TextEdit, VS Code).

#### Update Your Children's Information

Find this section:
```yaml
children:
  - name: "Leona Siu"
    class: "Indus"
    reference_school_year: 2025
    reference_grade: 5

  - name: "Leonidas Siu"
    class: "Bauhinia"
    reference_school_year: 2025
    reference_grade: 1
```

**Update with your children's information:**

- `name`: Your child's full name
- `class`: Their class name (e.g., Indus, Bauhinia, Oak, etc.)
- `reference_school_year`: Pick any school year where you know their grade
- `reference_grade`: Their grade in that school year

**Example for a child in Grade 2 during 2025-2026:**
```yaml
children:
  - name: "Emma Chen"
    class: "Oak"
    reference_school_year: 2025  # Aug 2025 - Jun 2026
    reference_grade: 2           # Grade 2 in that year
```

**Important:** You only enter this **once**! The system automatically calculates their grade each year.

#### Save the File

Save `config.yaml` after editing.

---

## Step 5: Set Up Gmail API Access

You have two options for setting up Gmail API access.

### Option A: Using Encrypted Credentials (Recommended for IMS Parents)

This is the easiest method if you're part of the IMS parent group.

**5A.1 Get Encrypted Credentials**

1. Contact the administrator to be added as a test user
2. You will receive `credentials.enc` (encrypted credentials file)
3. You will receive the password separately (via WhatsApp/email)

**5A.2 Place the File**

1. Place `credentials.enc` in the project folder (same folder as `main.py`)
2. Do NOT rename the file

**5A.3 First Run**

```bash
python main.py
```

When prompted, enter the shared password. You will only need to enter this once - it is saved for future runs.

**Your folder should now have:**
```
ims-gmail-automation/
├── main.py
├── config.yaml          ← You created this
├── credentials.enc      ← Encrypted credentials
├── requirements.txt
└── ...
```

---

### Option B: Using Your Own Google Cloud Project

Use this method if you prefer to set up your own Google Cloud project.

**5B.1 Go to Google Cloud Console**

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Gmail account

**5B.2 Create a New Project**

1. Click the project dropdown at the top
2. Click "NEW PROJECT"
3. Name it something like "IMS Email Automation"
4. Click "CREATE"

**5B.3 Enable Gmail API**

1. In the sidebar, go to **APIs & Services** → **Library**
2. Search for "Gmail API"
3. Click on "Gmail API"
4. Click "ENABLE"

**5B.4 Create OAuth Credentials**

1. Go to **APIs & Services** → **Credentials**
2. Click "+ CREATE CREDENTIALS" → "OAuth client ID"

**If prompted to configure consent screen:**
1. Choose "External" user type
2. Fill in:
   - App name: "IMS Email Automation"
   - User support email: Your email
   - Developer contact: Your email
3. Click "SAVE AND CONTINUE"
4. Skip "Scopes" (click "SAVE AND CONTINUE")
5. Skip "Test users" (click "SAVE AND CONTINUE")
6. Click "BACK TO DASHBOARD"

**Create OAuth Client ID:**
1. Application type: "Desktop app"
2. Name: "IMS Automation"
3. Click "CREATE"

**5B.5 Download Credentials**

1. Click the download icon (⬇️) next to your new credentials
2. Save the file as `credentials.json`
3. Place it in the project folder (same folder as `main.py`)

**Your folder should now have:**
```
ims-gmail-automation/
├── main.py
├── config.yaml          ← You created this
├── credentials.json     ← You just downloaded this
├── requirements.txt
└── ...
```

---

## Step 6: First Run (Authorize Access)

### If Using Encrypted Credentials (Option A)

**Run the Script:**

```bash
python main.py
```

**Enter Password:**

When prompted, enter the shared password. You will only need to enter this once.

**Authorize Google Access:**

1. A browser window will open
2. Sign in to your Google account
3. You'll see a warning: "This app isn't verified"
   - This is normal for personal projects
   - Click "Advanced" → "Go to (unsafe)"
4. Click "Allow" to grant Gmail access
5. The browser will show "Authentication successful"
6. Return to the terminal - the script will continue

**What Happens Next:**

- The script creates a `token.json` file (saved authorization)
- Future runs won't need browser authorization or password
- Emails are fetched and summarized

---

### If Using Your Own Google Cloud Project (Option B)

**Run the Script:**

```bash
python main.py
```

**Authorize Google Access:**

1. A browser window will open
2. Sign in to your Google account
3. You'll see a warning: "This app isn't verified"
   - This is normal for personal projects
   - Click "Advanced" → "Go to (unsafe)"
4. Click "Allow" to grant Gmail access
5. The browser will show "Authentication successful"
6. Return to the terminal - the script will continue

**What Happens Next:**

- The script creates a `token.json` file (saved authorization)
- Future runs won't need browser authorization
- Emails are fetched and summarized

---

## Step 7: (Optional) Install Ollama for AI Summaries

The tool can use local Ollama AI to summarize emails. This is optional.

### Install Ollama

1. Download and install from [ollama.com/download](https://ollama.com/download)

### Pull the Default Model

```bash
ollama pull llama3.2:1b
```

### Start Ollama (If Not Running)

```bash
ollama serve
```

### Disable AI (If Not Using)

If you don't want AI summaries, edit `config.yaml`:
```yaml
ai:
  enabled: false
```

---

## Step 8: Regular Usage

### Run the Script

```bash
python main.py
```

### Useful Commands

```bash
# Show help
python main.py --help

# Force refresh (get fresh emails)
python main.py --force-refresh

# Show your configuration
python main.py --show-config

# Search last 7 days only
python main.py --days 7
```

---

## Troubleshooting

### "Configuration file not found"

**Solution:**
```bash
copy config.yaml.example config.yaml
```

Then edit `config.yaml` with your information.

### "Credentials file not found"

**Solution:** Download `credentials.json` from Google Cloud Console (Step 5).

### "ModuleNotFoundError: No module named 'yaml'"

**Solution:**
```bash
pip install pyyaml
```

### "Ollama not running"

**Solution:** Either:
1. Install Ollama from [ollama.com/download](https://ollama.com/download) and run `ollama serve`
2. Pull the model: `ollama pull llama3.2:1b`
3. Or disable AI in `config.yaml`: `ai.enabled: false`

### Browser Doesn't Open for Authorization

**Solution:**
1. Copy the URL shown in the terminal
2. Paste it in your browser manually
3. Complete authorization
4. Return to terminal

### Emails Not Showing Up

**Check:**
1. Are emails from `@ims.edu.hk` or `@veracross.com`?
2. Try `--force-refresh` to get fresh data
3. Check `--days` parameter (default is 30 days)

---

## Next Steps

- **Understand the output:** See [README.md](README.md)
- **Customize settings:** Edit `config.yaml`
- **Technical details:** See [DEVELOPER.md](DEVELOPER.md)

---

## Getting Help

1. Check this guide first
2. Review [README.md](README.md) for general usage
3. Check [DEVELOPER.md](DEVELOPER.md) for technical issues
4. Run tests: `pytest`
