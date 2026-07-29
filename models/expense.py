"""Expense data models."""

from uuid import uuid4
from pydantic import BaseModel, Field, field_validator
from utils.validator import validate_currency_code, validate_positive_amount, validate_date_string


class Expense(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    trip_id: str = Field(..., description="Associated Trip ID")
    category: str = Field(..., min_length=1, description="Expense category (Food, Lodging, Transport, etc.)")
    amount: float = Field(..., description="Amount spent in local/original currency")
    currency: str = Field(..., description="Currency code of the expense")
    amount_in_base_currency: float = Field(0.0, description="Amount converted to trip base currency")
    date: str = Field(..., description="Date of expense in YYYY-MM-DD format")
    description: str = Field("", description="Optional details")

    @field_validator("currency")
    @classmethod
    def check_currency(cls, v: str) -> str:
        return validate_currency_code(v)

    @field_validator("amount", "amount_in_base_currency")
    @classmethod
    def check_amount(cls, v: float) -> float:
        return validate_positive_amount(v)

    @field_validator("date")
    @classmethod
    def check_date(cls, v: str) -> str:
        return validate_date_string(v)