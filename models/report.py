"""Reporting and comparison models."""

from typing import Dict, List
from pydantic import BaseModel, Field


class BudgetSummaryReport(BaseModel):
    trip_id: str
    destination_country: str
    total_budget: float
    total_spent: float
    remaining_budget: float
    base_currency: str
    daily_average_spent: float
    category_breakdown: Dict[str, float] = Field(default_factory=dict)
    is_over_budget: bool = False


class CountryCostComparison(BaseModel):
    country_name: str
    country_code: str
    currency_code: str
    estimated_daily_cost_usd: float
    estimated_total_cost_usd: float
    major_cities: List[str] = Field(default_factory=list)