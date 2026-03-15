"""
Configuration settings and constants for the Gmail automation script.
"""

from datetime import datetime

# Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Sender domains to filter
SENDER_DOMAINS = ["@ims.edu.hk", "@veracross.com"]

# Cache settings
CACHE_DIR = ".cache"
CACHE_EXPIRY_HOURS = 12

# Children information for email classification
# Grade is calculated automatically based on reference school year and grade
# Enter reference_school_year and reference_grade ONCE - no yearly updates needed
CHILDREN = {
    "leona": {
        "name": "Leona Siu",
        "class": "Indus",
        "reference_school_year": 2025,  # School year starts in August (2025 = Aug 2025 - Jun 2026)
        "reference_grade": 5,            # Grade during 2025-2026 school year
    },
    "leonidas": {
        "name": "Leonidas Siu",
        "class": "Bauhinia",
        "reference_school_year": 2025,  # School year starts in August (2025 = Aug 2025 - Jun 2026)
        "reference_grade": 1,            # Grade during 2025-2026 school year
    },
}

# Grade divisions
GRADE_DIVISIONS = {
    "Lower Elementary": (1, 3),  # Grades 1-3
    "Upper Elementary": (4, 6),  # Grades 4-6
    "Middle School": (7, 8),     # Grades 7-8
}


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
    
    if month >= 8:      # Aug-Dec: school year is year to year+1
        return year
    elif month <= 6:    # Jan-Jun: school year is year-1 to year
        return year - 1
    else:               # July: summer break, use previous school year
        return year - 1


def calculate_grade(reference_school_year: int, reference_grade: int, current_date=None) -> int:
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
    if 1 <= grade <= 3:
        return "Lower Elementary"
    elif 4 <= grade <= 6:
        return "Upper Elementary"
    elif 7 <= grade <= 8:
        return "Middle School"
    else:
        return "Unknown Division"


def get_division_range(division: str) -> str:
    """
    Get the grade range string for a division.

    Args:
        division: Division name ("Lower Elementary", "Upper Elementary", or "Middle School")

    Returns:
        Grade range string (e.g., "Grades 1-3", "Grades 4-6", or "Grades 7-8")
    """
    if division == "Lower Elementary":
        return "Grades 1-3"
    elif division == "Upper Elementary":
        return "Grades 4-6"
    elif division == "Middle School":
        return "Grades 7-8"
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
        grade = calculate_grade(
            child["reference_school_year"],
            child["reference_grade"],
            current_date
        )
        division = get_division(grade)
        current_school_year = get_school_year(current_date)
        
        result[key] = {
            "name": child["name"],
            "class": child["class"],
            "grade": grade,
            "division": division,
            "school_year": f"{current_school_year}-{current_school_year+1}",
        }
    return result

# Prompt for Qwen CLI to summarize and extract action items
# Note: All placeholders are calculated dynamically based on reference school year and grade
SUMMARIZE_PROMPT = """
You are helping a parent track school-related action items from IMS (International Montessori School) emails.

There are TWO children:
- **Leona Siu** - Class: **Indus** - Grade: **{leona_grade}** ({leona_school_year}) - {leona_division} ({leona_division_range})
- **Leonidas Siu** - Class: **Bauhinia** - Grade: **{leonidas_grade}** ({leonidas_school_year}) - {leonidas_division} ({leonidas_division_range})

Use the following to help classify which emails are for which child:
- Class names: Indus = Leona, Bauhinia = Leonidas
- Grade levels: Grade {leona_grade} = Leona, Grade {leonidas_grade} = Leonidas
- School divisions: {leona_division} ({leona_division_range}) = Leona, {leonidas_division} ({leonidas_division_range}) = Leonidas

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
- Use school divisions ({leona_division} = Leona, {leonidas_division} = Leonidas) to classify emails
  - Lower Elementary (Grades 1-3)
  - Upper Elementary (Grades 4-6)
  - Middle School (Grades 7-8)

---
EMAILS:
"""
