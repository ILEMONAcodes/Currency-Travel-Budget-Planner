"""Country comparison service for comparing travel costs across destinations."""

from typing import Dict, List, Optional
from models.report import CountryCostComparison
from services.currency_converter import CurrencyConverterService


class CountryComparisonService:
    """Service to estimate and compare travel costs between different countries."""

    # Baseline daily travel cost estimates in USD (Tier-based averages)
    # Tier 1 (Budget): ~$30-$60/day
    # Tier 2 (Moderate): ~$70-$130/day
    # Tier 3 (High): ~$150-$300+/day
    COUNTRY_COST_INDEX_USD: Dict[str, Dict[str, str | float | List[str]]] = {
        "FR": {
            "country_name": "France",
            "currency_code": "EUR",
            "estimated_daily_cost_usd": 150.0,
            "major_cities": ["Paris", "Nice", "Lyon", "Marseille"],
        },
        "JP": {
            "country_name": "Japan",
            "currency_code": "JPY",
            "estimated_daily_cost_usd": 120.0,
            "major_cities": ["Tokyo", "Kyoto", "Osaka", "Sapporo"],
        },
        "TH": {
            "country_name": "Thailand",
            "currency_code": "THB",
            "estimated_daily_cost_usd": 45.0,
            "major_cities": ["Bangkok", "Chiang Mai", "Phuket"],
        },
        "US": {
            "country_name": "United States",
            "currency_code": "USD",
            "estimated_daily_cost_usd": 180.0,
            "major_cities": ["New York", "Los Angeles", "Chicago", "Miami"],
        },
        "GB": {
            "country_name": "United Kingdom",
            "currency_code": "GBP",
            "estimated_daily_cost_usd": 160.0,
            "major_cities": ["London", "Edinburgh", "Manchester"],
        },
        "NG": {
            "country_name": "Nigeria",
            "currency_code": "NGN",
            "estimated_daily_cost_usd": 50.0,
            "major_cities": ["Lagos", "Abuja", "Calabar"],
        },
        "KE": {
            "country_name": "Kenya",
            "currency_code": "KES",
            "estimated_daily_cost_usd": 65.0,
            "major_cities": ["Nairobi", "Mombasa", "Kisumu"],
        },
    }

    def __init__(self, currency_service: CurrencyConverterService):
        self.currency_service = currency_service

    def get_country_cost_details(
        self, country_code: str, duration_days: int = 1
    ) -> Optional[CountryCostComparison]:
        """Fetch cost estimates for a single country code."""
        code = country_code.strip().upper()
        if code not in self.COUNTRY_COST_INDEX_USD:
            return None

        data = self.COUNTRY_COST_INDEX_USD[code]
        daily_usd = float(data["estimated_daily_cost_usd"])
        total_usd = daily_usd * duration_days

        return CountryCostComparison(
            country_name=str(data["country_name"]),
            country_code=code,
            currency_code=str(data["currency_code"]),
            estimated_daily_cost_usd=daily_usd,
            estimated_total_cost_usd=round(total_usd, 2),
            major_cities=list(data["major_cities"]),
        )

    def compare_countries(
        self, country_codes: List[str], duration_days: int = 7
    ) -> List[CountryCostComparison]:
        """Compare estimated travel costs across multiple countries for a set duration."""
        comparisons: List[CountryCostComparison] = []

        for code in country_codes:
            details = self.get_country_cost_details(code, duration_days=duration_days)
            if details:
                comparisons.append(details)

        # Sort from lowest to highest estimated total cost
        comparisons.sort(key=lambda x: x.estimated_total_cost_usd)
        return comparisons