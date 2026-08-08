# Developer Guide

Technical documentation for the IMS Gmail Automation project.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                  │
│                    (Entry Point)                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌─────────────────┐   ┌───────────────┐
│    config/    │    │    services/    │   │    utils/     │
│               │    │                 │   │               │
│  - YAML load  │    │  - Gmail Auth   │   │  - Cache      │
│  - Validation │    │  - Gmail Client │   │  - Parser     │
│  - Calc grade │    │  - Ollama Summ. │   │  - Cleanup    │
└───────────────┘    └─────────────────┘   └───────────────┘
```

## Project Structure

```
ims-gmail-automation/
├── main.py                      # Entry point, CLI parsing
├── config.yaml                  # User configuration (gitignored)
├── config.yaml.example          # Configuration template
├── requirements.txt             # Python dependencies
├── README.md                    # User documentation
├── DEVELOPER.md                 # This file
├── setup-guide.md               # Setup instructions
├── LICENSE                      # MIT License
│
├── config/
│   ├── __init__.py             # Package exports
│   └── settings.py             # Config loading, grade calculation
│
├── services/
│   ├── __init__.py             # Package exports
│   ├── gmail_auth.py           # OAuth authentication
│   ├── gmail_client.py         # Gmail API operations
│   └── ollama_summarizer.py    # AI summarization via local Ollama
│
├── utils/
│   ├── __init__.py             # Package exports
│   ├── cache.py                # Cache management
│   ├── email_cleanup.py        # Email body cleanup for AI
│   └── message_parser.py       # Email decoding (HTML→text)
│
└── tests/
    ├── __init__.py
    ├── test_school_year.py     # School year calculation tests
    ├── test_grade_calc.py      # Grade calculation tests
    ├── test_division.py        # Division mapping tests
    ├── test_children_info.py   # Integration tests
    └── test_email_cleanup.py   # Email cleanup tests
```

## Data Flow

1. **Configuration Loading** (`main.py` → `config/settings.py`)
   - Load `config.yaml`
   - Validate required fields
   - Initialize global configuration

2. **Email Fetching** (`main.py` → `services/gmail_client.py`)
   - Check cache first
   - If cache miss, authenticate with Gmail API
   - Fetch emails from configured domains
   - Cache results

3. **AI Summarization** (`main.py` → `services/ollama_summarizer.py`)
   - Map-reduce pipeline: extract facts from each email, then merge into per-child summary
   - Call local Ollama API
   - Cache per-message extractions and merge results as plain text
   - Return summary

4. **Output** (`main.py`)
   - Display formatted results
   - Show cache status

## Module Details

### config/settings.py

**Purpose:** Configuration loading and grade calculation

**Key Functions:**
- `load_config()` - Load and validate YAML configuration
- `get_children_info()` - Get children with calculated grades
- `get_school_year()` - Determine current school year
- `calculate_grade()` - Calculate grade from reference point
- `get_summarize_prompt()` - Generate AI prompt template

**Configuration Schema:**
```yaml
children:
  - name: string
    class: string
    reference_school_year: int
    reference_grade: int

email:
  sender_domains: [string]
  cache_expiry_hours: int

school:
  name: string
  divisions:
    Division Name: [min_grade, max_grade]

ai:
  enabled: bool
  action_item_days: int
```

### services/gmail_auth.py

**Purpose:** Gmail API OAuth 2.0 authentication

**Key Functions:**
- `get_gmail_service()` - Authenticate and return Gmail API client

**Flow:**
1. Check for existing `token.json`
2. If expired, refresh using refresh token
3. If no token, run OAuth flow (opens browser)
4. Save new token for future use

### services/gmail_client.py

**Purpose:** Gmail API operations

**Key Functions:**
- `read_messages()` - Fetch emails from specified domains

**Parameters:**
- `days` - Number of days to search back
- `max_results_per_domain` - Max emails per domain

### services/ollama_summarizer.py

**Purpose:** AI summarization using local Ollama (map-reduce pipeline)

**Key Functions:**
- `summarize_with_ollama()` - Summarize messages with Ollama
- `_build_extract_prompt()` - Build per-email extraction prompt
- `_build_merge_prompt()` - Build merge prompt from extraction blocks
- `_message_cache_key()` - Generate stable per-message cache key
- `_extractions_cache_key()` - Generate stable batch cache key

**Pipeline:**
1. Extract facts from each email individually (cached per-message)
2. Merge extractions into the per-child summary format (cached per-batch)

**Caching:**
- Per-message extractions and merge results are cached as plain text in `.cache/`
- Cache keys are SHA-256 hashes of message IDs (or content)
- Cache expiry is configurable (default: 12 hours)

**Configuration:**
- Model: `llama3.2:1b` (default)
- Base URL: `http://localhost:11434`
- Timeouts: 120s extract, 360s merge

### utils/cache.py

**Purpose:** Cache management for API results

**Key Functions:**
- `load_from_cache()` - Load cached messages
- `save_to_cache()` - Save messages to cache
- `load_data_from_cache()` - Load typed data (extractions, merge) from cache
- `save_data_to_cache()` - Save typed data to cache as plain text

**Cache Expiry:** Configurable (default: 12 hours)

**Storage:**
- Message caches: JSON files with timestamp in filename
- Extraction/merge caches: Plain text files with timestamp, type, and key in filename

### utils/email_cleanup.py

**Purpose:** Email body cleanup for AI

**Key Functions:**
- `clean_email_body()` - Strip HTML artifacts and boilerplate

### utils/message_parser.py

**Purpose:** Email parsing and HTML-to-text conversion

**Key Functions:**
- `decode_message()` - Decode Gmail message
- `html_to_text()` - Convert HTML to plain text

**Dependencies:** `html2text` library

## Adding Features

### 1. Add New Configuration Option

**Step 1:** Update `config/settings.py` defaults:
```python
DEFAULT_CONFIG = {
    "new_option": "default_value",
    ...
}
```

**Step 2:** Update `config.yaml.example`:
```yaml
# Description
new_option: "value"
```

**Step 3:** Update documentation

### 2. Add New Email Source

**Step 1:** Update `config.yaml.example`:
```yaml
email:
  sender_domains:
    - "@newdomain.com"
```

**Step 2:** No code changes needed - domains are read from config

### 3. Add New AI Provider

**Step 1:** Create `services/new_ai_provider.py`:
```python
def summarize_with_provider(messages, cache_key=None):
    # Implementation
    pass
```

**Step 2:** Update `config/settings.py`:
```python
ai:
  provider: "new_provider"  # Add option
```

**Step 3:** Update `main.py` to route to new provider

## Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_grade_calc.py
```

### Run Specific Test
```bash
pytest tests/test_grade_calc.py::TestCalculateGrade::test_leona_grade_progression
```

### Test Coverage
```bash
pytest --cov=config --cov=services --cov=utils
```

### Test Structure

Tests use `pytest` with the following conventions:
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`
- Parametrized tests: `@pytest.mark.parametrize`

## Code Style

- **Imports:** Standard library → Third-party → Local (with blank lines)
- **Functions:** Docstrings with Args and Returns
- **Types:** Type hints for function parameters and returns
- **Naming:** snake_case for functions/variables, PascalCase for classes

## Debugging

### Enable Debug Output

```bash
# Show configuration
python main.py --show-config

# Force fresh API call
python main.py --force-refresh
```

### Check Cache

```bash
# View cached messages
cat .cache/*.json | python -m json.tool

# View cached extractions/merge results
cat .cache/*_extraction_*.txt
cat .cache/*_merge_*.txt
```

### Common Issues

**Issue:** Configuration not loading
```bash
# Check config file exists
ls -la config.yaml

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

**Issue:** Ollama not running
```bash
# Start Ollama
ollama serve

# Pull the default model
ollama pull llama3.2:1b
```

**Issue:** Grade calculation wrong
```bash
# Test grade calculation
python -c "
from config import calculate_grade, get_school_year
from datetime import datetime

# Test with specific date
grade = calculate_grade(2025, 5, datetime(2026, 9, 15))
print(f'Grade: {grade}')
"
```

## Release Checklist

- [ ] Update version in documentation
- [ ] Run all tests: `pytest`
- [ ] Update `config.yaml.example` if schema changed
- [ ] Update README.md if user-facing changes
- [ ] Update DEVELOPER.md if API changed
- [ ] Test with fresh config (copy example, run)