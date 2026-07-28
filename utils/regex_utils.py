"""Regex patterns and helper checks."""

import re

# ISO 4217 Currency Code pattern (3 uppercase letters)
CURRENCY_CODE_REGEX = re.compile(r"^[A-Z]{3}$")

# Date pattern YYYY-MM-DD
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_valid_currency_code(code: str) -> bool:
    """Check if the string matches ISO 4217 currency format (e.g., USD, EUR)."""
    if not isinstance(code, str):
        return False
    return bool(CURRENCY_CODE_REGEX.match(code.strip().upper()))


def is_valid_date_format(date_str: str) -> bool:
    """Check if the string matches YYYY-MM-DD format."""
    if not isinstance(date_str, str):
        return False
    return bool(DATE_REGEX.match(date_str.strip()))