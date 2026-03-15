# IMS Gmail Automation

Automatically summarize school emails from International Montessori School (IMS) and extract action items for each child.

## What This Does

This tool:
- Reads emails from IMS (`@ims.edu.hk`) and Veracross (`@veracross.com`)
- Uses AI to summarize emails and extract action items
- Separates action items by child based on their class, grade, and school division
- Highlights upcoming events and deadlines
- Caches results to avoid excessive API calls

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Configuration

```bash
# Copy the example config
cp config.yaml.example config.yaml

# Edit with your family's information
# (See Configuration section below)
```

### 3. Set Up Gmail API

**Option A: Using Encrypted Credentials (Recommended)**

1. Contact the administrator to be added as a test user
2. Request for the `credentials.enc` (Ask author for it)
3. Place it in the project folder (same folder as `main.py`)
4. Run the script: `python main.py`
5. Enter the shared password when prompted (Ask author for it)
6. You will only need to enter the password once

**Option B: Using Your Own Google Cloud Project**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Gmail API**
4. Create **OAuth 2.0 Client ID** credentials
5. Download the JSON file as `credentials.json`
6. Place it in the project folder

[Detailed setup guide →](setup-guide.md)

### 4. Run the Script

```bash
python main.py
```

## Configuration

Edit `config.yaml` with your family's information:

```yaml
children:
  - name: "Your Child's Name"
    class: "Their Class (e.g., Indus, Bauhinia)"
    reference_school_year: 2025  # School year starts in August
    reference_grade: 5           # Grade during that school year
```

### How to Set Reference Grade

You only need to enter this **once** - grades are calculated automatically!

1. Pick any school year where you know your child's grade
2. School year starts in August (e.g., "2025" means Aug 2025 - Jun 2026)
3. Enter the grade your child was/will be in that school year

**Example:** If your child is in Grade 3 during the 2025-2026 school year:
```yaml
reference_school_year: 2025
reference_grade: 3
```

The system automatically calculates:
- Current grade (increments each August)
- School division (Lower Elementary, Upper Elementary, Middle School)

### Full Configuration Options

```yaml
# Your children
children:
  - name: "Child Name"
    class: "Class Name"
    reference_school_year: 2025
    reference_grade: 5

# Email settings
email:
  sender_domains:
    - "@ims.edu.hk"
    - "@veracross.com"
  cache_expiry_hours: 12

# School settings
school:
  name: "International Montessori School"
  divisions:
    Lower Elementary: [1, 3]
    Upper Elementary: [4, 6]
    Middle School: [7, 8]

# AI settings
ai:
  enabled: true
  action_item_days: 7
```

## Usage

### Basic Usage

```bash
# Run with default settings (30 days, 50 results per domain)
python main.py
```

### Command Line Options

```bash
# Show help
python main.py --help

# Force refresh (bypass cache)
python main.py --force-refresh

# Search last 7 days only
python main.py --days 7

# Limit results
python main.py --max-results 20

# Show loaded configuration
python main.py --show-config
```

### Output

The script outputs:
1. List of emails found
2. AI-generated summary with:
   - Action items for each child (next 7 days)
   - Upcoming events
   - Other relevant information

## Troubleshooting

### "Configuration file not found"

Copy the example config file:
```bash
cp config.yaml.example config.yaml
```

### "Credentials file not found"

Download `credentials.json` from Google Cloud Console and place it in the project directory.

[See setup guide →](setup-guide.md)

### "Qwen CLI not found"

The AI summarization requires Qwen CLI. Install it:

```bash
# Using npm
npm install -g @qwen-code/qwen-code

# Or skip AI summarization by setting in config.yaml:
ai:
  enabled: false
```

### "ModuleNotFoundError: No module named 'yaml'"

Install the YAML library:
```bash
pip install pyyaml
```

## Project Structure

```
ims-gmail-automation/
├── main.py                 # Main entry point
├── config.yaml             # Your configuration (create from example)
├── config.yaml.example     # Configuration template
├── credentials.json        # Gmail API credentials (you create)
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── DEVELOPER.md            # Technical documentation
├── setup-guide.md          # Detailed setup guide
│
├── config/                 # Configuration module
├── services/               # Gmail API, AI services
├── utils/                  # Utilities (cache, parsing)
├── tests/                  # Test suite
│
└── .cache/                 # Auto-generated cache
```

## For Developers

See [DEVELOPER.md](DEVELOPER.md) for technical documentation, architecture details, and contribution guidelines.

## License

MIT License - see [LICENSE](LICENSE) file.

## Support

For issues or questions:
1. Check the [setup guide](setup-guide.md)
2. Review [DEVELOPER.md](DEVELOPER.md) for technical details
3. Run tests: `pytest`
