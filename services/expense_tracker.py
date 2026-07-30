"""Expense tracking, searching, filtering, and summary logic."""

from typing import Dict, List, Optional
from models.expense import Expense
from models.report import BudgetSummaryReport
from models.trip_budget import TripBudget
from services.storage import StorageService


class ExpenseTrackerService:
    """Business logic for searching, filtering, and aggregating trip expenses."""

    def __init__(self, storage_service: StorageService):
        self.storage = storage_service

    # --- CRUD Wrappers ---
    def add_expense(self, expense: Expense) -> Expense:
        """Add or update an expense."""
        return self.storage.save_expense(expense)

    def log_expense(self, expense: Expense) -> Expense:
        """Alias for add_expense to support log_expense calls."""
        return self.add_expense(expense)

    def delete_expense(self, expense_id: str) -> bool:
        """Remove an expense record by ID."""
        return self.storage.delete_expense(expense_id)

    def get_expenses_for_trip(self, trip_id: str) -> List[Expense]:
        """Fetch all expenses associated with a specific trip."""
        return self.storage.get_expenses_by_trip(trip_id)

    # --- Search & Filter ---
    def filter_expenses(
        self,
        trip_id: str,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[Expense]:
        """Filter expenses by category, date range, or text query."""
        expenses = self.get_expenses_for_trip(trip_id)

        if category and category.strip().lower() != "all":
            expenses = [e for e in expenses if e.category.lower() == category.strip().lower()]

        if start_date:
            expenses = [e for e in expenses if e.date >= start_date]

        if end_date:
            expenses = [e for e in expenses if e.date <= end_date]

        if search_query:
            q = search_query.strip().lower()
            expenses = [
                e for e in expenses
                if q in e.description.lower() or q in e.category.lower()
            ]

        return expenses

    # --- Summaries & Reporting ---
    def generate_summary_report(self, trip_or_id) -> BudgetSummaryReport:
        """Calculate total spend, category breakdown, remaining budget, and daily averages.
        
        Accepts either a TripBudget object or a string trip_id for maximum flexibility.
        """
        if isinstance(trip_or_id, str):
            trip = self.storage.get_trip_by_id(trip_or_id)
            if not trip:
                raise ValueError(f"Trip with ID {trip_or_id} not found.")
        else:
            trip = trip_or_id

        expenses = self.get_expenses_for_trip(trip.id)

        total_spent = sum(exp.amount_in_base_currency for exp in expenses)
        remaining = round(trip.total_budget - total_spent, 2)
        daily_avg = round(total_spent / trip.duration_days, 2) if trip.duration_days > 0 else 0.0

        category_breakdown: Dict[str, float] = {}
        for exp in expenses:
            category_breakdown[exp.category] = round(
                category_breakdown.get(exp.category, 0.0) + exp.amount_in_base_currency, 2
            )

        return BudgetSummaryReport(
            trip_id=trip.id,
            destination_country=trip.destination_country,
            total_budget=trip.total_budget,
            total_spent=round(total_spent, 2),
            remaining_budget=remaining,
            base_currency=trip.base_currency,
            daily_average_spent=daily_avg,
            category_breakdown=category_breakdown,
            is_over_budget=total_spent > trip.total_budget,
        )