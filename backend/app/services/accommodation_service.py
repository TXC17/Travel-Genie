"""
Deterministic Accommodation Recommendation Service.
Provides multi-criteria ranking, room capacity calculations,
strict stay date validation, transparent multi-category budget accounting,
and explainable stay recommendations.
"""

import json
import math
from datetime import date
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.accommodation import Accommodation
from app.models.destination import Destination
from app.schemas.accommodation import (
    AccommodationResponse,
    AccommodationRecommendationRequest,
    AccommodationRecommendationItem,
    AccommodationBudgetContext,
    AccommodationRecommendationResponse,
)


def get_data_dir() -> Path:
    """Resolve absolute path to project data directory."""
    backend_dir = Path(__file__).resolve().parent.parent.parent
    root_data_dir = backend_dir.parent / "data"
    if root_data_dir.exists():
        return root_data_dir
    local_data_dir = backend_dir / "data"
    if local_data_dir.exists():
        return local_data_dir
    raise FileNotFoundError("Could not locate data directory")


class AccommodationService:
    @staticmethod
    def _load_fallback_accommodations(destination_id: str) -> List[Dict[str, Any]]:
        """Load curated benchmark accommodations from JSON if database table is unpopulated."""
        try:
            data_dir = get_data_dir()
            acc_file = data_dir / "accommodations.json"
            if acc_file.exists():
                with open(acc_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return [
                        item for item in data
                        if item.get("destination_id", "").lower() == destination_id.lower()
                        and item.get("is_active", True)
                    ]
        except Exception:
            pass
        return []

    @classmethod
    def get_accommodations_for_destination(
        cls,
        db: Session,
        destination_id: str,
        budget_tier: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_price_per_night: Optional[float] = None,
        accommodation_type: Optional[str] = None,
    ) -> List[AccommodationResponse]:
        """Fetch filtered accommodations from DB or fallback JSON."""
        dest_norm = destination_id.strip().lower()
        query = db.query(Accommodation).filter(
            Accommodation.destination_id == dest_norm,
            Accommodation.is_active == True,
        )

        if min_rating is not None:
            query = query.filter(Accommodation.rating >= min_rating)
        if max_price_per_night is not None:
            query = query.filter(Accommodation.price_per_night <= max_price_per_night)
        if accommodation_type is not None:
            query = query.filter(Accommodation.accommodation_type.ilike(f"%{accommodation_type}%"))

        db_records = query.all()

        if db_records:
            results = [AccommodationResponse.model_validate(r) for r in db_records]
        else:
            # Fallback to curated JSON file
            raw_data = cls._load_fallback_accommodations(dest_norm)
            results = []
            for item in raw_data:
                if min_rating is not None and item.get("rating", 0) < min_rating:
                    continue
                if max_price_per_night is not None and item.get("price_per_night", 0) > max_price_per_night:
                    continue
                if accommodation_type is not None and accommodation_type.lower() not in item.get("accommodation_type", "").lower():
                    continue
                results.append(AccommodationResponse(**item))

        # Filter by budget tier if requested
        if budget_tier:
            tier_upper = budget_tier.upper()
            filtered = []
            for r in results:
                price = r.price_per_night
                if tier_upper == "BUDGET" and price <= 3200:
                    filtered.append(r)
                elif tier_upper == "STANDARD" and 2200 <= price <= 8000:
                    filtered.append(r)
                elif tier_upper == "LUXURY" and price >= 6000:
                    filtered.append(r)
            if filtered:
                results = filtered

        return results

    @classmethod
    def get_accommodation_by_id(cls, db: Session, accommodation_id: str) -> Optional[AccommodationResponse]:
        """Retrieve single accommodation by ID."""
        record = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()
        if record:
            return AccommodationResponse.model_validate(record)

        # Fallback search in JSON
        try:
            data_dir = get_data_dir()
            acc_file = data_dir / "accommodations.json"
            if acc_file.exists():
                with open(acc_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        if item.get("id") == accommodation_id:
                            return AccommodationResponse(**item)
        except Exception:
            pass
        return None

    @classmethod
    def get_recommendations(
        cls,
        db: Session,
        request: AccommodationRecommendationRequest,
    ) -> AccommodationRecommendationResponse:
        """
        Deterministic multi-criteria accommodation recommendation engine.
        Calculates nights, required rooms, total stay cost, budget fit, and transparent explanations.
        Validates date ranges strictly (at least 1 night) and accounts for budget components accurately.
        """
        dest_norm = request.destination_id.strip().lower()

        # Destination display name
        dest_obj = db.query(Destination).filter(Destination.id == dest_norm).first()
        destination_name = dest_obj.name if dest_obj else dest_norm.title()

        # 1. Strict stay duration & nights validation
        try:
            d_in = date.fromisoformat(str(request.check_in_date))
            d_out = date.fromisoformat(str(request.check_out_date))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Dates must be in valid ISO YYYY-MM-DD format: {exc}")

        delta_days = (d_out - d_in).days
        if delta_days <= 0:
            raise ValueError(
                f"Invalid date range: check_out_date ({request.check_out_date}) must be strictly after "
                f"check_in_date ({request.check_in_date}). A lodging stay must include at least one night."
            )
        nights = delta_days

        # 2. Fetch candidates
        candidates = cls.get_accommodations_for_destination(
            db=db,
            destination_id=dest_norm,
            budget_tier=request.budget_tier,
            min_rating=request.min_rating,
            max_price_per_night=request.max_price_per_night,
            accommodation_type=request.preferred_type,
        )

        # If strict filtering produced nothing, relax filters to provide options
        if not candidates:
            candidates = cls.get_accommodations_for_destination(
                db=db,
                destination_id=dest_norm,
            )

        # 3. Determine budget tier & allocation limit
        party_size = max(request.party_size, 1)
        budget_tier = request.budget_tier or "Standard"

        if request.total_budget:
            daily_per_person = request.total_budget / (party_size * nights)
            if not request.budget_tier:
                if daily_per_person < 2500:
                    budget_tier = "Budget"
                elif daily_per_person > 7000:
                    budget_tier = "Luxury"
                else:
                    budget_tier = "Standard"

            tier_target_pct = {
                "Budget": 0.30,
                "Standard": 0.40,
                "Luxury": 0.50,
            }.get(budget_tier, 0.35)

            allocated_budget = request.accommodation_budget or (request.total_budget * tier_target_pct)
        elif request.accommodation_budget:
            allocated_budget = request.accommodation_budget
        else:
            allocated_budget = None

        # Cost category tracking
        transit_cost = (
            request.intercity_transport_cost
            if request.intercity_transport_cost is not None and request.intercity_transport_cost > 0
            else 0.0
        )
        included_categories = ["accommodation"]
        if transit_cost > 0:
            included_categories.append("intercity_transport")
        excluded_categories = ["local_intraday_transit", "attraction_admissions", "meals_and_incidentals"]

        recommendation_items: List[AccommodationRecommendationItem] = []

        # 4. Multi-criteria evaluation for each candidate
        for acc in candidates:
            # Capacity & Rooms needed based strictly on property room capacity
            capacity = max(acc.room_capacity, 1)
            rooms_needed = max(1, math.ceil(party_size / capacity))
            total_cost = nights * acc.price_per_night * rooms_needed
            total_accounted = total_cost + transit_cost

            # Budget analysis
            if allocated_budget is not None and allocated_budget > 0:
                is_within_budget = total_cost <= allocated_budget
                if is_within_budget:
                    ratio = total_cost / allocated_budget
                    budget_fit_score = round(max(0.70, 1.0 - abs(0.85 - ratio) * 0.3), 3)
                else:
                    overage_ratio = (total_cost - allocated_budget) / allocated_budget
                    budget_fit_score = round(max(0.10, 1.0 - min(overage_ratio, 1.0) * 0.8), 3)
            elif request.total_budget is not None and request.total_budget > 0:
                is_within_budget = total_cost <= request.total_budget
                budget_fit_score = 0.85 if is_within_budget else 0.20
            else:
                is_within_budget = True
                budget_fit_score = 0.85

            # Rating score
            rating_score = round(min(max(acc.rating / 5.0, 0.0), 1.0), 3)

            # Amenities score
            if request.required_amenities:
                req_lower = [req.lower().strip() for req in request.required_amenities]
                acc_amenities_lower = [am.lower() for am in acc.amenities]
                matches = sum(1 for req in req_lower if any(req in am for am in acc_amenities_lower))
                amenities_score = round(matches / len(request.required_amenities), 3)
            else:
                amenities_score = round(min(1.0, len(acc.amenities) / 6.0), 3)

            # Type score
            if request.preferred_type:
                type_match = request.preferred_type.lower() in acc.accommodation_type.lower()
                type_score = 1.0 if type_match else 0.5
            else:
                type_score = 1.0

            # Provenance score (verified property gets higher trust)
            provenance_score = 1.0 if acc.is_verified else 0.65

            # Composite match score: weights (0.35 budget, 0.25 rating, 0.20 amenities, 0.10 type, 0.10 provenance)
            match_score = round(
                0.35 * budget_fit_score
                + 0.25 * rating_score
                + 0.20 * amenities_score
                + 0.10 * type_score
                + 0.10 * provenance_score,
                3,
            )

            # Multi-category budget calculations
            remaining_after_acc = (
                (request.total_budget - total_cost) if request.total_budget is not None else None
            )
            remaining_budget = (
                (request.total_budget - total_accounted) if request.total_budget is not None else None
            )
            budget_utilization_pct = (
                round((total_accounted / request.total_budget) * 100, 1)
                if request.total_budget is not None and request.total_budget > 0
                else None
            )

            # Explainable match reasons
            reasons = []
            if rooms_needed == 1:
                reasons.append(
                    f"1 room for {party_size} guest{'s' if party_size > 1 else ''} across {nights} night{'s' if nights > 1 else ''} "
                    f"(₹{acc.price_per_night:,.0f}/night benchmark)"
                )
            else:
                reasons.append(
                    f"{rooms_needed} rooms required for {party_size} guests ({capacity} guests/room) across {nights} night{'s' if nights > 1 else ''}"
                )

            if is_within_budget and allocated_budget:
                reasons.append(
                    f"Fits within target lodging budget (₹{total_cost:,.0f} of ₹{allocated_budget:,.0f} allocated)"
                )
            elif not is_within_budget and allocated_budget:
                reasons.append(
                    f"Exceeds target lodging allocation by ₹{(total_cost - allocated_budget):,.0f}"
                )

            if remaining_budget is not None:
                if remaining_budget >= 0:
                    if transit_cost > 0:
                        reasons.append(
                            f"Leaves ₹{remaining_budget:,.0f} after lodging (₹{total_cost:,.0f}) and transit (₹{transit_cost:,.0f}) for attractions and dining"
                        )
                    else:
                        reasons.append(
                            f"Leaves ₹{remaining_budget:,.0f} after lodging for transit, attractions, and dining"
                        )
                else:
                    reasons.append(
                        f"Over total trip budget by ₹{abs(remaining_budget):,.0f}"
                    )

            reasons.append(f"{acc.rating:.1f}★ rated with {len(acc.amenities)} curated amenities")

            if acc.is_verified:
                source_name = acc.provenance.get("source", "Official Tourism Registry")
                reasons.append(f"Verified physical property ({source_name})")
            else:
                reasons.append("Estimated regional benchmark property")

            badge = acc.provenance.get("provenance_badge", "VERIFIED" if acc.is_verified else "ESTIMATED")

            booking_note = (
                f"Official booking available via {acc.booking_url}"
                if acc.booking_url
                else "Direct local booking and reception inquiry recommended"
            )

            recommendation_items.append(
                AccommodationRecommendationItem(
                    accommodation=acc,
                    nights=nights,
                    rooms_needed=rooms_needed,
                    price_per_night=acc.price_per_night,
                    total_cost=total_cost,
                    intercity_transport_cost=request.intercity_transport_cost,
                    total_accounted_cost=total_accounted,
                    budget_fit_score=budget_fit_score,
                    remaining_budget=remaining_budget,
                    remaining_budget_after_accommodation=remaining_after_acc,
                    budget_utilization_pct=budget_utilization_pct,
                    is_within_budget=is_within_budget,
                    match_score=match_score,
                    match_reasons=reasons,
                    provenance_badge=badge,
                    included_cost_categories=included_categories,
                    excluded_cost_categories=excluded_categories,
                    is_estimate_complete=False,
                    booking_note=booking_note,
                )
            )

        # Sort recommendations by match_score descending
        recommendation_items.sort(key=lambda item: item.match_score, reverse=True)

        # Summary generation
        top_name = recommendation_items[0].accommodation.name if recommendation_items else "lodging options"
        top_cost = recommendation_items[0].total_cost if recommendation_items else 0.0

        if allocated_budget:
            summary = (
                f"Found {len(recommendation_items)} authentic accommodation option(s) in {destination_name} for "
                f"{nights} night(s) and {party_size} traveler(s). Target lodging budget: ₹{allocated_budget:,.0f} "
                f"({budget_tier} tier). Top recommended: {top_name} at ₹{top_cost:,.0f} total."
            )
        else:
            summary = (
                f"Found {len(recommendation_items)} authentic accommodation option(s) in {destination_name} for "
                f"{nights} night(s) and {party_size} traveler(s). Top recommended: {top_name} at ₹{top_cost:,.0f} total."
            )

        # Room capacity for response-level context:
        # Match top recommended accommodation capacity, with fallback to standard double room capacity
        top_rooms = (
            recommendation_items[0].rooms_needed
            if recommendation_items
            else max(1, math.ceil(party_size / 2))
        )
        standard_rooms_est = max(1, math.ceil(party_size / 2))

        budget_ctx = AccommodationBudgetContext(
            total_budget=request.total_budget,
            allocated_accommodation_budget=allocated_budget,
            budget_tier=budget_tier,
            nights=nights,
            party_size=party_size,
            rooms_needed=top_rooms,
            standard_double_rooms_estimate=standard_rooms_est,
            intercity_transport_cost=request.intercity_transport_cost,
            total_accounted_cost=(top_cost + transit_cost) if recommendation_items else None,
            included_cost_categories=included_categories,
            excluded_cost_categories=excluded_categories,
            is_estimate_complete=False,
        )

        return AccommodationRecommendationResponse(
            destination_id=dest_norm,
            destination_name=destination_name,
            check_in_date=request.check_in_date,
            check_out_date=request.check_out_date,
            nights=nights,
            party_size=party_size,
            rooms_needed=top_rooms,
            budget_context=budget_ctx,
            recommendations=recommendation_items,
            summary=summary,
        )
