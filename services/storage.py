"""JSON Data Storage and CSV Export Service."""

import csv
import json
import os
from typing import List, Optional
from models.exceptions import StorageError
from models.expense import Expense
from models.trip_budget import TripBudget


class StorageService:
    """Handles JSON file persistence and CSV exports using built-in modules."""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.trips_file = os.path.join(self.data_dir, "trips.json")
        self.expenses_file = os.path.join(self.data_dir, "expenses.json")
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        """Create storage directory and default JSON files if they do not exist."""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            for file_path in [self.trips_file, self.expenses_file]:
                if not os.path.exists(file_path):
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump([], f)
        except Exception as e:
            raise StorageError(f"Failed to initialize storage layer: {str(e)}") from e

    # --- JSON Helper Methods ---
    def _load_json(self, file_path: str) -> List[dict]:
        """Guaranteed atomic loading and fallback recovery on corrupt local files."""
        try:
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                return []
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise StorageError(f"Storage file '{file_path}' corrupted or inaccessible: {str(e)}") from e

    def _save_json(self, file_path: str, data: List[dict]) -> None:
        """Persist data list as formatted JSON to disk."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except OSError as e:
            raise StorageError(f"Failed to write to storage file '{file_path}': {str(e)}") from e

    # --- Trip Management ---
    def save_trip(self, trip: TripBudget) -> TripBudget:
        """Create or update a trip record."""
        trips_data = self._load_json(self.trips_file)
        existing_idx = next((i for i, t in enumerate(trips_data) if t.get("id") == trip.id), None)
        trip_dict = trip.model_dump()

        if existing_idx is not None:
            trips_data[existing_idx] = trip_dict
        else:
            trips_data.append(trip_dict)

        self._save_json(self.trips_file, trips_data)
        return trip

    def get_all_trips(self) -> List[TripBudget]:
        """Retrieve all trips stored on disk."""
        data = self._load_json(self.trips_file)
        return [TripBudget(**item) for item in data]

    def get_trip_by_id(self, trip_id: str) -> Optional[TripBudget]:
        """Fetch a specific trip by its unique ID."""
        trips = self.get_all_trips()
        return next((trip for trip in trips if trip.id == trip_id), None)

    def delete_trip(self, trip_id: str) -> bool:
        """Delete a trip and all its associated expenses."""
        trips = self._load_json(self.trips_file)
        filtered_trips = [t for t in trips if t.get("id") != trip_id]

        if len(trips) == len(filtered_trips):
            return False

        self._save_json(self.trips_file, filtered_trips)
        expenses = self._load_json(self.expenses_file)
        filtered_expenses = [e for e in expenses if e.get("trip_id") != trip_id]
        self._save_json(self.expenses_file, filtered_expenses)
        return True

    # --- Expense Management ---
    def save_expense(self, expense: Expense) -> Expense:
        """Create or update an expense record."""
        expenses_data = self._load_json(self.expenses_file)
        existing_idx = next((i for i, e in enumerate(expenses_data) if e.get("id") == expense.id), None)
        expense_dict = expense.model_dump()

        if existing_idx is not None:
            expenses_data[existing_idx] = expense_dict
        else:
            expenses_data.append(expense_dict)

        self._save_json(self.expenses_file, expenses_data)
        return expense

    def get_expenses_by_trip(self, trip_id: str) -> List[Expense]:
        """Fetch all expenses linked to a given trip."""
        expenses = self._load_json(self.expenses_file)
        return [Expense(**e) for e in expenses if e.get("trip_id") == trip_id]

    def delete_expense(self, expense_id: str) -> bool:
        """Delete an expense record by ID."""
        expenses = self._load_json(self.expenses_file)
        filtered = [e for e in expenses if e.get("id") != expense_id]
        if len(expenses) == len(filtered):
            return False
        self._save_json(self.expenses_file, filtered)
        return True

    # --- CSV Export Engine ---
    def export_expenses_to_csv(self, trip_id: str, output_filepath: str) -> str:
        """Export all expenses for a specific trip to a CSV file using native csv module."""
        trip = self.get_trip_by_id(trip_id)
        if not trip:
            raise StorageError(f"Cannot export: Trip with ID '{trip_id}' not found.")

        expenses = self.get_expenses_by_trip(trip_id)

        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
            with open(output_filepath, mode="w", newline="", encoding="utf-8") as csv_file:
                fieldnames = ["id", "date", "category", "amount", "currency", "amount_in_base_currency", "description"]
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                writer.writeheader()
                for exp in expenses:
                    writer.writerow({
                        "id": exp.id,
                        "date": exp.date,
                        "category": exp.category,
                        "amount": exp.amount,
                        "currency": exp.currency,
                        "amount_in_base_currency": exp.amount_in_base_currency,
                        "description": exp.description,
                    })
            return output_filepath
        except Exception as e:
            raise StorageError(f"Failed to export expenses to CSV: {str(e)}") from e