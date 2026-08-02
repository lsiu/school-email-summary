"""Tests for email body cleanup."""

from utils.email_cleanup import clean_email_body


def test_clean_email_body_removes_table_separators_and_tracking_urls():
    body = """
| --- |
| **BUS CONFIRMATION** |

Order at https://email.mail2.veracross.com/c/eJxExampleTrackingUrl

Best regards,
IMS Administration Office
---
THE INTERNATIONAL MONTESSORI SCHOOL
+852 2566 7196
"""

    cleaned = clean_email_body(body)

    assert "| --- |" not in cleaned
    assert "veracross.com" not in cleaned
    assert "[link]" in cleaned
    assert "BUS CONFIRMATION" in cleaned
    assert "THE INTERNATIONAL MONTESSORI SCHOOL" not in cleaned


def test_clean_email_body_truncates_long_content():
    body = "Important update. " * 1000

    cleaned = clean_email_body(body, max_chars=100)

    assert cleaned.endswith("[truncated]")
    assert len(cleaned) <= 120
