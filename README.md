# Currency & Travel Budget Planner

A production-grade Python application built with Streamlit, ExchangeRate API, Nager.Date API, and Google Gemini API.

## Project Structure

- `app.py`: Main Streamlit UI entry point.
- `models/`: Core domain classes (`currency.py`, `trip_budget.py`, `expense.py`, `report.py`).
- `services/`: Application business logic (`currency_converter.py`, `holiday_checker.py`, `ai_service.py`, `comparison.py`, `storage.py`).
- `utils/`: Validation and regular expression utilities (`validator.py`, `regex_utils.py`).

## Quick Start

1. Clone the repository and navigate to the project directory:
   ```bash
   cd currency-travel-budget-planner
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your API credentials:
   ```bash
   cp .env.example .env
   ```
5. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```