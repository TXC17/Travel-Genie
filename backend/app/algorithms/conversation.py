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
        "goa": ["goa", "north goa", "south goa", "panaji", "calangute"],
    }

    INTEREST_KEYWORDS = {
        "heritage": ["heritage", "history", "historical", "ancient", "monument", "temple", "ruins", "architecture"],
        "nature": ["nature", "scenic", "waterfall", "coffee", "plantation", "greenery", "hills", "reservoir", "lake"],
        "adventure": ["adventure", "rafting", "kayaking", "trekking", "trek", "safari", "wildlife", "camping", "water sports"],
        "religious": ["religious", "temple", "spiritual", "pilgrimage", "shrine", "sacred", "church"],
        "beach": ["beach", "sea", "ocean", "coastal", "sand", "sunset"],
    }

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL

    def extract_constraints_rule_based(self, text: str) -> ExtractedTripConstraintsSchema:
        """
        Deterministic regex/rule-based NLU fallback parser.
        """
        text_lower = text.lower()

        # 1. Extract Destination
        detected_dest_id = None
        for dest_id, aliases in self.KNOWN_DESTINATIONS.items():
            if any(alias in text_lower for alias in aliases):
                detected_dest_id = dest_id
                break

        # 2. Extract Duration (Days)
        duration_days = None
        day_match = re.search(r"(\d+)\s*(?:-|–|\s)?\s*(?:day|days|d)", text_lower)
        if day_match:
            duration_days = min(14, max(1, int(day_match.group(1))))
        elif "weekend" in text_lower:
            duration_days = 2
        elif "week" in text_lower:
            duration_days = 7

        # 3. Extract Budget
        budget = None
        budget_match = re.search(
            r"(?:rs\.?|inr|₹|budget(?:\s+of)?)\s*[:=]?\s*(\d+[\d,]*)(?:\s*k)?", text_lower
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

        # 4. Extract Party Size
        party_size = None
        party_match = re.search(
            r"(\d+)\s*(?:people|persons|travelers|travellers|friends|adults|members)", text_lower
        )
        if party_match:
            party_size = int(party_match.group(1))
        elif "solo" in text_lower:
            party_size = 1
        elif "couple" in text_lower:
            party_size = 2
        elif "family" in text_lower:
            party_size = 4

        # 5. Extract Interests
        detected_interests = []
        for tag, keywords in self.INTEREST_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                detected_interests.append(tag)

        # 6. Extract Pace
        pace = None
        if "relaxed" in text_lower or "slow" in text_lower or "leisure" in text_lower:
            pace = "Relaxed"
        elif "intense" in text_lower or "fast" in text_lower or "packed" in text_lower:
            pace = "Intense"
        elif "moderate" in text_lower or "balanced" in text_lower:
            pace = "Moderate"

        # 7. Extract Transport
        transport = None
        if "walking" in text_lower or "on foot" in text_lower:
            transport = "walking"
        elif "auto" in text_lower or "rickshaw" in text_lower or "tuk" in text_lower:
            transport = "auto"
        elif "car" in text_lower or "cab" in text_lower or "taxi" in text_lower:
            transport = "car"
        elif "rental" in text_lower or "bike" in text_lower or "scooter" in text_lower:
            transport = "rental"
        elif "public" in text_lower or "bus" in text_lower or "train" in text_lower:
            transport = "public"

        # Check completeness
        missing = []
        if not detected_dest_id:
            missing.append("destination")
        if not duration_days:
            missing.append("duration_days")

        clarification = None
        if "destination" in missing and "duration_days" in missing:
            clarification = "Which destination would you like to visit (Hampi, Coorg, Dandeli, or Goa), and for how many days?"
        elif "destination" in missing:
            clarification = "Which destination would you like to plan for (Hampi, Coorg, Dandeli, or Goa)?"
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
        Extract trip constraints using rule-based parsing with contextual merging.
        """
        # Parse new input
        extracted = self.extract_constraints_rule_based(text)

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
            if "destination" in missing:
                clarification = "Which destination would you like to explore (Hampi, Coorg, Dandeli, or Goa)?"
            elif "duration_days" in missing:
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
        Generate deterministic natural-language academic explanation summarizing the
        optimized schedule, transit savings, and replanning modifications.
        """
        lines = []

        if replanning_diff and replanning_diff.is_replanned:
            lines.append("### 🔄 Smart Replanning Update")
            lines.append("I have updated your itinerary according to your requested changes:")
            for change in replanning_diff.changed_constraints:
                lines.append(f"- **{change.field.replace('_', ' ').title()}**: Updated from `{change.old_value}` to `{change.new_value}`.")

            if replanning_diff.removed_attractions:
                lines.append("\n**Removed / Deferred Stops:**")
                for r in replanning_diff.removed_attractions:
                    lines.append(f"- *{r.name}*: {r.reason}")

            if replanning_diff.added_attractions:
                lines.append("\n**Added Stops:**")
                for a in replanning_diff.added_attractions:
                    lines.append(f"- *{a.name}* (Day {a.day_number}): {a.reason}")

            lines.append("\n---")

        lines.append(
            f"### 📍 {itinerary.destination_id.title()} {itinerary.total_days}-Day Optimized Itinerary"
        )
        lines.append(
            f"Generated **{itinerary.total_scheduled_attractions} sightseeing visits** across **{itinerary.total_days} days** "
            f"covering a total road transit distance of **{itinerary.total_travel_distance_km:.1f} km** "
            f"({itinerary.total_travel_duration_hours:.2f}h travel time, {itinerary.total_sightseeing_duration_hours:.1f}h sightseeing)."
        )
        lines.append(
            f"OR-Tools intra-day route optimization achieved an aggregate distance reduction of **{itinerary.aggregate_distance_reduction_pct:.1f}%** "
            f"over the unoptimized baseline sequence."
        )
        lines.append(f"**Total Estimated Trip Cost**: ₹{itinerary.total_estimated_cost:,.2f}")

        # Summary of days
        for day in itinerary.days:
            lines.append(f"\n#### Day {day.day_number} ({day.day_start_time} - {day.day_end_time})")
            lines.append(
                f"- **Transit Mode**: {day.recommended_transport.title()} | **Day Travel**: {day.total_travel_distance_km:.1f} km ({day.total_travel_duration_hours:.2f}h)"
            )
            lines.append(
                f"- **Optimization Savings**: Saved {day.optimization_metrics.distance_reduction_km:.2f} km ({day.optimization_metrics.distance_reduction_pct:.1f}%)"
            )
            for item in day.items:
                notes = f" (Admission: ₹{item.item_admission_fee:.0f})" if item.item_admission_fee > 0 else " (Free Entry)"
                lines.append(
                    f"  {item.visit_order}. **{item.attraction.name}** [{item.arrival_time} - {item.departure_time}]{notes}"
                )

        if itinerary.deferred_attractions:
            lines.append("\n#### ⚠️ Deferred Stops (Daily Feasibility Protection)")
            for d in itinerary.deferred_attractions:
                lines.append(f"- **{d.attraction_name}**: {d.reason}")

        return "\n".join(lines)
