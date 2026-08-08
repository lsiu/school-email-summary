# Family Automation - Context Guide

## Project Overview

**Family Automation** (formerly "IMS Gmail Automation") is a Python-based tool that automatically summarizes school emails from International Montessori School (IMS) and Veracross. It uses AI to extract action items for each child based on their class, grade, and school division.

### Key Features
- Reads emails from IMS (`@ims.edu.hk`) and Veracross (`@veracross.com`) domains
- AI-powered summarization using local Ollama (map-reduce pipeline)
- Automatic grade calculation based on reference school year
- Action item extraction with deadline awareness
- Child-specific summaries based on class/grade/division classification
- Caching to minimize API calls (default: 12-hour expiry)

### Tech Stack
- **Language:** Python 3.x
- **Dependencies:** google-auth, google-api-python-client, pyyaml, html2text, pytest
- **AI Integration:** Ollama (local, default model: `llama3.2:1b`)
- **API:** Gmail API (OAuth 2.0)

## Project Structure

```
family-automation/
├── main.py                    # Entry point, CLI argument parsing
├── config.yaml                # User configuration (gitignored)
├── config.yaml.example        # Configuration template
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Pytest configuration
│
├── config/
│   ├── __init__.py           # Package exports
│   ├── settings.py           # Config loading, grade calculation, AI prompt template
│   └── credentials_manager.py # Encrypted credential handling
│
├── services/
│   ├── __init__.py           # Package exports
│   ├── gmail_auth.py         # OAuth authentication (encrypted/standard)
│   ├── gmail_client.py       # Gmail API message fetching
│   └── ollama_summarizer.py  # AI summarization via local Ollama
│
├── utils/
│   ├── __init__.py           # Package exports
│   ├── cache.py              # Timestamped caching with expiry
│   ├── email_cleanup.py      # Email body cleanup for AI
│   └── message_parser.py     # HTML-to-text email parsing
│
└── tests/
    ├── test_school_year.py   # School year calculation tests
    ├── test_grade_calc.py    # Grade calculation tests
    ├── test_division.py      # Division mapping tests
    ├── test_children_info.py # Integration tests
    └── test_email_cleanup.py # Email cleanup tests
```

## Building and Running

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Ollama (for local AI summarization)
# https://ollama.com/download
ollama pull llama3.2:1b
```

### Configuration

```bash
# Copy example config
cp config.yaml.example config.yaml

# Edit config.yaml with family information
```

### Running

```bash
# Basic run (30 days, 50 results per domain)
python main.py

# Force refresh (bypass cache)
python main.py --force-refresh

# Search last 7 days
python main.py --days 7

# Show loaded configuration
python main.py --show-config

# Run tests
pytest

# Run specific test file
pytest tests/test_grade_calc.py
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--force-refresh` | Bypass cache, fetch from Gmail API | `false` |
| `--days` | Days to search back | `30` |
| `--max-results` | Max results per domain | `50` |
| `--show-config` | Display loaded configuration | - |

## Configuration Schema

```yaml
children:
  - name: "Child Name"
    class: "Class Name (e.g., Indus, Bauhinia)"
    reference_school_year: 2025  # School year starts in August
    reference_grade: 5           # Grade during that school year

email:
  sender_domains:
    - "@ims.edu.hk"
    - "@veracross.com"
  cache_expiry_hours: 12

school:
  name: "International Montessori School"
  divisions:
    Lower Elementary: [1, 3]
    Upper Elementary: [4, 6]
    Middle School: [7, 8]

ai:
  enabled: true
  action_item_days: 7
```

## Key Modules

### config/settings.py
- **Purpose:** Configuration loading, grade calculation, AI prompt generation
- **Key Functions:**
  - `load_config()` - Load and validate YAML configuration
  - `calculate_grade(reference_year, reference_grade, date)` - Calculate current grade
  - `get_school_year(date)` - Determine school year (August-June cycle)
  - `get_division(grade)` - Map grade to school division
  - `get_children_info()` - Get children with calculated grades/divisions
  - `get_summarize_prompt()` - Generate AI prompt template

### services/gmail_auth.py
- **Purpose:** OAuth 2.0 authentication
- **Supports:** Encrypted credentials (`credentials.enc`) or standard (`credentials.json`)
- **Key Functions:**
  - `get_gmail_service()` - Authenticate and return Gmail API client

### services/gmail_client.py
- **Purpose:** Gmail API operations
- **Key Functions:**
  - `read_messages(service, days, max_results_per_domain)` - Fetch emails

### services/ollama_summarizer.py
- **Purpose:** AI summarization using local Ollama (map-reduce pipeline)
- **Pipeline:** Extracts facts from each email individually, then merges extractions into the per-child summary format
- **Key Functions:**
  - `summarize_with_ollama(messages, model, base_url)` - Summarize messages with Ollama
  - `_build_extract_prompt(msg, ...)` - Build per-email extraction prompt
  - `_build_merge_prompt(extractions, ...)` - Build merge prompt from extraction blocks
  - `_message_cache_key(msg)` - Generate stable per-message cache key
  - `_extractions_cache_key(messages)` - Generate stable batch cache key
- **Caching:** Per-message extractions and merge results are cached as plain text in `.cache/` to avoid repeated Ollama calls

### utils/cache.py
- **Purpose:** Cache management
- **Storage:** `.cache/` directory with timestamped files
- **Key Functions:**
  - `load_from_cache()` - Load cached messages
  - `save_to_cache(messages)` - Save messages to cache
  - `load_data_from_cache(cache_type, key)` - Load typed data (e.g., extractions, merge) from cache
  - `save_data_to_cache(data, cache_type, key)` - Save typed data to cache as plain text

### utils/email_cleanup.py
- **Purpose:** Email body cleanup for AI
- **Key Functions:**
  - `clean_email_body(body, max_chars)` - Strip HTML artifacts and boilerplate

### utils/message_parser.py
- **Purpose:** Email parsing
- **Key Functions:**
  - `decode_message()` - Decode Gmail message payload
  - `html_to_text()` - Convert HTML email to plain text

## Development Conventions

### Code Style
- **Imports:** Standard library → Third-party → Local (separated by blank lines)
- **Functions:** Docstrings with Args and Returns sections
- **Types:** Type hints for parameters and return values
- **Naming:** `snake_case` for functions/variables, `PascalCase` for classes

### Testing Practices
- **Framework:** pytest
- **Structure:**
  - Test files: `test_*.py`
  - Test classes: `Test*`
  - Test functions: `test_*`
- **Run:** `pytest` (auto-discovers tests in `tests/`)
- **Coverage:** `pytest --cov=config --cov=services --cov=utils`

### Git Workflow
- **Ignored Files:** `config.yaml`, `credentials.json`, `credentials.enc`, `token.json`, `.cache/`, `summary/`
- **Tracked:** `config.yaml.example` (template for users)

## Authentication Setup

### Option A: Encrypted Credentials (Recommended)
1. Obtain `credentials.enc` from administrator
2. Place in project root
3. Run script and enter shared password
4. Token cached in `token.json`

### Option B: Own Google Cloud Project
1. Create project at [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Gmail API
3. Create OAuth 2.0 Client ID credentials
4. Download as `credentials.json`
5. Place in project root

## Output

The script produces:
1. **Console output:** List of emails, AI summary with action items
2. **Summary files:** Markdown files in `summary/` directory (timestamped)
3. **Cache files:** JSON message caches and plain-text extraction/merge caches in `.cache/` directory

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `config.yaml` not found | Copy `config.yaml.example` to `config.yaml` |
| `credentials.json` not found | Provide `credentials.enc` or create `credentials.json` |
| `ModuleNotFoundError: yaml` | `pip install pyyaml` |
| Ollama not running | Start Ollama with `ollama serve` or install from https://ollama.com/download |
| Ollama model not found | `ollama pull llama3.2:1b` |
| Grade calculation wrong | Verify `reference_school_year` and `reference_grade` |

## Notes

- **School Year:** Runs August to June (e.g., "2025" = Aug 2025 - Jun 2026)
- **Grade Calculation:** Automatic based on reference point; increments each August
- **Divisions:** Lower Elementary (1-3), Upper Elementary (4-6), Middle School (7-8)
- **Cache:** Expires after configurable hours (default: 12)
- **AI Summarization:** Local Ollama with map-reduce pipeline; extractions and merge results are cached as plain text