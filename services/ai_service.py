"""Gemini AI Travel Assistant service using google-genai SDK."""

import os
from typing import Optional
from dotenv import load_dotenv
from google import genai

from models.exceptions import APIError
from models.trip_budget import TripBudget

# Ensure variables from .env are loaded into os.environ
load_dotenv()


class AITravelAssistantService:
    """Service providing AI-powered travel advice, itineraries, and budget optimization."""

    DEFAULT_MODEL = "gemini-flash-latest"

    def __init__(self, api_key: Optional[str] = None):
        raw_key = api_key or os.getenv("GEMINI_API_KEY", "")
        # Clean extra quotes or spaces from .env parsing
        self.api_key = raw_key.strip().strip('"').strip("'")
        
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def generate_trip_advice(self, trip: TripBudget) -> str:
        """Generate tailored travel recommendations based on trip parameters."""
        prompt = (
            f"You are an expert travel advisor. Provide a concise, highly practical travel and budgeting "
            f"guide for a trip to {trip.destination_country}.\n"
            f"- Duration: {trip.duration_days} days\n"
            f"- Total Budget: {trip.total_budget} {trip.base_currency}\n"
            f"- Daily Allowance: {trip.calculate_daily_budget()} {trip.base_currency}/day\n"
            f"- Target Currency: {trip.destination_currency}\n\n"
            f"Please structure your response into 3 bulleted sections:\n"
            f"1. Top Money-Saving Tips for {trip.destination_country}\n"
            f"2. Local Payment Practices (Cash vs. Card)\n"
            f"3. High-Value Budget Activities"
        )
        return self._send_prompt(prompt, fallback_type="advice", trip=trip)

    def generate_itinerary(self, trip: TripBudget) -> str:
        """Generate a realistic day-by-day itinerary fitting the trip duration and budget."""
        prompt = (
            f"Create a realistic day-by-day travel itinerary for a {trip.duration_days}-day trip to "
            f"{trip.destination_country} with a budget of {trip.total_budget} {trip.base_currency}.\n"
            f"Keep activities budget-friendly and highlight popular cultural, culinary, and historic attractions."
        )
        return self._send_prompt(prompt, fallback_type="itinerary", trip=trip)

    def generate_expense_tips(self, category: str, total_spent: float, currency: str) -> str:
        """Provide specific advice to curb overspending in a particular category."""
        prompt = (
            f"I have spent {total_spent} {currency} on '{category}' during my current trip, "
            f"which is exceeding my plan. Give me 3 immediate, actionable tips to reduce spending in this category."
        )
        return self._send_prompt(prompt, fallback_type="expense_tips", category=category)

    def _send_prompt(
        self,
        prompt: str,
        fallback_type: str,
        trip: Optional[TripBudget] = None,
        category: Optional[str] = None,
    ) -> str:
        """Execute request to Gemini API via genai Client with error fallback."""
        if not self.client:
            return self._get_fallback_response(fallback_type, trip, category)

        try:
            response = self.client.models.generate_content(
                model=self.DEFAULT_MODEL,
                contents=prompt,
            )
            if response and response.text:
                return response.text
            raise APIError("Empty response received from Gemini API.")

        except Exception as e:
            # Print exception to terminal console for debugging
            print(f"[Gemini API Error]: {e}")
            return (
                f"*(AI API temporarily unavailable: {e}. Displaying offline baseline advice)*\n\n"
                + self._get_fallback_response(fallback_type, trip, category)
            )

    def _get_fallback_response(
        self, fallback_type: str, trip: Optional[TripBudget] = None, category: Optional[str] = None
    ) -> str:
        """Provide helpful fallback text when Gemini API key is not configured."""
        if fallback_type == "advice" and trip:
            return (
                f"### Travel & Budget Guide for {trip.destination_country}\n\n"
                f"* **Money-Saving**: Use public transportation passes and eat at local lunch markets.\n"
                f"* **Payments**: Carry a mix of local currency ({trip.destination_currency}) cash and fee-free cards.\n"
                f"* **Activities**: Explore free museums, public parks, and walking tours."
            )
        elif fallback_type == "itinerary" and trip:
            return (
                f"### Sample {trip.duration_days}-Day Itinerary ({trip.destination_country})\n\n"
                f"* **Day 1**: Arrival, check-in, and local neighborhood exploration.\n"
                f"* **Mid-Trip**: Sightseeing major historical spots and enjoying regional cuisine.\n"
                f"* **Final Day**: Souvenir shopping, market visits, and preparation for departure."
            )
        else:
            cat_name = category or "Expenses"
            return (
                f"### Budget Control for {cat_name}\n\n"
                f"1. Compare prices online before making purchases.\n"
                f"2. Set a firm daily spending limit for {cat_name}.\n"
                f"3. Look for bundle discounts or off-peak deals."
            )
        