"""Main Streamlit Application Entry Point for Currency & Travel Budget Planner."""

import os
import pandas as pd
from dotenv import load_dotenv
import streamlit as st

from models.currency import CurrencyConversionRequest
from models.exceptions import PlannerException
from models.expense import Expense
from models.trip_budget import TripBudget
from services.ai_service import AITravelAssistantService
from services.comparison import CountryComparisonService
from services.currency_converter import CurrencyConverterService
from services.expense_tracker import ExpenseTrackerService
from services.holiday_checker import HolidayCheckerService
from services.storage import StorageService

load_dotenv()


# Page Configuration
st.set_page_config(
    page_title="Currency & Travel Budget Planner",
    page_icon="✈️",
    layout="wide",
)


# Dependency Injection via Session State
@st.cache_resource
def get_services():
    storage = StorageService()
    currency = CurrencyConverterService()
    expense_tracker = ExpenseTrackerService(storage)
    comparison = CountryComparisonService(currency)
    holidays = HolidayCheckerService()
    ai_assistant = AITravelAssistantService()
    return storage, currency, expense_tracker, comparison, holidays, ai_assistant


storage_svc, currency_svc, expense_svc, comparison_svc, holiday_svc, ai_svc = get_services()


# --- Main Header ---
st.title("✈️ Currency & Travel Budget Planner")
st.caption("Plan trips, convert currencies, track expenses, compare countries, and get AI travel insights.")

# Navigation Tabs
tab_trips, tab_expenses, tab_currency, tab_comparison, tab_ai = st.tabs([
    "🧳 Trips & Budgeting",
    "💳 Expense Tracker",
    "💱 Currency Converter",
    "🌍 Country & Holiday Insights",
    "🤖 AI Assistant",
])


# ==============================================================================
# TAB 1: TRIPS & BUDGETING
# ==============================================================================
with tab_trips:
    st.header("Trip Management")

    col_create, col_list = st.columns([1, 2])

    with col_create:
        st.subheader("Create New Trip")
        with st.form("create_trip_form", clear_on_submit=True):
            dest_country = st.text_input("Destination Country", placeholder="France")
            dest_code = st.text_input("Country Code (2-letter ISO)", placeholder="FR", max_chars=2)
            base_curr = st.text_input("Base Currency (3-letter)", value="USD", max_chars=3)
            dest_curr = st.text_input("Destination Currency (3-letter)", value="EUR", max_chars=3)
            total_budget = st.number_input("Total Budget", min_value=1.0, value=1500.0, step=50.0)
            start_d = st.date_input("Start Date")
            end_d = st.date_input("End Date")
            notes = st.text_area("Notes / Objectives", placeholder="Summer vacation in Paris")

            submitted = st.form_submit_button("Create Trip")
            if submitted:
                try:
                    duration = (end_d - start_d).days + 1
                    new_trip = TripBudget(
                        destination_country=dest_country,
                        destination_country_code=dest_code,
                        base_currency=base_curr,
                        destination_currency=dest_curr,
                        total_budget=total_budget,
                        duration_days=duration,
                        start_date=str(start_d),
                        end_date=str(end_d),
                        notes=notes,
                    )
                    storage_svc.save_trip(new_trip)
                    st.success(f"Successfully created trip to {dest_country}!")
                    st.rerun()
                except PlannerException as e:
                    st.error(f"Validation Error: {str(e)}")
                except Exception as e:
                    st.error(f"Error creating trip: {str(e)}")

    with col_list:
        st.subheader("Your Trips")
        all_trips = storage_svc.get_all_trips()

        if not all_trips:
            st.info("No trips created yet. Use the form on the left to add your first trip.")
        else:
            for trip in all_trips:
                summary = expense_svc.generate_summary_report(trip.id)
                with st.expander(f"📍 {trip.destination_country} ({trip.start_date} to {trip.end_date})", expanded=True):
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total Budget", f"{trip.total_budget:,.2f} {trip.base_currency}")
                    m2.metric("Total Spent", f"{summary.total_spent:,.2f} {trip.base_currency}")
                    m3.metric("Remaining", f"{summary.remaining_budget:,.2f} {trip.base_currency}")
                    m4.metric("Daily Cap", f"{trip.calculate_daily_budget():,.2f} {trip.base_currency}/day")

                    if summary.is_over_budget:
                        st.warning("⚠️ Warning: You have exceeded your total budget for this trip!")

                    col_del, _ = st.columns([1, 4])
                    if col_del.button("Delete Trip", key=f"del_trip_{trip.id}"):
                        storage_svc.delete_trip(trip.id)
                        st.success("Trip deleted.")
                        st.rerun()


# ==============================================================================
# TAB 2: EXPENSE TRACKER
# ==============================================================================
with tab_expenses:
    st.header("Expense Tracker")

    trips = storage_svc.get_all_trips()
    if not trips:
        st.info("Please create a trip first before adding expenses.")
    else:
        trip_options = {f"{t.destination_country} ({t.start_date})": t for t in trips}
        selected_trip_label = st.selectbox("Select Active Trip", list(trip_options.keys()))
        active_trip = trip_options[selected_trip_label]

        col_add_exp, col_view_exp = st.columns([1, 2])

        with col_add_exp:
            st.subheader("Add New Expense")
            with st.form("add_expense_form", clear_on_submit=True):
                exp_cat = st.selectbox("Category", ["Accommodation", "Food & Dining", "Transport", "Activities", "Shopping", "Misc"])
                exp_amount = st.number_input("Amount Spent", min_value=0.01, value=45.0, step=5.0)
                exp_currency = st.text_input("Expense Currency", value=active_trip.destination_currency, max_chars=3)
                exp_date = st.date_input("Expense Date")
                exp_desc = st.text_input("Description", placeholder="Dinner at bistro")

                if st.form_submit_button("Log Expense"):
                    try:
                        # Convert amount to base currency if needed
                        if exp_currency.upper() != active_trip.base_currency.upper():
                            req = CurrencyConversionRequest(
                                from_currency=exp_currency,
                                to_currency=active_trip.base_currency,
                                amount=exp_amount,
                            )
                            rate_res = currency_svc.convert(req)
                            converted_val = rate_res.converted_amount
                        else:
                            converted_val = exp_amount

                        new_exp = Expense(
                            trip_id=active_trip.id,
                            category=exp_cat,
                            amount=exp_amount,
                            currency=exp_currency,
                            amount_in_base_currency=converted_val,
                            date=str(exp_date),
                            description=exp_desc,
                        )
                        expense_svc.log_expense(new_exp)
                        st.success("Expense logged successfully!")
                        st.rerun()
                    except PlannerException as e:
                        st.error(f"Error: {str(e)}")

        with col_view_exp:
            st.subheader("Expense History & Filtering")

            search_q = st.text_input("Search Description or Category", "")
            cat_filter = st.selectbox("Filter Category", ["All", "Accommodation", "Food & Dining", "Transport", "Activities", "Shopping", "Misc"])

            filtered_expenses = expense_svc.filter_expenses(
                trip_id=active_trip.id,
                category=None if cat_filter == "All" else cat_filter,
                search_query=search_q,
            )

            if not filtered_expenses:
                st.write("No matching expenses found.")
            else:
                table_data = [
                    {
                        "Date": e.date,
                        "Category": e.category,
                        "Description": e.description,
                        "Amount": f"{e.amount:,.2f} {e.currency}",
                        "In Base Currency": f"{e.amount_in_base_currency:,.2f} {active_trip.base_currency}",
                        "ID": e.id,
                    }
                    for e in filtered_expenses
                ]
                st.dataframe(table_data, use_container_width=True)

                # Export to CSV (Saved locally to ./data/ AND downloaded in browser)
                csv_filename = f"expenses_{active_trip.id[:8]}.csv"
                csv_path = f"./data/{csv_filename}"
                
                # Ensure local save to data folder
                storage_svc.export_expenses_to_csv(active_trip.id, csv_path)

                # Convert dataframe to CSV string for browser download
                df = pd.DataFrame(table_data)
                csv_bytes = df.to_csv(index=False).encode('utf-8')

                st.download_button(
                    label="Export Expenses to CSV",
                    data=csv_bytes,
                    file_name=csv_filename,
                    mime="text/csv",
                )


# ==============================================================================
# TAB 3: CURRENCY CONVERTER
# ==============================================================================
with tab_currency:
    st.header("Currency Converter")

    col_conv1, col_conv2 = st.columns(2)
    with col_conv1:
        from_c = st.text_input("From Currency (3-letter)", value="USD", max_chars=3)
        to_c = st.text_input("To Currency (3-letter)", value="EUR", max_chars=3)
        conv_amt = st.number_input("Amount to Convert", min_value=1.0, value=100.0, step=10.0)

        if st.button("Convert Currency"):
            try:
                req = CurrencyConversionRequest(
                    from_currency=from_c,
                    to_currency=to_c,
                    amount=conv_amt,
                )
                res = currency_svc.convert(req)
                st.success(f"**{conv_amt:,.2f} {from_c.upper()}** = **{res.converted_amount:,.2f} {to_c.upper()}**")
                st.caption(f"Exchange Rate: 1 {from_c.upper()} = {res.exchange_rate:.4f} {to_c.upper()}")
            except PlannerException as e:
                st.error(f"Conversion Error: {str(e)}")


# ==============================================================================
# TAB 4: COUNTRY COMPARISON & HOLIDAYS
# ==============================================================================
with tab_comparison:
    st.header("Country Comparison & Holiday Checker")

    col_comp, col_hol = st.columns(2)

    with col_comp:
        st.subheader("Compare Destination Costs")
        selected_codes = st.multiselect(
            "Select Countries to Compare",
            options=["FR", "JP", "TH", "US", "GB", "NG", "KE"],
            default=["FR", "JP", "TH"],
        )
        comp_days = st.number_input("Trip Duration (Days)", min_value=1, value=7)

        if st.button("Compare Costs"):
            comparisons = comparison_svc.compare_countries(selected_codes, duration_days=comp_days)
            for c in comparisons:
                st.markdown(f"### 📍 {c.country_name} ({c.country_code})")
                st.write(f"- **Est. Daily Cost**: ${c.estimated_daily_cost_usd:,.2f} USD")
                st.write(f"- **Est. Total Cost ({comp_days} days)**: ${c.estimated_total_cost_usd:,.2f} USD")
                st.write(f"- **Major Cities**: {', '.join(c.major_cities)}")
                st.divider()

    with col_hol:
        st.subheader("Check Public Holidays")
        c_code = st.text_input("Country Code (e.g., FR, US, JP)", value="FR", max_chars=2)
        h_start = st.date_input("Start Date", key="hol_start")
        h_end = st.date_input("End Date", key="hol_end")

        if st.button("Find Holidays"):
            try:
                holidays_found = holiday_svc.get_holidays_during_trip(c_code, str(h_start), str(h_end))
                if not holidays_found:
                    st.info("No public holidays found during these dates.")
                else:
                    for h in holidays_found:
                        st.write(f" **{h['date']}**: {h['name']} ({h['local_name']})")
            except PlannerException as e:
                st.error(f"Holiday Check Error: {str(e)}")


# ==============================================================================
# TAB 5: GEMINI AI ASSISTANT
# ==============================================================================
with tab_ai:
    st.header("AI Travel Assistant")

    trips = storage_svc.get_all_trips()
    if not trips:
        st.info("Please create a trip first to enable AI recommendations.")
    else:
        trip_map = {f"{t.destination_country} ({t.start_date})": t for t in trips}
        selected_ai_trip = st.selectbox("Select Trip for AI Analysis", list(trip_map.keys()))
        ai_trip = trip_map[selected_ai_trip]

        col_a1, col_a2 = st.columns(2)

        with col_a1:
            if st.button("Generate Travel & Budget Guide"):
                with st.spinner("Generating travel insights..."):
                    advice = ai_svc.generate_trip_advice(ai_trip)
                    st.markdown(advice)

        with col_a2:
            if st.button("Generate Day-by-Day Itinerary"):
                with st.spinner("Crafting custom itinerary..."):
                    itinerary = ai_svc.generate_itinerary(ai_trip)
                    st.markdown(itinerary)