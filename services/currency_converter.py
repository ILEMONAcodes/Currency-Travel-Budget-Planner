"""Currency Converter service using ExchangeRate API with enhanced cache normalization."""
import os
from typing import Dict, Optional
import requests

from models.currency import CurrencyConversionRequest, CurrencyConversionResult
from models.exceptions import APIError, CurrencyNotFoundError
from utils.validator import validate_currency_code
class CurrencyConverterService:
    """Service to handle real-time and cached exchange rates via ExchangeRate API."""

    BASE_URL = "https://v6.exchangerate-api.com/v6"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("EXCHANGE_RATE_API_KEY", "")
        self._rate_cache: Dict[str, Dict[str, float]] = {}

    def fetch_exchange_rates(self, base_currency: str) -> Dict[str, float]:
        """Fetch real-time conversion rates for a given base currency.

        Caches results per normalized base currency during session runtime.
        """
        base_currency = validate_currency_code(base_currency).upper()

        # Return cached rates if available
        if base_currency in self._rate_cache:
            return self._rate_cache[base_currency]

        if not self.api_key:
            # Fallback mock rate mode if no API key is set (useful for local dev/testing)
            return self._get_fallback_rates(base_currency)

        url = f"{self.BASE_URL}/{self.api_key}/latest/{base_currency}"

        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            if response.status_code != 200 or data.get("result") != "success":
                error_type = data.get("error-type", "unknown-error")
                if error_type == "unsupported-code":
                    raise CurrencyNotFoundError(f"Currency code '{base_currency}' is not supported.")
                raise APIError(f"ExchangeRate API error: {error_type}")

            rates = data.get("conversion_rates", {})
            
            # Normalize rate dictionary keys to uppercase for resilient lookups
            normalized_rates = {k.upper(): float(v) for k, v in rates.items()}
            self._rate_cache[base_currency] = normalized_rates
            return normalized_rates

        except requests.exceptions.RequestException as e:
            raise APIError(f"Failed to connect to ExchangeRate API: {str(e)}") from e

    def convert(self, request: CurrencyConversionRequest) -> CurrencyConversionResult:
        """Convert a specific monetary amount from one currency to another with short-circuit optimizations."""
        from_curr = validate_currency_code(request.from_currency).upper()
        to_curr = validate_currency_code(request.to_currency).upper()

        # Same-currency short-circuit guard (prevents unnecessary API network requests)
        if from_curr == to_curr:
            return CurrencyConversionResult(
                from_currency=from_curr,
                to_currency=to_curr,
                original_amount=request.amount,
                converted_amount=round(request.amount, 2),
                exchange_rate=1.0,
                last_updated="Instant (1:1 Same Currency)",
            )

        rates = self.fetch_exchange_rates(from_curr)

        if to_curr not in rates:
            raise CurrencyNotFoundError(f"Target currency '{to_curr}' not found in exchange rate table.")

        rate = rates[to_curr]
        converted_amount = round(request.amount * rate, 2)

        return CurrencyConversionResult(
            from_currency=from_curr,
            to_currency=to_curr,
            original_amount=request.amount,
            converted_amount=converted_amount,
            exchange_rate=rate,
            last_updated="Live/Cached API Rate",
        )

    def _get_fallback_rates(self, base_currency: str) -> Dict[str, float]:
        """Provide basic default conversion ratios if API key is unconfigured."""
        mock_database = {
            "USD": {"USD": 1.0, "EUR": 0.92, "GBP": 0.78, "NGN": 1500.0, "JPY": 155.0, "CAD": 1.36},
            "EUR": {"EUR": 1.0, "USD": 1.09, "GBP": 0.85, "NGN": 1630.0, "JPY": 168.0, "CAD": 1.48},
            "GBP": {"GBP": 1.0, "USD": 1.28, "EUR": 1.18, "NGN": 1920.0, "JPY": 198.0, "CAD": 1.74},
            "NGN": {"NGN": 1.0, "USD": 0.00067, "EUR": 0.00061, "GBP": 0.00052, "JPY": 0.10, "CAD": 0.00091},
        }
        return mock_database.get(base_currency, {base_currency: 1.0, "USD": 1.0})