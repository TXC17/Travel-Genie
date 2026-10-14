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
    ROAD_WINDING_FACTOR = 1.30

    @classmethod
    def calculate_estimated_road_distance(
        cls, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Estimate road distance in kilometers using Haversine formula
        multiplied by empirical ROAD_WINDING_FACTOR = 1.30.
        """
        if lat1 == lat2 and lon1 == lon2:
            return 0.0
        R = 6371.0  # Earth radius km
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = (
            math.sin(dphi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
        return round(R * c * cls.ROAD_WINDING_FACTOR, 3)

    @classmethod
    def _extract_itinerary_day_waypoints(
        cls, db: Session, request: AccommodationRecommendationRequest
    ) -> List[List[Dict[str, Any]]]:
        """
        Extract ordered attraction coordinates per day from either:
        1. request.itinerary_days (passed directly from client or pipeline)
        2. request.itinerary_id (queried from DB)
        3. request.trip_id (queried from DB)
        Returns a list of days, where each day is a list of attraction dicts with 'latitude', 'longitude', 'name'.
        """
        day_waypoints: List[List[Dict[str, Any]]] = []

        if request.itinerary_days:
            for day in request.itinerary_days:
                items = day.get("items") or []
                ordered_attrs = day.get("ordered_attractions") or []
                day_coords = []
                if items:
                    for item in sorted(items, key=lambda x: x.get("visit_order", 0)):
                        attr = item.get("attraction") or {}
                        lat = attr.get("latitude")
                        lon = attr.get("longitude")
                        if lat is not None and lon is not None:
                            day_coords.append({
                                "latitude": float(lat),
                                "longitude": float(lon),
                                "name": attr.get("name", "Attraction"),
                            })
                elif ordered_attrs:
                    for attr in ordered_attrs:
                        lat = attr.get("latitude")
                        lon = attr.get("longitude")
                        if lat is not None and lon is not None:
                            day_coords.append({
                                "latitude": float(lat),
                                "longitude": float(lon),
                                "name": attr.get("name", "Attraction"),
                            })
                if day_coords:
                    day_waypoints.append(day_coords)

        if not day_waypoints and (request.itinerary_id or request.trip_id):
            from app.models.itinerary import Itinerary

            itin = None
            if request.itinerary_id:
                itin = db.query(Itinerary).filter(Itinerary.id == request.itinerary_id).first()
            if not itin and request.trip_id:
                itin = (
                    db.query(Itinerary)
                    .filter(Itinerary.trip_id == request.trip_id)
                    .order_by(Itinerary.created_at.desc())
                    .first()
                )

            if itin and itin.days:
                for d in sorted(itin.days, key=lambda x: x.day_number):
                    day_coords = []
                    for item in sorted(d.items, key=lambda x: x.visit_order):
                        if (
                            item.attraction
                            and item.attraction.latitude is not None
                            and item.attraction.longitude is not None
                        ):
                            day_coords.append({
                                "latitude": float(item.attraction.latitude),
                                "longitude": float(item.attraction.longitude),
                                "name": item.attraction.name,
                            })
                    if day_coords:
                        day_waypoints.append(day_coords)

        return day_waypoints

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
    def normalize_category(cls, category: Optional[str]) -> Optional[str]:
        """Normalize category filter key."""
        if not category:
            return None
        c = category.strip().lower()
        if c in ("all", "all stays", "*", "any"):
            return "all"
        if c in ("ultra_luxury", "ultra-luxury", "luxury", "ultraluxury"):
            return "ultra_luxury"
        if c in ("ultra_budget", "ultra-budget", "budget", "ultrabudget"):
            return "ultra_budget"
        if c in ("moderate", "mid_range", "mid-range", "moderate / mid-range", "standard"):
            return "moderate"
        return c

    @classmethod
    def get_accommodations_for_destination(
        cls,
        db: Session,
        destination_id: str,
        budget_tier: Optional[str] = None,
        category: Optional[str] = None,
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
                if min_rating is not None and item.get("rating") is not None and item.get("rating", 0) < min_rating:
                    continue
                if max_price_per_night is not None and item.get("price_per_night", 0) > max_price_per_night:
                    continue
                if accommodation_type is not None and accommodation_type.lower() not in item.get("accommodation_type", "").lower():
                    continue
                results.append(AccommodationResponse(**item))

        # Filter by category if requested
        if category:
            cat_norm = cls.normalize_category(category)
            if cat_norm == "ultra_luxury":
                results = [r for r in results if r.category == "Ultra-Luxury"]
            elif cat_norm == "ultra_budget":
                results = [r for r in results if r.category == "Ultra-Budget"]
            elif cat_norm == "moderate":
                results = [r for r in results if r.category == "Moderate / Mid-Range"]
        elif budget_tier:
            # Filter by legacy budget tier if requested
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

        # 2. Category normalization & candidate fetching
        category_filter = request.category or request.budget_tier
        norm_cat = cls.normalize_category(category_filter) or "all"

        candidates = cls.get_accommodations_for_destination(
            db=db,
            destination_id=dest_norm,
            category=request.category,
            budget_tier=request.budget_tier if not request.category else None,
            min_rating=request.min_rating,
            max_price_per_night=request.max_price_per_night,
            accommodation_type=request.preferred_type,
        )

        # Dataset depth and status explanation
        category_data_status = None
        if norm_cat == "ultra_luxury":
            if len(candidates) == 1:
                category_data_status = (
                    f"Curated dataset currently contains 1 verified Ultra-Luxury benchmark property for {destination_name}. "
                    f"Additional 5-star resort/palace benchmarks require verified regional tariff data."
                )
            elif len(candidates) == 0:
                category_data_status = f"No verified accommodation records found in the Ultra-Luxury category for {destination_name}."
        elif norm_cat == "ultra_budget":
            if len(candidates) == 0:
                category_data_status = f"No verified accommodation records found in the Ultra-Budget category for {destination_name}."
            elif len(candidates) <= 2:
                category_data_status = f"Curated dataset contains {len(candidates)} verified Ultra-Budget property/properties for {destination_name}."
        elif norm_cat == "moderate":
            if len(candidates) == 0:
                category_data_status = f"No verified accommodation records found in the Moderate / Mid-Range category for {destination_name}."

        # If strict filtering produced nothing and user did not specify a category or tier, relax filters
        if not candidates and norm_cat == "all" and not request.budget_tier:
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

        # Multi-day itinerary spatial suitability precomputation
        day_waypoints = cls._extract_itinerary_day_waypoints(db, request)
        is_itinerary_aware = len(day_waypoints) > 0

        # Calculate intra-day attraction distance across all days (fixed baseline)
        total_intra_attraction_km = 0.0
        activity_centroid: Optional[Dict[str, float]] = None
        acc_dist_to_center_map: Dict[str, Optional[float]] = {}

        if is_itinerary_aware:
            all_attr_coords = [attr for day in day_waypoints for attr in day]
            if all_attr_coords:
                c_lat = sum(a["latitude"] for a in all_attr_coords) / len(all_attr_coords)
                c_lon = sum(a["longitude"] for a in all_attr_coords) / len(all_attr_coords)
                activity_centroid = {
                    "latitude": round(c_lat, 6),
                    "longitude": round(c_lon, 6),
                }

            for day_coords in day_waypoints:
                for k in range(len(day_coords) - 1):
                    total_intra_attraction_km += cls.calculate_estimated_road_distance(
                        day_coords[k]["latitude"],
                        day_coords[k]["longitude"],
                        day_coords[k + 1]["latitude"],
                        day_coords[k + 1]["longitude"],
                    )

        # Precompute hotel transit and activity centroid distance for all candidates to compute relative ranking
        acc_transit_map: Dict[str, float] = {}
        if is_itinerary_aware:
            for acc in candidates:
                if acc.latitude is not None and acc.longitude is not None:
                    # Centroid road distance (itinerary activity center)
                    if activity_centroid:
                        d_centroid = cls.calculate_estimated_road_distance(
                            acc.latitude,
                            acc.longitude,
                            activity_centroid["latitude"],
                            activity_centroid["longitude"],
                        )
                        acc_dist_to_center_map[acc.id] = round(d_centroid, 1)
                    else:
                        acc_dist_to_center_map[acc.id] = None

                    hotel_transit = 0.0
                    for day_coords in day_waypoints:
                        first_attr = day_coords[0]
                        last_attr = day_coords[-1]
                        d_origin = cls.calculate_estimated_road_distance(
                            acc.latitude, acc.longitude, first_attr["latitude"], first_attr["longitude"]
                        )
                        d_return = cls.calculate_estimated_road_distance(
                            last_attr["latitude"], last_attr["longitude"], acc.latitude, acc.longitude
                        )
                        hotel_transit += (d_origin + d_return)
                    acc_transit_map[acc.id] = round(hotel_transit, 2)
                else:
                    acc_transit_map[acc.id] = 999.0
                    acc_dist_to_center_map[acc.id] = None

            valid_transits = [v for v in acc_transit_map.values() if v < 900.0]
            min_hotel_transit = min(valid_transits) if valid_transits else 0.0
            max_hotel_transit = max(valid_transits) if valid_transits else 0.0
        else:
            min_hotel_transit = 0.0
            max_hotel_transit = 0.0

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

            # Rating score (Honest: neutral 0.70 if unrated, never assume 5.0 or 0.0)
            has_valid_rating = acc.rating is not None and acc.rating > 0.0
            if has_valid_rating:
                rating_score = round(min(max(acc.rating / 5.0, 0.0), 1.0), 3)
            else:
                rating_score = 0.70

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

            # Location Suitability Scoring (Itinerary-Aware across all days)
            if (
                is_itinerary_aware
                and acc.id in acc_transit_map
                and acc.latitude is not None
                and acc.longitude is not None
            ):
                total_transit_km = acc_transit_map[acc.id]
                avg_daily_transit_km = round(total_transit_km / max(1, len(day_waypoints)), 1)
                dist_to_activity_center = acc_dist_to_center_map.get(acc.id)
                total_trip_km = round(total_intra_attraction_km + total_transit_km, 1)
                savings_km = round(max(0.0, max_hotel_transit - total_transit_km), 1)

                transit_range = max_hotel_transit - min_hotel_transit
                rel_score = (
                    1.0 - ((total_transit_km - min_hotel_transit) / transit_range)
                    if transit_range > 0.0
                    else 1.0
                )
                abs_score = 1.0 / (1.0 + (avg_daily_transit_km / 25.0))
                if dist_to_activity_center is not None:
                    centroid_score = 1.0 / (1.0 + (dist_to_activity_center / 20.0))
                    location_score = round(
                        min(1.0, max(0.05, 0.50 * rel_score + 0.30 * abs_score + 0.20 * centroid_score)), 3
                    )
                else:
                    location_score = round(
                        min(1.0, max(0.05, 0.60 * rel_score + 0.40 * abs_score)), 3
                    )

                if dist_to_activity_center is not None and dist_to_activity_center <= 8.0:
                    loc_explanation = (
                        f"Central to your planned activities: ~{dist_to_activity_center} km from itinerary activity center, "
                        f"estimated ~{avg_daily_transit_km} km/day round-trip transit (saves ~{savings_km} km total vs outlying options)."
                    )
                elif dist_to_activity_center is not None:
                    loc_explanation = (
                        f"~{dist_to_activity_center} km from your itinerary activity center: estimated ~{avg_daily_transit_km} km/day "
                        f"round-trip transit across planned itinerary days."
                    )
                elif avg_daily_transit_km <= 15.0:
                    loc_explanation = (
                        f"Centrally located for this itinerary: estimated ~{avg_daily_transit_km} km/day round-trip transit "
                        f"to daily waypoints (saves ~{savings_km} km total vs outlying options)."
                    )
                elif avg_daily_transit_km <= 35.0:
                    loc_explanation = (
                        f"Moderate transit distance: requires estimated ~{avg_daily_transit_km} km/day round-trip transit "
                        f"to planned itinerary waypoints."
                    )
                else:
                    loc_explanation = (
                        f"Peripheral location / dispersed attractions: requires estimated ~{avg_daily_transit_km} km/day "
                        f"round-trip transit across planned itinerary days."
                    )
            elif is_itinerary_aware:
                total_transit_km = None
                avg_daily_transit_km = None
                dist_to_activity_center = None
                total_trip_km = None
                savings_km = None
                location_score = 0.5
                loc_explanation = "Location coordinates unavailable for spatial routing analysis."
            else:
                total_transit_km = None
                avg_daily_transit_km = None
                dist_to_activity_center = None
                total_trip_km = None
                savings_km = None
                location_score = None
                loc_explanation = None

            # Category-specific composite match score
            acc_cat = acc.category
            if acc_cat == "Ultra-Luxury":
                if is_itinerary_aware and location_score is not None:
                    # Ultra-Luxury weights: Quality/Rating (0.25), Amenities (0.25), Location (0.25), Budget/Stay Cost (0.15), Provenance (0.10)
                    match_score = round(
                        0.25 * rating_score
                        + 0.25 * amenities_score
                        + 0.25 * location_score
                        + 0.15 * budget_fit_score
                        + 0.10 * provenance_score,
                        3,
                    )
                else:
                    match_score = round(
                        0.35 * rating_score
                        + 0.30 * amenities_score
                        + 0.15 * budget_fit_score
                        + 0.10 * provenance_score
                        + 0.10 * type_score,
                        3,
                    )
            elif acc_cat == "Ultra-Budget":
                # Affordability benchmark: lower price_per_night receives higher affordability score
                affordability_score = round(min(1.0, max(0.2, 1.0 - (acc.price_per_night - 1000.0) / 3000.0)), 3)
                combined_budget_score = round(0.60 * budget_fit_score + 0.40 * affordability_score, 3)
                if is_itinerary_aware and location_score is not None:
                    # Ultra-Budget weights: Affordability (0.40), Location/Transit (0.25), Rating/Quality (0.20), Amenities (0.10), Provenance (0.05)
                    match_score = round(
                        0.40 * combined_budget_score
                        + 0.25 * location_score
                        + 0.20 * rating_score
                        + 0.10 * amenities_score
                        + 0.05 * provenance_score,
                        3,
                    )
                else:
                    match_score = round(
                        0.45 * combined_budget_score
                        + 0.25 * rating_score
                        + 0.15 * amenities_score
                        + 0.10 * provenance_score
                        + 0.05 * type_score,
                        3,
                    )
            else:
                # Moderate / Mid-Range (balanced)
                if is_itinerary_aware and location_score is not None:
                    match_score = round(
                        0.30 * budget_fit_score
                        + 0.25 * location_score
                        + 0.20 * rating_score
                        + 0.15 * amenities_score
                        + 0.05 * type_score
                        + 0.05 * provenance_score,
                        3,
                    )
                else:
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
            reasons.append(
                f"Category: {acc.category} ({acc.accommodation_type.title()}) — {rooms_needed} room{'s' if rooms_needed > 1 else ''} for {party_size} traveler{'s' if party_size > 1 else ''} across {nights} night{'s' if nights > 1 else ''}"
            )
            reasons.append(
                f"Estimated tariff: ₹{acc.price_per_night:,.0f}/night benchmark (estimated total stay: ₹{total_cost:,.0f})"
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

            if has_valid_rating:
                if acc.review_count:
                    reasons.append(f"{acc.rating:.1f}★ rating based on {acc.review_count} documented guest reviews")
                else:
                    reasons.append(f"{acc.rating:.1f}★ documented guest rating")
            else:
                reasons.append("Guest ratings unavailable (scored on verified tariff and documented amenities)")

            reasons.append(f"{len(acc.amenities)} documented amenities: {', '.join(acc.amenities[:4])}{'...' if len(acc.amenities) > 4 else ''}")

            if acc.is_verified:
                source_name = acc.provenance.get("source", "Official Tourism Registry")
                reasons.append(f"Verified physical property ({source_name})")
            else:
                reasons.append("Estimated regional benchmark property")

            if loc_explanation:
                reasons.append(loc_explanation)

            # Category-specific rationale
            if acc.category == "Ultra-Luxury":
                reasons.append(f"Recommended for premium luxury hospitality, resort/heritage setting, and curated amenities ({', '.join(acc.amenities[:3])})")
            elif acc.category == "Ultra-Budget":
                reasons.append(f"Recommended for outstanding affordability (₹{acc.price_per_night:,.0f}/night) and transit efficiency")
            else:
                reasons.append("Recommended for balanced comfort, verified pricing, and convenient proximity to planned activities")

            badge = acc.provenance.get("provenance_badge", "VERIFIED" if acc.is_verified else "ESTIMATED")

            booking_note = (
                f"Official booking available via {acc.booking_url}"
                if acc.booking_url
                else "Direct local booking and reception inquiry recommended"
            )

            recommendation_items.append(
                AccommodationRecommendationItem(
                    accommodation=acc,
                    category=acc.category,
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
                    location_suitability_score=location_score,
                    estimated_distance_to_activity_center_km=dist_to_activity_center,
                    estimated_total_hotel_transit_km=total_transit_km,
                    estimated_daily_hotel_transit_km=avg_daily_transit_km,
                    estimated_trip_travel_distance_km=total_trip_km,
                    location_explanation=loc_explanation,
                    distance_reduction_vs_max_km=savings_km,
                    provenance_distance_method="haversine_with_road_winding_factor",
                    road_winding_factor=cls.ROAD_WINDING_FACTOR,
                )
            )

        # Sort recommendations by match_score descending
        recommendation_items.sort(key=lambda item: item.match_score, reverse=True)

        # Summary generation
        top_name = recommendation_items[0].accommodation.name if recommendation_items else "lodging options"
        top_cost = recommendation_items[0].total_cost if recommendation_items else 0.0

        if is_itinerary_aware:
            summary = (
                f"Found {len(recommendation_items)} authentic accommodation option(s) in {destination_name} for "
                f"{nights} night(s) and {party_size} traveler(s), ranked by itinerary location centrality across "
                f"{len(day_waypoints)} planned day(s). Top recommended: {top_name} at ₹{top_cost:,.0f} total."
            )
        elif allocated_budget:
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

        selected_cat_display = {
            "ultra_luxury": "Ultra-Luxury",
            "ultra_budget": "Ultra-Budget",
            "moderate": "Moderate / Mid-Range",
        }.get(norm_cat, "All Stays")

        budget_ctx = AccommodationBudgetContext(
            total_budget=request.total_budget,
            allocated_accommodation_budget=allocated_budget,
            budget_tier=budget_tier,
            selected_category=selected_cat_display,
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
            is_itinerary_aware=is_itinerary_aware,
            total_itinerary_days_evaluated=len(day_waypoints) if is_itinerary_aware else None,
            activity_center_coordinates=activity_centroid,
            category_filter=norm_cat,
            category_data_status=category_data_status,
        )
