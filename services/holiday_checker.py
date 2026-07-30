"""Public Holiday Checker service using Nager.Date API."""

from typing import Dict, List, Optional
import requests
from models.exceptions import APIError


class HolidayCheckerService:
    """Service to fetch and filter public holidays via Nager.Date API."""

    BASE_URL = "https://date.nager.at/api/v3/PublicHolidays"

    def __init__(self):
        self._holiday_cache: Dict[str, List[dict]] = {}

    def fetch_public_holidays(self, year: int, country_code: str) -> List[dict]:
        """Fetch all public holidays for a specific year and 2-letter country code (ISO 3166-1 alpha-2)."""
        code = country_code.strip().upper()
        cache_key = f"{year}_{code}"

        if cache_key in self._holiday_cache:
            return self._holiday_cache[cache_key]

        url = f"{self.BASE_URL}/{year}/{code}"

        try:
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                holidays = response.json()
                self._holiday_cache[cache_key] = holidays
                return holidays
            elif response.status_code == 404:
                # Country code not supported or no holidays found
                return []
            else:
                raise APIError(
                    f"Nager.Date API returned error status {response.status_code} for country '{code}'"
                )

        except requests.exceptions.RequestException as e:
            raise APIError(f"Failed to connect to Nager.Date API: {str(e)}") from e

    def get_holidays_during_trip(
        self, country_code: str, start_date: str, end_date: str
    ) -> List[dict]:
        """Filter holidays that fall strictly within the trip's start_date and end_date (YYYY-MM-DD)."""
        try:
            start_year = int(start_date.split("-")[0])
            end_year = int(end_date.split("-")[0])
        except (ValueError, IndexError) as e:
            raise APIError(f"Invalid date format supplied for holiday check: {str(e)}") from e

        # Gather holidays across all relevant years covered by the trip
        all_holidays = []
        for year in range(start_year, end_year + 1):
            yearly_holidays = self.fetch_public_holidays(year, country_code)
            all_holidays.extend(yearly_holidays)

        # Filter holidays strictly within the range
        trip_holidays = [
            {
                "date": h.get("date"),
                "local_name": h.get("localName"),
                "name": h.get("name"),
                "country_code": h.get("countryCode"),
                "fixed": h.get("fixed"),
                "global": h.get("global"),
            }
            for h in all_holidays
            if start_date <= h.get("date", "") <= end_date
        ]

        return trip_holidays