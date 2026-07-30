"""Currency data models."""

from pydantic import BaseModel, Field, field_validator
from utils.validator import validate_currency_code, validate_positive_amount


class CurrencyConversionRequest(BaseModel):
    from_currency: str = Field(..., description="Source 3-letter currency code")
    to_currency: str = Field(..., description="Target 3-letter currency code")
    amount: float = Field(..., description="Amount to convert")

    @field_validator("from_currency", "to_currency")
    @classmethod
    def check_currency_code(cls, v: str) -> str:
        return validate_currency_code(v)

    @field_validator("amount")
    @classmethod
    def check_amount(cls, v: float) -> float:
        return validate_positive_amount(v, "Conversion amount")


class CurrencyConversionResult(BaseModel):
    from_currency: str
    to_currency: str
    original_amount: float
    converted_amount: float
    exchange_rate: float
    last_updated: str