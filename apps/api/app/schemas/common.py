"""Common validation utilities for Pydantic schemas."""

import re

# Password: min. 8 chars, at least 1 uppercase, 1 lowercase, 1 digit
PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,72}$")


def sanitize_html(value: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", value).strip()
