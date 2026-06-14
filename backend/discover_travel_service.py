"""
Intelligent Travel Service — AI-powered route comparison for Indian locations.

Uses Groq LLM (Llama 3.3 70B) for realistic transport pricing with a
deterministic fare formula fallback. Results are cached in MongoDB for 24h.
"""

import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

logger = logging.getLogger(__name__)

# ============ PROMPTS ============

TRAVEL_SYSTEM_PROMPT = """You are a travel cost estimator for Indian locations.
Given a source and destination, estimate realistic travel costs in Indian Rupees (₹).

Return a JSON array of transport options. Each option must have:
- mode: transport type (Auto, Metro, Bus, Ola/Uber, Cycle Rickshaw, Walk, Train, Local Train)
- cost: estimated cost in ₹ (integer)
- time: estimated duration (e.g. "25 min", "1h 30min")
- distance: approximate distance (e.g. "3.5 km")
- eco: boolean (true for walking, cycling, metro, bus)
- safe: boolean (true for all except walking alone at night)
- notes: any relevant info (peak pricing, availability)

Only include modes that make sense for the given distance.
For intra-city (<15km): Auto, Metro, Bus, Ola/Uber, Cycle Rickshaw, Walk
For intercity (>15km): Bus, Train, Ola/Uber

Use realistic 2024 Indian pricing:
- Auto: ₹25 base + ₹15/km (varies by city)
- Ola/Uber: ₹50 base + ₹10/km (mini), surge possible
- Metro (where available): ₹10-60 depending on stations
- Bus: ₹5-10/km for city, ₹1-2/km for intercity
- Train: ₹1-2/km (sleeper), ₹2-4/km (AC)
- Cycle Rickshaw: ₹20 base + ₹10/km (short distances only)

Return ONLY valid JSON array, no markdown, no explanation."""

TRAVEL_USER_PROMPT = "Estimate travel costs from '{source}' to '{destination}' in India."


def _now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _iso_plus_hours(hours: int) -> str:
    """Return ISO timestamp for now + given hours."""
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


class TravelService:
    """AI-powered travel route comparison service for Indian locations."""

    def __init__(self, db):
        self.db = db

    async def get_routes(self, source: str, destination: str, user_id: str) -> list[dict]:
        """
        Orchestrate route comparison: cache check -> LLM -> fallback.

        Returns a list of route option dicts with mode, cost, time, distance, eco, safe, notes.
        """
        # Step 1: Normalize inputs
        source_norm = source.strip().lower()
        dest_norm = destination.strip().lower()

        # Step 2: Check cache
        cached = await self.get_cached_route(source_norm, dest_norm)
        if cached is not None:
            return cached

        # Step 3: Try LLM estimation
        routes = await self.estimate_via_llm(source, destination)

        # Step 4: Validate LLM response
        if not routes or not self._validate_routes(routes):
            # Step 5: Fallback to formula with default distance
            routes = self.estimate_via_formula(5.0)

        # Step 6: Cache result
        await self._cache_result(source, destination, source_norm, dest_norm, routes)

        return routes

    async def get_cached_route(self, source_normalized: str, destination_normalized: str) -> Optional[list[dict]]:
        """
        Check MongoDB route_cache for a previously computed route within TTL.

        Returns the cached routes list if found and not expired, otherwise None.
        """
        now = _now_iso()
        cached = await self.db.route_cache.find_one({
            "source_normalized": source_normalized,
            "destination_normalized": destination_normalized,
            "expires_at": {"$gt": now}
        })

        if cached:
            return cached.get("routes", [])
        return None

    async def estimate_via_llm(self, source: str, destination: str) -> list[dict]:
        """
        Query Groq LLM for realistic Indian transport pricing.

        Returns a list of route option dicts, or an empty list on failure.
        """
        try:
            api_key = os.getenv("GROQ_API_KEY", "")
            if not api_key:
                logger.warning("GROQ_API_KEY not set, skipping LLM estimation")
                return []

            llm = LlmChat(
                api_key=api_key,
                session_id="discover-travel",
                system_message=TRAVEL_SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=2048,
                cache_enabled=True,
            ).with_model("groq", "llama-3.3-70b-versatile")

            user_prompt = TRAVEL_USER_PROMPT.format(source=source, destination=destination)

            full_text = ""
            async for event in llm.stream_message(UserMessage(text=user_prompt)):
                if isinstance(event, TextDelta):
                    full_text += event.content
                elif isinstance(event, StreamDone):
                    break

            # Parse JSON response - handle markdown code blocks if LLM wraps response
            full_text = full_text.strip()
            if full_text.startswith("```"):
                lines = full_text.split("\n")
                lines = [line for line in lines if not line.strip().startswith("```")]
                full_text = "\n".join(lines)

            routes = json.loads(full_text)

            if not isinstance(routes, list):
                logger.warning("LLM returned non-list response for travel estimation")
                return []

            return routes

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse LLM travel response: {e}")
            return []
        except Exception as e:
            logger.error(f"LLM travel estimation failed: {e}")
            return []

    def estimate_via_formula(self, distance_km: float) -> list[dict]:
        """
        Deterministic fare calculation using known Indian transport rates.

        Rates:
        - Auto: 25 base + 15/km
        - Bus: 7/km
        - Metro: 10 base + 3/km (capped at 60)
        - Ola/Uber: 50 base + 10/km
        - Cycle Rickshaw: 20 base + 10/km (only for distance < 5km)
        - Walk: 0 (only for distance < 3km)
        """
        routes = []

        # Auto rickshaw: Rs 25 base + Rs 15/km
        auto_cost = round(25 + 15 * distance_km)
        routes.append({
            "mode": "Auto",
            "cost": auto_cost,
            "time": f"{max(1, round(distance_km * 4))} min",
            "distance": f"{distance_km} km",
            "eco": False,
            "safe": True,
            "notes": "Metered fare, may vary by city"
        })

        # Bus: Rs 7/km
        bus_cost = round(7 * distance_km)
        routes.append({
            "mode": "Bus",
            "cost": bus_cost,
            "time": f"{max(1, round(distance_km * 5))} min",
            "distance": f"{distance_km} km",
            "eco": True,
            "safe": True,
            "notes": "City bus, frequent stops"
        })

        # Metro: Rs 10 base + Rs 3/km, capped at Rs 60
        metro_cost = min(round(10 + 3 * distance_km), 60)
        routes.append({
            "mode": "Metro",
            "cost": metro_cost,
            "time": f"{max(1, round(distance_km * 3))} min",
            "distance": f"{distance_km} km",
            "eco": True,
            "safe": True,
            "notes": "Where metro is available"
        })

        # Ola/Uber: Rs 50 base + Rs 10/km
        cab_cost = round(50 + 10 * distance_km)
        routes.append({
            "mode": "Ola/Uber",
            "cost": cab_cost,
            "time": f"{max(1, round(distance_km * 3.5))} min",
            "distance": f"{distance_km} km",
            "eco": False,
            "safe": True,
            "notes": "Mini category, surge may apply"
        })

        # Cycle Rickshaw: Rs 20 base + Rs 10/km (only for distance < 5km)
        if distance_km < 5:
            rickshaw_cost = round(20 + 10 * distance_km)
            routes.append({
                "mode": "Cycle Rickshaw",
                "cost": rickshaw_cost,
                "time": f"{max(1, round(distance_km * 6))} min",
                "distance": f"{distance_km} km",
                "eco": True,
                "safe": True,
                "notes": "Short distances only"
            })

        # Walk: Rs 0 (only for distance < 3km)
        if distance_km < 3:
            routes.append({
                "mode": "Walk",
                "cost": 0,
                "time": f"{max(1, round(distance_km * 12))} min",
                "distance": f"{distance_km} km",
                "eco": True,
                "safe": True,
                "notes": "Free and healthy"
            })

        return routes

    async def _cache_result(
        self,
        source: str,
        destination: str,
        source_normalized: str,
        destination_normalized: str,
        routes: list[dict]
    ) -> None:
        """Store route result in MongoDB route_cache with 24h TTL."""
        try:
            await self.db.route_cache.insert_one({
                "source": source,
                "destination": destination,
                "source_normalized": source_normalized,
                "destination_normalized": destination_normalized,
                "routes": routes,
                "created_at": _now_iso(),
                "expires_at": _iso_plus_hours(24),
            })
        except Exception as e:
            logger.error(f"Failed to cache route result: {e}")

    def _validate_routes(self, routes: list) -> bool:
        """Validate that LLM response contains properly structured route options."""
        if not routes:
            return False

        required_fields = {"mode", "cost", "time", "distance"}
        for route in routes:
            if not isinstance(route, dict):
                return False
            if not required_fields.issubset(route.keys()):
                return False
            # cost must be a non-negative number
            cost = route.get("cost")
            if not isinstance(cost, (int, float)) or cost < 0:
                return False

        return True
