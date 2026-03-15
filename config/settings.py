"""
Configuration settings and constants for the Gmail automation script.
"""

# Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Sender domains to filter
SENDER_DOMAINS = ["@ims.edu.hk", "@veracross.com"]

# Cache settings
CACHE_DIR = ".cache"
CACHE_EXPIRY_HOURS = 12

# Children information for email classification
# Grade and division are calculated dynamically based on birth year
CHILDREN = {
    "leona": {
        "name": "Leona Siu",
        "class": "Indus",
        "birth_year": 2015,
    },
    "leonidas": {
        "name": "Leonidas Siu",
        "class": "Bauhinia",
        "birth_year": 2019,
    },
}

# Grade divisions
GRADE_DIVISIONS = {
    "Lower Elementary": (1, 3),  # Grades 1-3
    "Upper Elementary": (4, 6),  # Grades 4-6
}


def calculate_grade(birth_year: int, current_date=None) -> int:
    """
    Calculate the grade level based on birth year and current date.
    
    Assumes school year starts in August/September.
    Age 6-7 = Grade 1, Age 7-8 = Grade 2, etc.
    
    Args:
        birth_year: Year the child was born
        current_date: Optional datetime, defaults to today
        
    Returns:
        Grade level (1-6 for elementary)
    """
    from datetime import datetime
    
    if current_date is None:
        current_date = datetime.now()
    
    current_year = current_date.year
    current_month = current_date.month
    
    # School year typically starts in August/September
    # If before August, use previous school year
    school_year_start = current_year - 1 if current_month < 8 else current_year
    
    # Typical age for each grade: Grade 1 = 6-7 years old
    # Calculate age as of school year start
    age_at_school_start = school_year_start - birth_year
    
    # Grade 1 starts at age 6
    grade = age_at_school_start - 5
    
    # Clamp to reasonable elementary range
    return max(1, min(grade, 6))


def get_division(grade: int) -> str:
    """
    Get the elementary division for a given grade.

    Args:
        grade: Grade level (1-6)

    Returns:
        Division name: "Lower Elementary" or "Upper Elementary"
    """
    if 1 <= grade <= 3:
        return "Lower Elementary"
    elif 4 <= grade <= 6:
        return "Upper Elementary"
    else:
        return "Unknown Division"


def get_division_range(division: str) -> str:
    """
    Get the grade range string for a division.

    Args:
        division: Division name ("Lower Elementary" or "Upper Elementary")

    Returns:
        Grade range string (e.g., "Grades 1-3" or "Grades 4-6")
    """
    if division == "Lower Elementary":
        return "Grades 1-3"
    elif division == "Upper Elementary":
        return "Grades 4-6"
    else:
        return "Unknown Grades"


def get_children_info(current_date=None):
    """
    Get children information with dynamically calculated grade and division.
    
    Args:
        current_date: Optional datetime for calculation
        
    Returns:
        Dictionary with children info including calculated grade/division
    """
    result = {}
    for key, child in CHILDREN.items():
        grade = calculate_grade(child["birth_year"], current_date)
        division = get_division(grade)
        result[key] = {
            **child,
            "grade": grade,
            "division": division,
        }
    return result

# Prompt for Qwen CLI to summarize and extract action items
# Note: All placeholders are calculated dynamically based on birth years and today's date
SUMMARIZE_PROMPT = """
You are helping a parent track school-related action items from IMS (International Montessori School) emails.

There are TWO children:
- **Leona Siu** - Class: **Indus** - Grade: **{leona_grade}** - {leona_division} ({leona_division_range}) - Born: **{leona_birth_year}**
- **Leonidas Siu** - Class: **Bauhinia** - Grade: **{leonidas_grade}** - {leonidas_division} ({leonidas_division_range}) - Born: **{leonidas_birth_year}**

Use the following to help classify which emails are for which child:
- Class names: Indus = Leona, Bauhinia = Leonidas
- Grade levels: Grade {leona_grade} = Leona, Grade {leonidas_grade} = Leonidas
- Elementary divisions: {leona_division} ({leona_division_range}) = Leona, {leonidas_division} ({leonidas_division_range}) = Leonidas
- Age-based events: Use birth years ({leona_birth_year}/{leonidas_birth_year}) to determine which child an age-specific event applies to

TODAY'S DATE: {today_date}

Analyze the following email(s) and provide SEPARATE summaries for EACH child:

---

## For LEONA SIU (Class: Indus, Grade {leona_grade}, {leona_division}):

### SUMMARY
Brief overview of emails relevant to Leona (look for "Indus", "Grade {leona_grade}", "{leona_division}" references)

### ACTION ITEMS (Next 7 Days)
List any actions the parent needs to take within the next 7 days for Leona:
- What needs to be done
- Deadline (if specified)
- Any relevant details (links, forms, payments, etc.)
- Mark **URGENT** if deadline is within 48 hours
- Only include action items with deadlines from {today_date} to {seven_days_from_now}

### UPCOMING EVENTS
Events, meetings, or important dates for Leona that are **in the future** (after {today_date}).
Do NOT include events that have already passed.
Include the event date if mentioned.

### OTHER INFO
Any other relevant information for Leona

---

## For LEONIDAS SIU (Class: Bauhinia, Grade {leonidas_grade}, {leonidas_division}):

### SUMMARY
Brief overview of emails relevant to Leonidas (look for "Bauhinia", "Grade {leonidas_grade}", "{leonidas_division}" references)

### ACTION ITEMS (Next 7 Days)
List any actions the parent needs to take within the next 7 days for Leonidas:
- What needs to be done
- Deadline (if specified)
- Any relevant details (links, forms, payments, etc.)
- Mark **URGENT** if deadline is within 48 hours
- Only include action items with deadlines from {today_date} to {seven_days_from_now}

### UPCOMING EVENTS
Events, meetings, or important dates for Leonidas that are **in the future** (after {today_date}).
Do NOT include events that have already passed.
Include the event date if mentioned.

---

## GENERAL (Both Children)
Any information that applies to both children

---

**IMPORTANT:**
- Only include events that are **after {today_date}** in the UPCOMING EVENTS sections
- If an event date has already passed, do NOT list it as "upcoming"
- If there are NO action items in the next 7 days for a child, clearly state "No action items in the next 7 days" for that child
- Use class names (Indus = Leona, Bauhinia = Leonidas) to classify emails even when child names are not mentioned
- Use grade levels to classify emails
- Use elementary divisions ({leona_division} = Leona, {leonidas_division} = Leonidas) to classify emails
- Use birth years ({leona_birth_year} = Leona, {leonidas_birth_year} = Leonidas) to determine age-appropriate events

---
EMAILS:
"""
