"""
Conversational AI, Natural Language Understanding (NLU), and Natural Language Explanation (NLG) Engine.
Integrates Google Gemini with robust deterministic rule-based fallback.
Ensures Gemini is isolated to constraint parsing and factual explanation without altering deterministic results.
"""

import re
import json
from typing import Dict, Any, Optional, List, Tuple
from app.core.config import settings
from app.schemas.chat import (
    ExtractedTripConstraintsSchema,
    ReplanningDiffSchema,
)
from app.schemas.optimization import MultiDayTripOptimizationResponse


class ConversationalEngine:
    """
    NLU and Explanation Engine.
    Leverages Google Gemini when available; seamlessly falls back to regex/rule-based parsing
    and deterministic template generation when Gemini is unavailable or unconfigured.
    """

    KNOWN_DESTINATIONS = {
        "hampi": ["hampi", "vijayanagara", "unesco hampi"],
        "coorg": ["coorg", "kodagu", "madikeri"],
        "dandeli": ["dandeli", "kali river", "dandeli jungle"],
        "goa": ["goa", "north goa", "south goa", "panaji", "calangute", "baga", "anjuna", "candolim"],
    }

    INTEREST_KEYWORDS = {
        "heritage": ["heritage", "history", "historical", "ancient", "monument", "temple", "ruins", "architecture", "fort", "church"],
        "nature": ["nature", "scenic", "waterfall", "coffee", "plantation", "greenery", "hills", "reservoir", "lake", "forest"],
        "adventure": ["adventure", "rafting", "kayaking", "trekking", "trek", "safari", "wildlife", "camping", "water sports", "scuba"],
        "religious": ["religious", "temple", "spiritual", "pilgrimage", "shrine", "sacred", "church"],
        "beach": ["beach", "sea", "ocean", "coastal", "sand", "sunset"],
    }

    NUMBER_WORDS = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    }

    GREETING_REGEX = re.compile(
        r"^(?:hi+|hello+|hey+|heyy+|hola|greetings|namaste|howdy|sup|yo|good\s+(?:morning|afternoon|evening|day))[\s!.,?]*$",
        re.IGNORECASE,
    )

    GREETING_PREFIX_REGEX = re.compile(
        r"\b(?:hi+|hello+|hey+|heyy+|hola|greetings|namaste|howdy|good\s+(?:morning|afternoon|evening|day))\b",
        re.IGNORECASE,
    )

    THANKS_REGEX = re.compile(
        r"^(?:thank\s*you|thanks|thx|thank\s*u|ty|great|awesome|cool|ok|okay)[\s!.,?]*$",
        re.IGNORECASE,
    )

    HELP_REGEX = re.compile(
        r"^(?:help|what\s+can\s+you\s+do|who\s+are\s+you|how\s+does\s+this\s+work)[\s!.,?]*$",
        re.IGNORECASE,
    )

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL

    def is_greeting(self, text: str) -> bool:
        """Check if message contains or is a greeting."""
        return bool(self.GREETING_PREFIX_REGEX.search(text.strip()))

    def is_pure_greeting(self, text: str) -> bool:
        """Check if message is ONLY a greeting without other commands."""
        return bool(self.GREETING_REGEX.match(text.strip()))

    def is_pure_thanks(self, text: str) -> bool:
        """Check if message is an acknowledgement/thanks."""
        return bool(self.THANKS_REGEX.match(text.strip()))

    def is_help_query(self, text: str) -> bool:
        """Check if message is asking for help or capabilities."""
        return bool(self.HELP_REGEX.match(text.strip()))

    def extract_constraints_rule_based(self, text: str) -> ExtractedTripConstraintsSchema:
        """
        Deterministic regex/rule-based NLU fallback parser.
        Robustly parses destination, duration (including digits and number words),
        budget, party size, pace, interests, and transport.
        """
        text_lower = text.lower().strip()
        has_greeting = self.is_greeting(text_lower)

        # 1. Extract Destination
        detected_dest_id = None
        for dest_id, aliases in self.KNOWN_DESTINATIONS.items():
            if any(re.search(r"\b" + re.escape(alias) + r"\b", text_lower) for alias in aliases):
                detected_dest_id = dest_id
                break

        # 2. Extract Duration (Days)
        duration_days = None

        # A. Pattern: "3 days", "3-day", "3 d", "3 nights"
        day_match = re.search(r"(\d+)\s*(?:-|–|\s)?\s*(?:days?|d\b|nights?)", text_lower)
        if day_match:
            duration_days = min(14, max(1, int(day_match.group(1))))

        # B. Pattern: Number words with days: "three days", "two nights", "for 3 days"
        if not duration_days:
            for word, num in self.NUMBER_WORDS.items():
                if re.search(r"\b" + word + r"\s*(?:days?|d\b|nights?)", text_lower):
                    duration_days = num
                    break

        # C. Special words: weekend, week, two weeks
        if not duration_days:
            if "two weeks" in text_lower or "2 weeks" in text_lower:
                duration_days = 14
            elif "weekend" in text_lower:
                duration_days = 2
            elif "week" in text_lower or "1 week" in text_lower or "a week" in text_lower or "one week" in text_lower:
                duration_days = 7

        # D. Direct / Standalone number or number word (e.g. user replies "3", "three", "for 3", "just 2", "staying 4")
        if not duration_days:
            # Check if input is a simple phrase like "3", "for 3", "just 3", "make it 3", "three"
            isolated_num_match = re.search(r"\b(?:for|just|around|about|staying|make it)?\s*(\d{1,2})\b", text_lower)
            if isolated_num_match:
                candidate_val = int(isolated_num_match.group(1))
                # Ensure it is in plausible day range (1-14) and not a currency/budget indicator
                if 1 <= candidate_val <= 14:
                    # Check that it's not accompanied by budget keywords
                    if not re.search(r"(?:rs|inr|₹|budget|k\b|000)", text_lower):
                        duration_days = candidate_val

        if not duration_days:
            # Check standalone number words: "three", "for two", "four"
            for word, num in self.NUMBER_WORDS.items():
                if re.search(r"\b" + word + r"\b", text_lower):
                    if not re.search(r"(?:rs|inr|₹|budget|thousand|k\b)", text_lower):
                        duration_days = num
                        break

        # 3. Extract Budget
        budget = None
        budget_match = re.search(
            r"(?:rs\.?|inr|₹|budget(?:\s+of|\s+is|\s+below|\s+under)?)\s*[:=]?\s*(\d+[\d,]*)(?:\s*k)?",
            text_lower,
        )
        if budget_match:
            raw_b = budget_match.group(1).replace(",", "")
            val = float(raw_b)
            if "k" in text_lower and val < 1000:
                val *= 1000
            budget = val
        else:
            k_match = re.search(r"(\d+)\s*k\b", text_lower)
            if k_match:
                budget = float(k_match.group(1)) * 1000
            else:
                # Check for large numbers like "15000" or "12000" without prefix
                large_num = re.search(r"\b(\d{4,6})\b", text_lower)
                if large_num:
                    budget = float(large_num.group(1))

        # 4. Extract Party Size
        party_size = None
        party_match = re.search(
            r"(\d+)\s*(?:people|persons|travelers|travellers|friends|adults|members|of us)", text_lower
        )
        if party_match:
            party_size = int(party_match.group(1))
        elif "solo" in text_lower or "just me" in text_lower or "myself" in text_lower:
            party_size = 1
        elif "couple" in text_lower or "me and my wife" in text_lower or "me and my husband" in text_lower or "me and my partner" in text_lower:
            party_size = 2
        elif "family" in text_lower:
            party_size = 4

        # 5. Extract Interests
        detected_interests = []
        for tag, keywords in self.INTEREST_KEYWORDS.items():
            if any(re.search(r"\b" + re.escape(kw) + r"\b", text_lower) for kw in keywords):
                detected_interests.append(tag)

        # 6. Extract Pace
        pace = None
        if re.search(r"\b(?:relaxed|slow|leisure|chill|easy)\b", text_lower):
            pace = "Relaxed"
        elif re.search(r"\b(?:intense|fast|packed|busy|hectic)\b", text_lower):
            pace = "Intense"
        elif re.search(r"\b(?:moderate|balanced|medium|normal)\b", text_lower):
            pace = "Moderate"

        # 7. Extract Transport
        transport = None
        if re.search(r"\b(?:walking|walk|on foot|foot)\b", text_lower):
            transport = "walking"
        elif re.search(r"\b(?:auto|rickshaw|tuk|tuk-tuk|autorickshaw)\b", text_lower):
            transport = "auto"
        elif re.search(r"\b(?:car|cab|taxi|uber|ola)\b", text_lower):
            transport = "car"
        elif re.search(r"\b(?:rental|bike|scooter|self-drive|scooty)\b", text_lower):
            transport = "rental"
        elif re.search(r"\b(?:public|bus|train|transit)\b", text_lower):
            transport = "public"

        # Determine missing fields and clarification
        missing = []
        if not detected_dest_id:
            missing.append("destination")
        if not duration_days:
            missing.append("duration_days")

        clarification = None
        if has_greeting and "destination" in missing and "duration_days" in missing:
            clarification = "Hello! 👋 Welcome to Travel Genie. Which destination would you like to explore (Hampi, Coorg, Dandeli, or Goa), and for how many days?"
        elif has_greeting and "duration_days" in missing and detected_dest_id:
            clarification = f"Hello! 👋 How many days would you like to spend in {detected_dest_id.title()}?"
        elif "destination" in missing and "duration_days" in missing:
            clarification = "Which destination would you like to visit (Hampi, Coorg, Dandeli, or Goa), and for how many days?"
        elif "destination" in missing:
            clarification = f"Which destination would you like to plan for (Hampi, Coorg, Dandeli, or Goa) for your {duration_days}-day trip?"
        elif "duration_days" in missing:
            clarification = f"How many days would you like to spend in {detected_dest_id.title()}?"

        return ExtractedTripConstraintsSchema(
            destination_id=detected_dest_id,
            destination_name=detected_dest_id.title() if detected_dest_id else None,
            duration_days=duration_days,
            total_budget=budget,
            party_size=party_size,
            interests=detected_interests if detected_interests else None,
            pace=pace,
            preferred_transport=transport,
            is_complete=(len(missing) == 0),
            missing_fields=missing,
            clarification_question=clarification,
            extraction_method="rule_based_fallback",
        )

    def extract_constraints(
        self, text: str, previous_constraints: Optional[ExtractedTripConstraintsSchema] = None
    ) -> ExtractedTripConstraintsSchema:
        """
        Extract trip constraints using rule-based parsing with contextual multi-turn merging.
        """
        extracted = self.extract_constraints_rule_based(text)
        has_greeting = self.is_greeting(text)

        # Contextually merge with previous session constraints if available
        if previous_constraints:
            merged_dest = extracted.destination_id or previous_constraints.destination_id
            merged_duration = extracted.duration_days or previous_constraints.duration_days
            merged_budget = extracted.total_budget or previous_constraints.total_budget
            merged_party = extracted.party_size or previous_constraints.party_size
            merged_interests = extracted.interests or previous_constraints.interests
            merged_pace = extracted.pace or previous_constraints.pace
            merged_transport = extracted.preferred_transport or previous_constraints.preferred_transport

            missing = []
            if not merged_dest:
                missing.append("destination")
            if not merged_duration:
                missing.append("duration_days")

            clarification = None
            if "destination" in missing and "duration_days" in missing:
                if has_greeting:
                    clarification = "Hello! 👋 Welcome to Travel Genie. Which destination would you like to explore (Hampi, Coorg, Dandeli, or Goa), and for how many days?"
                else:
                    clarification = "Which destination would you like to explore (Hampi, Coorg, Dandeli, or Goa), and for how many days?"
            elif "destination" in missing:
                clarification = f"Which destination would you like to explore (Hampi, Coorg, Dandeli, or Goa) for your {merged_duration}-day trip?"
            elif "duration_days" in missing:
                if has_greeting:
                    clarification = f"Hello! 👋 How many days will you be staying in {merged_dest.title()}?"
                else:
                    clarification = f"How many days will you be staying in {merged_dest.title()}?"

            return ExtractedTripConstraintsSchema(
                destination_id=merged_dest,
                destination_name=merged_dest.title() if merged_dest else None,
                duration_days=merged_duration,
                total_budget=merged_budget,
                party_size=merged_party,
                interests=merged_interests,
                pace=merged_pace,
                preferred_transport=merged_transport,
                is_complete=(len(missing) == 0),
                missing_fields=missing,
                clarification_question=clarification,
                extraction_method=extracted.extraction_method,
            )

        return extracted

    def generate_explanation(
        self,
        itinerary: MultiDayTripOptimizationResponse,
        replanning_diff: Optional[ReplanningDiffSchema] = None,
    ) -> str:
        """
        Generate rich, attractive, emoji-enhanced natural-language explanation summarizing
        the optimized schedule, transit savings, and replanning modifications.
        """
        lines = []

        if replanning_diff and replanning_diff.is_replanned:
            lines.append("🔄 **Smart Replanning Update**")
            lines.append("Here are the updates applied to your itinerary:")
            for change in replanning_diff.changed_constraints:
                lines.append(f"• **{change.field.replace('_', ' ').title()}**: Updated from `{change.old_value}` ➔ **{change.new_value}**")

            if replanning_diff.removed_attractions:
                lines.append("\n🚫 **Removed / Deferred Stops:**")
                for r in replanning_diff.removed_attractions:
                    lines.append(f"• **{r.name}**: {r.reason}")

            if replanning_diff.added_attractions:
                lines.append("\n✨ **Added Stops:**")
                for a in replanning_diff.added_attractions:
                    lines.append(f"• **{a.name}** (Day {a.day_number}): {a.reason}")

            lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        dest_title = itinerary.destination_id.title()
        lines.append(f"✨ 📍 **{dest_title} — {itinerary.total_days}-Day Optimized Itinerary** 🌴")
        lines.append(
            f"🎯 **{itinerary.total_scheduled_attractions} Sightseeing Visits** across **{itinerary.total_days} Days**\n"
            f"🚗 **Transit**: {itinerary.total_travel_distance_km:.1f} km road travel ({itinerary.total_travel_duration_hours:.2f}h transit | {itinerary.total_sightseeing_duration_hours:.1f}h sightseeing)\n"
            f"⚡ **Route Optimization**: **{itinerary.aggregate_distance_reduction_pct:.1f}% Distance Reduction** via OR-Tools TSP\n"
            f"💰 **Total Estimated Trip Cost**: **₹{itinerary.total_estimated_cost:,.2f}**"
        )

        # Summary of days
        for day in itinerary.days:
            lines.append(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"🗓️ **DAY {day.day_number}** ({day.day_start_time} - {day.day_end_time})")
            lines.append(
                f"🚕 **Transit Mode**: {day.recommended_transport.title()}  |  🛣️ **Day Travel**: {day.total_travel_distance_km:.1f} km ({day.total_travel_duration_hours:.2f}h)  |  📉 **Saved**: {day.optimization_metrics.distance_reduction_km:.2f} km ({day.optimization_metrics.distance_reduction_pct:.1f}%)"
            )
            lines.append("📍 **Planned Activities:**")
            for item in day.items:
                notes = f"🎟️ Fee: ₹{item.item_admission_fee:.0f}" if item.item_admission_fee > 0 else "🎟️ Free Entry"
                lines.append(
                    f"  {item.visit_order}. 🏛️ **{item.attraction.name}** [{item.arrival_time} - {item.departure_time}] ({notes})"
                )

        if itinerary.deferred_attractions:
            lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("⚠️ **DEFERRED STOPS (Daily Feasibility Protection)**")
            for d in itinerary.deferred_attractions:
                lines.append(f"• ⏳ **{d.attraction_name}**: {d.reason}")

        return "\n".join(lines)
