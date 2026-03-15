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
CHILDREN = {
    "leona": {
        "name": "Leona Siu",
        "class": "Indus",
    },
    "leonidas": {
        "name": "Leonidas Siu",
        "class": "Bauhinia",
    },
}

# Prompt for Qwen CLI to summarize and extract action items
SUMMARIZE_PROMPT = """
You are helping a parent track school-related action items from IMS (International Montessori School) emails.

There are TWO children:
- **Leona Siu** - Class: **Indus**
- **Leonidas Siu** - Class: **Bauhinia**

Use the class names (Indus/Bauhinia) to help classify which emails are for which child.

TODAY'S DATE: {today_date}

Analyze the following email(s) and provide SEPARATE summaries for EACH child:

---

## For LEONA SIU (Class: Indus):

### SUMMARY
Brief overview of emails relevant to Leona (look for "Indus" class references)

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

## For LEONIDAS SIU (Class: Bauhinia):

### SUMMARY
Brief overview of emails relevant to Leonidas (look for "Bauhinia" class references)

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

---
EMAILS:
"""
