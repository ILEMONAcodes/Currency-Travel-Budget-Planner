"""Input validation utilities."""

from datetime import datetime
from models.exceptions import ValidationError
from utils.regex_utils import is_valid_currency_code, is_valid_date_format


def validate_currency_code(code: str) -> str:
    """Validate and sanitize standard 3-letter currency code."""
    if not code or not is_valid_currency_code(code):
        raise ValidationError(
            f"Invalid currency code: '{code}'. Must be 3 uppercase letters (e.g., USD, EUR)."
        )
    return code.strip().upper()


def validate_positive_amount(amount: float, field_name: str = "Amount") -> float:
    """Ensure monetary values are non-negative."""
    if amount is None or amount < 0:
        raise ValidationError(f"{field_name} must be a non-negative number. Got: {amount}")
    return float(amount)


def validate_date_string(date_str: str) -> str:
    """Ensure date matches YYYY-MM-DD and is a valid calendar date."""
    if not is_valid_date_format(date_str):
        raise ValidationError(
            f"Invalid date format: '{date_str}'. Expected format: YYYY-MM-DD"
        )
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValidationError(f"Invalid calendar date: '{date_str}'")
    return date_str