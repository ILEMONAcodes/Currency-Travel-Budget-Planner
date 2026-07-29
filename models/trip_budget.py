"""Trip Budget data models and budget computation engine."""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator, model_validator
from utils.validator import (
    ValidationError,
    validate_currency_code,
    validate_date_string,
    validate_positive_amount,
)


class TripBudget(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    destination_country: str = Field(..., min_length=1)
    destination_country_code: str = Field(
        ..., min_length=2, max_length=2, description="2-letter ISO country code e.g. FR"
    )
    base_currency: str = Field(..., description="Home currency for budget tracking")
    destination_currency: str = Field(..., description="Target country currency")
    total_budget: float = Field(..., description="Total budget in base currency")
    duration_days: int = Field(..., gt=0, description="Trip duration in days")
    start_date: str = Field(..., description="Start date YYYY-MM-DD")
    end_date: str = Field(..., description="End date YYYY-MM-DD")
    notes: Optional[str] = ""

    @field_validator("base_currency", "destination_currency")
    @classmethod
    def check_currency(cls, v: str) -> str:
        return validate_currency_code(v)

    @field_validator("total_budget")
    @classmethod
    def check_budget(cls, v: float) -> float:
        return validate_positive_amount(v, "Total budget")

    @field_validator("start_date", "end_date")
    @classmethod
    def check_dates(cls, v: str) -> str:
        return validate_date_string(v)

    @field_validator("destination_country_code")
    @classmethod
    def check_country_code(cls, v: str) -> str:
        return v.strip().upper()

    @model_validator(mode="after")
    def validate_date_range_and_duration(self) -> "TripBudget":
        """Verify end_date is after start_date and recalculate duration if needed."""
        d_start = datetime.strptime(self.start_date, "%Y-%m-%d")
        d_end = datetime.strptime(self.end_date, "%Y-%m-%d")

        if d_end < d_start:
            raise ValidationError("End date cannot be earlier than start date.")

        calculated_days = (d_end - d_start).days + 1
        if self.duration_days != calculated_days:
            self.duration_days = calculated_days

        return self

    # --- Domain Methods / Calculations ---
    def calculate_daily_budget(self) -> float:
        """Calculate the daily spending allowance in base currency."""
        if self.duration_days <= 0:
            return 0.0
        return round(self.total_budget / self.duration_days, 2)

    def calculate_daily_budget_destination_currency(self, exchange_rate: float) -> float:
        """Calculate the daily spending allowance in the destination currency."""
        daily_base = self.calculate_daily_budget()
        return round(daily_base * exchange_rate, 2)