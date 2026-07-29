"""
CURRENCY AND TRAVEL BUDGET PLANNER
----------------------------------
An intermediate-level Python project demonstrating:
- File handling (JSON / CSV)
- Exception handling (custom exceptions)
- Regular expressions (validation & extraction)
- Object-Oriented Programming (classes & composition)

Run:
    python travel_budget_planner.py
"""

import json
import csv
import os
import re
from datetime import datetime, date

# CUSTOM EXCEPTIONS

class InvalidCurrencyError(Exception):
    """Raised when a currency code fails validation."""
    pass

class InvalidAmountError(Exception):
    """Raised when a numeric amount cannot be parsed or is out of range."""
    pass

class ConversionError(Exception):
    """Raised when a currency conversion cannot be completed."""
    pass

# CURRENCY CONVERTER

class CurrencyConverter:
    """
    Handles currency code validation and conversion between currencies.

    Rates are stored as 'units of currency per 1 USD' for simplicity.
    Replace EXCHANGE_RATES with a live API call later without changing
    the public interface (validate_code / convert).
    """

    CODE_PATTERN = re.compile(r"^[A-Z]{3}$")

    # Static mock rates: 1 USD = X units of currency
    EXCHANGE_RATES = {
        "USD": 1.0,
        "NGN": 1550.00,
        "GBP": 0.77,
        "EUR": 0.91,
        "JPY": 149.50,
        "CAD": 1.36,
        "ZAR": 17.80,
        "GHS": 15.20,
        "KES": 129.00,
        "AED": 3.67,
    }

    @classmethod
    def validate_code(cls, code: str) -> str:
        """Validate a 3-letter currency code using regex. Returns the
        normalized (uppercase) code or raises InvalidCurrencyError."""
        if not isinstance(code, str):
            raise InvalidCurrencyError(f"Currency code must be text, got {type(code).__name__}")

        code = code.strip().upper()
        if not cls.CODE_PATTERN.match(code):
            raise InvalidCurrencyError(
                f"'{code}' is not a valid currency code (expected 3 letters, e.g. USD, NGN, GBP)."
            )
        if code not in cls.EXCHANGE_RATES:
            raise InvalidCurrencyError(f"No exchange rate data available for '{code}'.")
        return code

    @staticmethod
    def extract_amount(text: str) -> float:
        """Extract a numeric value from a free-form string, e.g. 'about $500.50'."""
        match = re.search(r"[-+]?\d[\d,]*\.?\d*", text)
        if not match:
            raise InvalidAmountError(f"Could not find a numeric amount in '{text}'.")
        cleaned = match.group().replace(",", "")
        try:
            value = float(cleaned)
        except ValueError:
            raise InvalidAmountError(f"'{cleaned}' is not a valid number.")
        if value <= 0:
            raise InvalidAmountError("Amount must be greater than zero.")
        return value

    @classmethod
    def convert(cls, amount: float, from_code: str, to_code: str) -> float:
        """Convert an amount from one currency to another."""
        from_code = cls.validate_code(from_code)
        to_code = cls.validate_code(to_code)

        if amount <= 0:
            raise InvalidAmountError("Amount to convert must be greater than zero.")

        try:
            usd_value = amount / cls.EXCHANGE_RATES[from_code]
            converted = usd_value * cls.EXCHANGE_RATES[to_code]
        except (KeyError, ZeroDivisionError) as e:
            raise ConversionError(f"Failed to convert {from_code} to {to_code}: {e}")

        return round(converted, 2)


PUBLIC_HOLIDAYS = {
    "NG": {"2026-10-01": "Independence Day", "2026-12-25": "Christmas Day"},
    "US": {"2026-07-04": "Independence Day", "2026-11-26": "Thanksgiving"},
    "GB": {"2026-12-25": "Christmas Day", "2026-12-26": "Boxing Day"},
    "JP": {"2026-11-03": "Culture Day", "2026-01-01": "New Year's Day"},
    "FR": {"2026-07-14": "Bastille Day", "2026-12-25": "Noel"},
}

CURRENCY_TO_COUNTRY = {
    "USD": "US", "NGN": "NG", "GBP": "GB", "EUR": "FR",
    "JPY": "JP", "CAD": "US", "ZAR": "NG", "GHS": "NG",
    "KES": "NG", "AED": "US",
}


def check_public_holidays(country_code: str, start_date: date, end_date: date) -> list:
    """Return a list of (date, name) tuples for holidays falling within the trip."""
    holidays = PUBLIC_HOLIDAYS.get(country_code, {})
    hits = []
    for date_str, name in holidays.items():
        h_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if start_date <= h_date <= end_date:
            hits.append((h_date, name))
    return sorted(hits)
# AI ADVISOR
class AIAdvisor:
    """
    Generates travel budget advice. Attempts a real Anthropic API call if
    ANTHROPIC_API_KEY is set in the environment; otherwise falls back to a
    rule-based tip generator so the program always works offline.
    """

    @staticmethod
    def generate_advice(destination: str, daily_limit: float, currency: str, days: int) -> str:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            try:
                return AIAdvisor._call_anthropic_api(api_key, destination, daily_limit, currency, days)
            except Exception:
                # Fall through to rule-based advice on any API failure
                pass
        return AIAdvisor._rule_based_advice(destination, daily_limit, currency, days)

    @staticmethod
    def _call_anthropic_api(api_key, destination, daily_limit, currency, days):
        import urllib.request

        prompt = (
            f"Give concise, practical travel budget advice (3-4 bullet points) for a trip to "
            f"{destination} lasting {days} days, with a daily budget of {daily_limit} {currency}."
        )
        payload = json.dumps({
            "model": "claude-sonnet-4-6",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        return "".join(block.get("text", "") for block in data.get("content", []))

    @staticmethod
    def _rule_based_advice(destination, daily_limit, currency, days):
        tips = [f"Trip to {destination}: {days} day(s), daily budget ~{daily_limit} {currency}."]
        if daily_limit < 20:
            tips.append("Your daily budget is quite tight — consider hostels, cooking your own meals, "
                         "and free walking tours to stretch your funds.")
        elif daily_limit < 60:
            tips.append("You have a moderate daily budget — mix budget accommodation with occasional "
                         "splurges on food or activities.")
        else:
            tips.append("You have a comfortable daily budget — you can enjoy hotels, dining out, and "
                         "guided experiences without much worry.")
        tips.append("Set aside 10-15% of your total budget as an emergency buffer.")
        tips.append("Track expenses daily so small purchases don't add up unnoticed.")
        return "\n- ".join(tips)

# TRIP BUDGET

class TripBudget:
    """Represents a single trip's budget: currencies, amount, duration, and
    derived figures (daily limit, total estimate, holiday warnings)."""

    def __init__(self, destination: str, home_currency: str, dest_currency: str,
                 amount: float, days: int, buffer_percent: float = 10.0):
        self.destination = destination
        self.home_currency = CurrencyConverter.validate_code(home_currency)
        self.dest_currency = CurrencyConverter.validate_code(dest_currency)

        if days <= 0:
            raise InvalidAmountError("Trip duration must be at least 1 day.")
        if amount <= 0:
            raise InvalidAmountError("Budget amount must be greater than zero.")

        self.amount = amount
        self.days = days
        self.buffer_percent = buffer_percent

        self.converted_amount = CurrencyConverter.convert(amount, home_currency, dest_currency)
        self.daily_limit = round(self.converted_amount / days, 2)
        self.total_with_buffer = round(self.converted_amount * (1 + buffer_percent / 100), 2)

    def holiday_warnings(self, start_date: date, end_date: date) -> list:
        country_code = CURRENCY_TO_COUNTRY.get(self.dest_currency)
        if not country_code:
            return []
        return check_public_holidays(country_code, start_date, end_date)

    def to_dict(self) -> dict:
        return {
            "destination": self.destination,
            "home_currency": self.home_currency,
            "dest_currency": self.dest_currency,
            "amount": self.amount,
            "days": self.days,
            "converted_amount": self.converted_amount,
            "daily_limit": self.daily_limit,
            "total_with_buffer": self.total_with_buffer,
        }

    def __str__(self):
        return (f"Trip to {self.destination}: {self.amount} {self.home_currency} "
                f"-> {self.converted_amount} {self.dest_currency} over {self.days} day(s) "
                f"(daily limit: {self.daily_limit} {self.dest_currency})")

# EXPENSE & TRACKER

class Expense:
    """A single recorded expense."""

    def __init__(self, category: str, amount: float, currency: str,
                 note: str = "", expense_date: str = None):
        self.category = category
        self.amount = amount
        self.currency = CurrencyConverter.validate_code(currency)
        self.note = note
        self.expense_date = expense_date or date.today().isoformat()

        if amount <= 0:
            raise InvalidAmountError("Expense amount must be greater than zero.")

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "amount": self.amount,
            "currency": self.currency,
            "note": self.note,
            "date": self.expense_date,
        }


class ExpenseTracker:
    """Holds a list of Expense objects for a trip and computes totals."""

    def __init__(self, budget: TripBudget):
        self.budget = budget
        self.expenses = []

    def add_expense(self, expense: Expense):
        self.expenses.append(expense)

    def total_spent(self) -> float:
        # Convert every expense into the destination currency before summing
        total = 0.0
        for e in self.expenses:
            try:
                total += CurrencyConverter.convert(e.amount, e.currency, self.budget.dest_currency)
            except ConversionError:
                continue
        return round(total, 2)

    def remaining_budget(self) -> float:
        return round(self.budget.converted_amount - self.total_spent(), 2)

    def is_overspent(self) -> bool:
        return self.total_spent() > self.budget.converted_amount

    def summary(self) -> str:
        spent = self.total_spent()
        remaining = self.remaining_budget()
        status = "OVER BUDGET" if self.is_overspent() else "within budget"
        return (f"Spent: {spent} {self.budget.dest_currency} | "
                f"Remaining: {remaining} {self.budget.dest_currency} | Status: {status}")

# BUDGET REPORT (file handling / export)

class BudgetReport:
    """Generates summaries and exports trip/expense data to JSON or CSV."""

    def __init__(self, tracker: ExpenseTracker):
        self.tracker = tracker

    def generate_summary(self) -> str:
        budget = self.tracker.budget
        advice = AIAdvisor.generate_advice(
            budget.destination, budget.daily_limit, budget.dest_currency, budget.days
        )
        lines = [
            "=" * 50,
            f"TRAVEL BUDGET REPORT: {budget.destination}",
            "=" * 50,
            str(budget),
            self.tracker.summary(),
            "-" * 50,
            "AI Travel Advice:",
            f"- {advice}",
        ]
        return "\n".join(lines)

    def export_json(self, filepath: str):
        data = {
            "budget": self.tracker.budget.to_dict(),
            "expenses": [e.to_dict() for e in self.tracker.expenses],
        }
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            raise OSError(f"Could not write JSON file: {e}")

    def export_csv(self, filepath: str):
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["category", "amount", "currency", "note", "date"])
                for e in self.tracker.expenses:
                    d = e.to_dict()
                    writer.writerow([d["category"], d["amount"], d["currency"], d["note"], d["date"]])
        except OSError as e:
            raise OSError(f"Could not write CSV file: {e}")

# COMPARISON HELPER

def compare_destinations(dest_a: TripBudget, dest_b: TripBudget) -> str:
    """Compare two TripBudget objects and report which is cheaper (in USD terms)."""
    usd_a = CurrencyConverter.convert(dest_a.converted_amount, dest_a.dest_currency, "USD")
    usd_b = CurrencyConverter.convert(dest_b.converted_amount, dest_b.dest_currency, "USD")

    cheaper = dest_a if usd_a < usd_b else dest_b
    diff = round(abs(usd_a - usd_b), 2)

    return (
        f"{dest_a.destination}: ~{usd_a} USD total\n"
        f"{dest_b.destination}: ~{usd_b} USD total\n"
        f"=> {cheaper.destination} is cheaper by approximately {diff} USD."
    )

# CLI

def prompt_float(message: str) -> float:
    while True:
        raw = input(message).strip()
        try:
            return CurrencyConverter.extract_amount(raw)
        except InvalidAmountError as e:
            print(f"  ! {e} Try again.")


def prompt_currency(message: str) -> str:
    while True:
        raw = input(message).strip()
        try:
            return CurrencyConverter.validate_code(raw)
        except InvalidCurrencyError as e:
            print(f"  ! {e} Try again.")


def prompt_date(message: str) -> date:
    while True:
        raw = input(message).strip()
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("  ! Invalid date format. Use YYYY-MM-DD. Try again.")


def build_trip_budget() -> TripBudget:
    destination = input("Destination name: ").strip()
    home_currency = prompt_currency("Home currency (e.g. NGN): ")
    dest_currency = prompt_currency("Destination currency (e.g. USD): ")
    amount = prompt_float("Total budget amount: ")
    while True:
        try:
            days = int(input("Trip duration (days): ").strip())
            break
        except ValueError:
            print("  ! Please enter a whole number of days.")
    return TripBudget(destination, home_currency, dest_currency, amount, days)


def main():
    print("=== CURRENCY AND TRAVEL BUDGET PLANNER ===")
    current_budget = None
    current_tracker = None

    while True:
        print("\nMenu:")
        print("1. Create a new trip budget")
        print("2. Check public holidays for current trip")
        print("3. Add an expense")
        print("4. View expense summary")
        print("5. Compare with another destination")
        print("6. Export report (JSON/CSV)")
        print("7. Generate AI advice + full report")
        print("8. Exit")

        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                current_budget = build_trip_budget()
                current_tracker = ExpenseTracker(current_budget)
                print(f"\n{current_budget}")

            elif choice == "2":
                if not current_budget:
                    print("Create a trip budget first (option 1).")
                    continue
                start = prompt_date("Trip start date (YYYY-MM-DD): ")
                end = prompt_date("Trip end date (YYYY-MM-DD): ")
                warnings = current_budget.holiday_warnings(start, end)
                if warnings:
                    print("Public holiday warnings:")
                    for d, name in warnings:
                        print(f"  - {d}: {name}")
                else:
                    print("No public holidays found in that date range (based on local dataset).")

            elif choice == "3":
                if not current_tracker:
                    print("Create a trip budget first (option 1).")
                    continue
                category = input("Expense category (e.g. food, hotel): ").strip()
                amount = prompt_float("Expense amount: ")
                currency = prompt_currency("Expense currency: ")
                note = input("Note (optional): ").strip()
                expense = Expense(category, amount, currency, note)
                current_tracker.add_expense(expense)
                print("Expense added.")

            elif choice == "4":
                if not current_tracker:
                    print("Create a trip budget first (option 1).")
                    continue
                print(current_tracker.summary())

            elif choice == "5":
                if not current_budget:
                    print("Create a trip budget first (option 1).")
                    continue
                print("\nNow enter details for the destination to compare against:")
                other_budget = build_trip_budget()
                print("\n" + compare_destinations(current_budget, other_budget))

            elif choice == "6":
                if not current_tracker:
                    print("Create a trip budget first (option 1).")
                    continue
                report = BudgetReport(current_tracker)
                fmt = input("Export as (json/csv): ").strip().lower()
                filename = input("Filename (without extension): ").strip() or "travel_budget"
                if fmt == "csv":
                    report.export_csv(f"{filename}.csv")
                    print(f"Exported to {filename}.csv")
                else:
                    report.export_json(f"{filename}.json")
                    print(f"Exported to {filename}.json")

            elif choice == "7":
                if not current_tracker:
                    print("Create a trip budget first (option 1).")
                    continue
                report = BudgetReport(current_tracker)
                print("\n" + report.generate_summary())

            elif choice == "8":
                print("Safe travels!")
                break

            else:
                print("Invalid option, please choose 1-8.")

        except (InvalidCurrencyError, InvalidAmountError, ConversionError, OSError) as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
