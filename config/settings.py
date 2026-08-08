"""
Configuration settings and constants for the Gmail automation script.

Loads user configuration from config.yaml file.
Functions for grade calculation and school year determination.
"""

import os
from datetime import datetime
from typing import Any, Dict, List

try:
    import yaml
except ImportError:
    yaml = None  # Will raise error if YAML is needed but not installed


# =============================================================================
# Default Configuration
# =============================================================================

# Gmail API scopes (constant - doesn't change)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Cache directory (constant)
CACHE_DIR = ".cache"

DEFAULT_CONFIG = {
    "children": [],
    "email": {
        "sender_domains": ["@ims.edu.hk", "@veracross.com"],
        "cache_expiry_hours": 12,
    },
    "school": {
        "name": "International Montessori School",
        "divisions": {
            "Lower Elementary": [1, 3],
            "Upper Elementary": [4, 6],
            "Middle School": [7, 8],
        },
    },
    "ai": {
        "enabled": True,
        "action_item_days": 7,
    },
}

# =============================================================================
# Module-level Configuration (loaded from YAML)
# =============================================================================

_config: Dict[str, Any] = None
CHILDREN: Dict[str, Dict[str, Any]] = {}
SENDER_DOMAINS: List[str] = []
CACHE_EXPIRY_HOURS: int = 12
GRADE_DIVISIONS: Dict[str, tuple] = {}


# =============================================================================
# Configuration Getters (use these to get current values)
# =============================================================================


def get_sender_domains() -> List[str]:
    """Get sender domains from loaded config."""
    if _config is None:
        load_config()
    return SENDER_DOMAINS


def get_cache_expiry_hours() -> int:
    """Get cache expiry hours from loaded config."""
    if _config is None:
        load_config()
    return CACHE_EXPIRY_HOURS


# =============================================================================
# Configuration Loading
# =============================================================================


def load_config(config_path: str | None = None) -> Dict[str, Any]:
    """
    Load configuration from config.yaml file.

    Args:
        config_path: Optional path to config file. Defaults to 'config.yaml' in script directory.

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        ImportError: If pyyaml is not installed
    """
    global _config, CHILDREN, SENDER_DOMAINS, CACHE_EXPIRY_HOURS, GRADE_DIVISIONS

    if yaml is None:
        raise ImportError("pyyaml is required. Install with: pip install pyyaml")

    if config_path is None:
        # Look for config.yaml in the script's directory
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(script_dir, "config.yaml")

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Copy 'config.yaml.example' to 'config.yaml' and edit with your family's information."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        user_config = yaml.safe_load(f)

    # Merge with defaults
    _config = {**DEFAULT_CONFIG, **user_config}

    # Extract and validate configuration
    _extract_config()

    return _config


def _extract_config():
    """Extract global configuration values from loaded config."""
    global CHILDREN, SENDER_DOMAINS, CACHE_EXPIRY_HOURS, GRADE_DIVISIONS

    # Convert children list to dictionary keyed by lowercase first name
    CHILDREN = {}
    for child in _config.get("children", []):
        key = child["name"].split()[0].lower()
        CHILDREN[key] = {
            "name": child["name"],
            "class": child.get("class", ""),
            "reference_school_year": child["reference_school_year"],
            "reference_grade": child["reference_grade"],
        }

    # Email settings
    email_config = _config.get("email", {})
    SENDER_DOMAINS = email_config.get(
        "sender_domains", DEFAULT_CONFIG["email"]["sender_domains"]
    )
    CACHE_EXPIRY_HOURS = email_config.get(
        "cache_expiry_hours", DEFAULT_CONFIG["email"]["cache_expiry_hours"]
    )

    # School settings
    school_config = _config.get("school", {})
    divisions = school_config.get("divisions", DEFAULT_CONFIG["school"]["divisions"])
    GRADE_DIVISIONS = {name: tuple(range_val) for name, range_val in divisions.items()}


def get_config() -> Dict[str, Any]:
    """Get the loaded configuration dictionary."""
    if _config is None:
        load_config()
    return _config


def is_config_loaded() -> bool:
    """Check if configuration has been loaded."""
    return _config is not None


# =============================================================================
# Grade Calculation Functions
# =============================================================================


def get_school_year(current_date=None) -> int:
    """
    Get the school year for a given date.
    School year runs August to June.

    Args:
        current_date: Optional datetime, defaults to today

    Returns:
        int: The start year of the school year (e.g., 2025 for "2025-2026")
    """
    if current_date is None:
        current_date = datetime.now()

    year = current_date.year
    month = current_date.month

    if month >= 8:  # Aug-Dec: school year is year to year+1
        return year
    elif month <= 6:  # Jan-Jun: school year is year-1 to year
        return year - 1
    else:  # July: summer break, use previous school year
        return year - 1


def calculate_grade(
    reference_school_year: int, reference_grade: int, current_date=None
) -> int:
    """
    Calculate the grade level based on reference school year and grade.
    Grade increases by 1 for each school year that passes.

    Args:
        reference_school_year: The school year start (e.g., 2025 for 2025-2026)
        reference_grade: The grade during the reference school year
        current_date: Optional datetime, defaults to today

    Returns:
        Grade level (1-12)
    """
    if current_date is None:
        current_date = datetime.now()

    current_school_year = get_school_year(current_date)

    # Grade changes by +1 for each school year
    years_passed = current_school_year - reference_school_year
    grade = reference_grade + years_passed

    # Clamp to reasonable K-12 range
    return max(1, min(grade, 12))


def get_division(grade: int) -> str:
    """
    Get the elementary division for a given grade.

    Args:
        grade: Grade level (1-12)

    Returns:
        Division name: "Lower Elementary", "Upper Elementary", or "Middle School"
    """
    if _config is None:
        load_config()
    for division_name, (min_grade, max_grade) in GRADE_DIVISIONS.items():
        if min_grade <= grade <= max_grade:
            return division_name
    return "Unknown Division"


def get_division_range(division: str) -> str:
    """
    Get the grade range string for a division.

    Args:
        division: Division name

    Returns:
        Grade range string (e.g., "Grades 1-3")
    """
    if division not in GRADE_DIVISIONS:
        return "Unknown Grades"

    min_grade, max_grade = GRADE_DIVISIONS[division]
    return f"Grades {min_grade}-{max_grade}"


def get_children_info(current_date=None) -> Dict[str, Dict[str, Any]]:
    """
    Get children information with dynamically calculated grade and division.

    Args:
        current_date: Optional datetime for calculation

    Returns:
        Dictionary with children info including calculated grade/division
    """
    if not is_config_loaded():
        load_config()

    result = {}
    for key, child in CHILDREN.items():
        grade = calculate_grade(
            child["reference_school_year"], child["reference_grade"], current_date
        )
        division = get_division(grade)
        current_school_year = get_school_year(current_date)

        result[key] = {
            "name": child["name"],
            "class": child["class"],
            "grade": grade,
            "division": division,
            "school_year": f"{current_school_year}-{current_school_year + 1}",
        }
    return result


# =============================================================================
# AI Prompt Template
# =============================================================================


def get_summarize_prompt() -> str:
    """
    Get the AI summary prompt template with current children information.

    Returns:
        Formatted prompt string
    """
    if not is_config_loaded():
        load_config()

    children_info = get_children_info()

    # Build child-specific sections
    child_sections = []
    child_vars = {}

    for key, child in children_info.items():
        name = child["name"]
        grade = child["grade"]
        school_year = child["school_year"]
        division = child["division"]
        division_range = get_division_range(division)
        class_name = child["class"]

        # Store variables for template
        child_vars[f"{key}_grade"] = grade
        child_vars[f"{key}_school_year"] = school_year
        child_vars[f"{key}_division"] = division
        child_vars[f"{key}_division_range"] = division_range
        child_vars[f"{key}_class"] = class_name
        child_vars[f"{key}_name"] = name

        # Build section
        section = f"""
## For {name.upper()} (Class: {class_name}, Grade {grade}, {division}):

### SUMMARY
Brief overview of emails relevant to {name.split()[0]} (look for "{class_name}", "Grade {grade}", "{division}" references)

### ACTION ITEMS (Next 7 Days)
List any actions the parent needs to take within the next 7 days for {name.split()[0]}:
- What needs to be done
- Deadline (if specified)
- Any relevant details (links, forms, payments, etc.)
- Mark **URGENT** if deadline is within 48 hours
- Only include action items with deadlines from {{today_date}} to {{seven_days_from_now}}

### UPCOMING EVENTS
Events, meetings, or important dates for {name.split()[0]} that are **in the future** (after {{today_date}}).
Do NOT include events that have already passed.
Include the event date if mentioned.

### OTHER INFO
Any other relevant information for {name.split()[0]}

---
"""
        child_sections.append(section)

    # Build classification hints
    classification_hints = []
    for key, child in children_info.items():
        name = child["name"].split()[0]
        classification_hints.append(f"- {child['class']} = {name}")

    for key, child in children_info.items():
        name = child["name"].split()[0]
        classification_hints.append(f"- Grade {child['grade']} = {name}")

    for key, child in children_info.items():
        name = child["name"].split()[0]
        classification_hints.append(f"- {child['division']} = {name}")

    prompt = f"""
You are helping a parent track school-related action items from IMS (International Montessori School) emails.

There are {len(children_info)} children:
"""

    for key, child in children_info.items():
        prompt += f"- **{child['name']}** - Class: **{child['class']}** - Grade: **{child['grade']}** ({child['school_year']}) - {child['division']} ({get_division_range(child['division'])})\n"

    prompt += f"""

Use the following to help classify which emails are for which child:
- Class names: {", ".join(classification_hints)}

TODAY'S DATE: {{today_date}}

Analyze the following email(s) and provide SEPARATE summaries for EACH child:

---
{"".join(child_sections)}
## GENERAL (All Children)
Any information that applies to all children

---

**IMPORTANT:**
- Only include events that are **after {{today_date}}** in the UPCOMING EVENTS sections
- If an event date has already passed, do NOT list it as "upcoming"
- If there are NO action items in the next 7 days for a child, clearly state "No action items in the next 7 days" for that child
- Use class names, grade levels, and school divisions to classify emails even when child names are not mentioned

---
EMAILS:
"""

    return prompt


# Initialize SUMMARIZE_PROMPT as a function for lazy loading
def _get_summarize_prompt_template():
    """Internal function to get prompt template."""
    return get_summarize_prompt()
