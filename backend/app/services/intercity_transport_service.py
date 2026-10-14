"""
Deterministic Intercity Transportation Recommendation and Comparison Service.
Evaluates Car, Bike, Bus, Train, Flight, and Boat with transparent pricing,
duration estimation, group suitability, and budget compatibility.
"""

import json
import math
import os
import re
from typing import Dict, List, Optional, Tuple, Any
from app.schemas.transport import (
    TransportModeEnum,
    VerificationStatusEnum,
    BudgetCompatibilityEnum,
    IntercityOptionSchema,
    IntercityRecommendationRequest,
    IntercityRecommendationResponse,
)
from app.core.exceptions import TravelGenieException


class IntercityTransportService:
    """
    Evaluates, ranks, and explains intercity travel mode recommendations.
    Maintains strict separation between intercity transit and intra-city sightseeing routes.
    """

    EARTH_RADIUS_KM = 6371.0088
    ROAD_DETOUR_FACTOR = 1.30  # Standard regional detour coefficient for non-highway straight-line approximations

    KNOWN_ORIGIN_HUBS: Dict[str, Tuple[float, float, str]] = {
        "bengaluru": (12.9716, 77.5946, "Bengaluru"),
        "bangalore": (12.9716, 77.5946, "Bengaluru"),
        "mysuru": (12.2958, 76.6394, "Mysuru"),
        "mysore": (12.2958, 76.6394, "Mysuru"),
        "mangaluru": (12.9141, 74.8560, "Mangaluru"),
        "mangalore": (12.9141, 74.8560, "Mangaluru"),
        "hubballi": (15.3647, 75.1240, "Hubballi"),
        "hubli": (15.3647, 75.1240, "Hubballi"),
        "belagavi": (15.8497, 74.4977, "Belagavi"),
        "belgaum": (15.8497, 74.4977, "Belagavi"),
        "pune": (18.5204, 73.8567, "Pune"),
        "mumbai": (19.0760, 72.8777, "Mumbai"),
        "bombay": (19.0760, 72.8777, "Mumbai"),
        "hyderabad": (17.3850, 78.4867, "Hyderabad"),
        "chennai": (13.0827, 80.2707, "Chennai"),
        "madras": (13.0827, 80.2707, "Chennai"),
        "panaji": (15.4989, 73.8278, "Panaji"),
        "goa": (15.4989, 73.8278, "Goa"),
        "dharwad": (15.4589, 75.0078, "Dharwad"),
        "shivamogga": (13.9299, 75.5681, "Shivamogga"),
        "shimoga": (13.9299, 75.5681, "Shivamogga"),
        "coimbatore": (11.0168, 76.9558, "Coimbatore"),
        "kochi": (9.9312, 76.2673, "Kochi"),
        "delhi": (28.6139, 77.2090, "Delhi"),
        "new delhi": (28.6139, 77.2090, "Delhi"),
    }

    DESTINATION_ALIASES: Dict[str, Tuple[str, float, float, str]] = {
        "hampi": ("hampi", 15.3350, 76.4600, "Hampi"),
        "coorg": ("coorg", 12.4244, 75.7382, "Coorg (Madikeri)"),
        "kodagu": ("coorg", 12.4244, 75.7382, "Coorg (Madikeri)"),
        "madikeri": ("coorg", 12.4244, 75.7382, "Coorg (Madikeri)"),
        "dandeli": ("dandeli", 15.2361, 74.6173, "Dandeli"),
        "goa": ("goa", 15.4989, 73.8278, "Goa"),
        "north goa": ("goa", 15.4989, 73.8278, "Goa"),
        "south goa": ("goa", 15.4989, 73.8278, "Goa"),
        "panaji": ("goa", 15.4989, 73.8278, "Goa"),
    }

    def __init__(self, data_dir: Optional[str] = None):
        if not data_dir:
            # Detect project root directory containing data/
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            potential_data = os.path.join(os.path.dirname(base_dir), "data")
            if os.path.isdir(potential_data):
                self.data_dir = potential_data
            else:
                self.data_dir = os.path.join(base_dir, "data")
        else:
            self.data_dir = data_dir

        self.rates: Dict[str, Any] = self._load_rates()
        self.verified_routes: List[Dict[str, Any]] = self._load_routes()

    def _load_rates(self) -> Dict[str, Any]:
        path = os.path.join(self.data_dir, "intercity_transport_rates.json")
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _load_routes(self) -> List[Dict[str, Any]]:
        path = os.path.join(self.data_dir, "intercity_routes.json")
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Great-Circle geodesic distance in km."""
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(IntercityTransportService.EARTH_RADIUS_KM * c, 2)

    def resolve_destination(self, dest_input: str) -> Tuple[str, str, float, float]:
        """Normalize destination input to canonical (dest_id, display_name, lat, lon)."""
        clean = re.sub(r"[^\w\s]", "", dest_input.lower()).strip()
        for alias, data in self.DESTINATION_ALIASES.items():
            if alias in clean or clean in alias:
                return data[0], data[3], data[1], data[2]
        raise TravelGenieException(
            status_code=404,
            detail=f"Unsupported destination '{dest_input}'. Supported destinations are Dandeli, Coorg, Hampi, and Goa."
        )

    def resolve_origin(self, origin_input: str) -> Tuple[str, Optional[Tuple[float, float]]]:
        """Normalize origin input to canonical display name and coordinates if known."""
        clean = re.sub(r"[^\w\s]", "", origin_input.lower()).strip()
        for alias, data in self.KNOWN_ORIGIN_HUBS.items():
            if alias == clean or clean in alias or alias in clean:
                return data[2], (data[0], data[1])
        # Unrecognized city string
        display = origin_input.strip().title()
        return display, None

    def find_verified_route(self, origin_name: str, dest_id: str) -> Optional[Dict[str, Any]]:
        """Look up verified route record in curated route matrix."""
        orig_clean = origin_name.lower().strip()
        for r in self.verified_routes:
            if (r.get("destination_id") == dest_id and
                (r.get("origin_id") in orig_clean or orig_clean in r.get("origin_name", "").lower())):
                return r
        return None

    def get_recommendations(self, request: IntercityRecommendationRequest) -> IntercityRecommendationResponse:
        """
        Evaluate and rank all intercity travel modes for origin -> destination query.
        """
        dest_id, dest_name, dest_lat, dest_lon = self.resolve_destination(request.destination)
        origin_display, origin_coords = self.resolve_origin(request.origin)

        # Edge case: Origin is the same as destination
        orig_norm = re.sub(r"[^\w\s]", "", request.origin.lower()).strip()
        if orig_norm == dest_id or dest_id in orig_norm:
            raise TravelGenieException(
                status_code=400,
                detail=f"Origin '{request.origin}' is identical to destination '{dest_name}'. Intercity travel recommendations require different origin and destination points. Use local transit for intra-city routes."
            )

        # Check for verified route in curated database
        verified_route = self.find_verified_route(origin_display, dest_id)

        # Determine distance baselines
        is_verified = False
        road_distance_km: Optional[float] = None
        rail_distance_km: Optional[float] = None
        air_distance_km: Optional[float] = None
        rail_available = False
        flight_available = False
        boat_available = False
        boat_notes: Optional[str] = None
        route_provenance: Dict[str, Any] = {}

        if verified_route:
            is_verified = True
            road_distance_km = float(verified_route["road_distance_km"])
            rail_distance_km = float(verified_route["rail_distance_km"]) if verified_route.get("rail_distance_km") else None
            rail_available = bool(verified_route.get("rail_available", False))
            flight_available = bool(verified_route.get("flight_available", False))
            air_distance_km = float(verified_route["flight_straight_line_km"]) if verified_route.get("flight_straight_line_km") else None
            boat_available = bool(verified_route.get("boat_available", False))
            boat_notes = verified_route.get("boat_notes")
            route_provenance = {
                "source": verified_route.get("provenance", "Curated Intercity Route Benchmark"),
                "verification_status": "VERIFIED",
                "nearest_railhead": verified_route.get("nearest_railhead"),
                "nearest_airport": verified_route.get("nearest_airport"),
            }
        else:
            # Fallback to Great-Circle estimation if coordinates known or approximate
            if origin_coords:
                air_distance_km = self.haversine_distance_km(origin_coords[0], origin_coords[1], dest_lat, dest_lon)
                road_distance_km = round(air_distance_km * self.ROAD_DETOUR_FACTOR, 1)
            else:
                # Default generic regional distance proxy if origin coordinates are completely unknown
                air_distance_km = 350.0
                road_distance_km = round(air_distance_km * self.ROAD_DETOUR_FACTOR, 1)

            rail_available = road_distance_km >= 60.0
            rail_distance_km = round(road_distance_km * 1.05, 1) if rail_available else None
            flight_available = air_distance_km >= 250.0
            boat_available = False
            boat_notes = f"Inland or unverified corridor: No commercial passenger ferry route cataloged between {origin_display} and {dest_name}."
            route_provenance = {
                "source": "Haversine Great-Circle calculation with regional winding coefficient (1.30x)",
                "verification_status": "ESTIMATED",
                "estimation_assumption": "Straight-line geographic distance scaled by detour factor; live traffic and topography not accounted for.",
            }

        # Evaluate all 6 modes
        evaluated_options: List[IntercityOptionSchema] = []

        for mode_key in ["car", "bike", "bus", "train", "flight", "boat"]:
            opt = self._evaluate_mode(
                mode_key=mode_key,
                origin_name=origin_display,
                dest_name=dest_name,
                party_size=request.party_size,
                budget=request.budget,
                is_verified=is_verified,
                road_dist=road_distance_km,
                rail_dist=rail_distance_km,
                air_dist=air_distance_km,
                rail_available=rail_available,
                flight_available=flight_available,
                boat_available=boat_available,
                boat_notes=boat_notes,
                route_provenance=route_provenance,
            )
            evaluated_options.append(opt)

        # Rank options deterministically
        ranked_options = self._rank_options(evaluated_options, request.budget, request.user_preferred_mode)

        # Determine fastest, cheapest, and best ranked
        available_opts = [o for o in ranked_options if o.is_available and o.estimated_total_cost is not None]
        cheapest_mode = None
        fastest_mode = None
        best_ranked = None

        if available_opts:
            cheapest = min(available_opts, key=lambda x: x.estimated_total_cost or float("inf"))
            cheapest_mode = cheapest.transport_mode.value
            fastest = min(available_opts, key=lambda x: x.estimated_duration_hours or float("inf"))
            fastest_mode = fastest.transport_mode.value
            best_ranked = ranked_options[0].transport_mode.value

        methodology = (
            "Multi-criteria deterministic evaluation balancing total group expenditure, travel duration, "
            "group passenger capacity, budget compatibility, and data verification status. "
            "All pricing and speeds reflect curated Indian regional benchmarks without simulated bookings."
        )

        return IntercityRecommendationResponse(
            origin=origin_display,
            destination=dest_name,
            destination_id=dest_id,
            party_size=request.party_size,
            budget=request.budget,
            fastest_mode=fastest_mode,
            cheapest_mode=cheapest_mode,
            best_ranked_mode=best_ranked,
            options=ranked_options,
            available_count=len(available_opts),
            methodology_summary=methodology,
        )

    def _evaluate_mode(
        self,
        mode_key: str,
        origin_name: str,
        dest_name: str,
        party_size: int,
        budget: Optional[float],
        is_verified: bool,
        road_dist: float,
        rail_dist: Optional[float],
        air_dist: Optional[float],
        rail_available: bool,
        flight_available: bool,
        boat_available: bool,
        boat_notes: Optional[str],
        route_provenance: Dict[str, Any],
    ) -> IntercityOptionSchema:
        """Evaluate a single transportation mode against route parameters."""
        rate_meta = self.rates.get(mode_key, {})
        status = VerificationStatusEnum.VERIFIED if is_verified else VerificationStatusEnum.ESTIMATED

        # CAR
        if mode_key == "car":
            speed = rate_meta.get("speed_kmh", 65.0)
            per_km = rate_meta.get("per_km_rate", 14.0)
            base = rate_meta.get("base_fare", 500.0)
            toll = rate_meta.get("toll_estimate_per_km", 1.5)
            max_pax = rate_meta.get("max_passengers_per_vehicle", 4)

            vehicles_needed = max(1, math.ceil(party_size / max_pax))
            total_cost = round(((base + road_dist * (per_km + toll)) * vehicles_needed), 2)
            cost_per_person = round(total_cost / party_size, 2)
            # Duration with rest stop heuristic: 30 min break per 200 km
            rest_stops = math.floor(road_dist / 200.0) * 0.5
            duration = round((road_dist / speed) + rest_stops, 1)

            group_score = 1.0 if party_size <= 4 else (0.85 if party_size <= 8 else 0.70)
            group_label = "Optimal" if party_size <= 4 else ("Good" if party_size <= 8 else "Moderate")
            notes = f"Requires {vehicles_needed} standard vehicle{'s' if vehicles_needed > 1 else ''} for {party_size} traveler{'s' if party_size > 1 else ''}."

            return IntercityOptionSchema(
                transport_mode=TransportModeEnum.CAR,
                mode_name="Private Car / Cab",
                origin=origin_name,
                destination=dest_name,
                is_available=True,
                distance_km=road_dist,
                distance_type="verified_road" if is_verified else "estimated_road_winding",
                estimated_duration_hours=duration,
                estimated_cost_per_person=cost_per_person,
                estimated_total_cost=total_cost,
                cost_per_km=round(per_km + toll, 2),
                group_suitability_score=group_score,
                group_suitability_label=group_label,
                group_suitability_notes=notes,
                score=0.0,
                rank=1,
                recommendation_reason="",
                advantages=rate_meta.get("advantages", []),
                limitations=rate_meta.get("limitations", []),
                verification_status=status,
                data_provenance={**route_provenance, "mode_benchmark": rate_meta.get("provenance", {})},
            )

        # BIKE
        elif mode_key == "bike":
            speed = rate_meta.get("speed_kmh", 50.0)
            per_km = rate_meta.get("per_km_rate", 4.0)
            base = rate_meta.get("base_fare", 100.0)
            max_dist = rate_meta.get("max_practical_distance_km", 350.0)

            if road_dist > max_dist:
                return IntercityOptionSchema(
                    transport_mode=TransportModeEnum.BIKE,
                    mode_name="Motorcycle / Touring Bike",
                    origin=origin_name,
                    destination=dest_name,
                    is_available=False,
                    unavailability_reason=f"Journey distance ({road_dist} km) exceeds practical single-day motorcycle touring limit ({max_dist} km due to severe rider fatigue and safety).",
                    distance_km=road_dist,
                    distance_type="verified_road" if is_verified else "estimated_road_winding",
                    group_suitability_score=0.0,
                    group_suitability_label="Not Feasible",
                    group_suitability_notes="Exceeds safe single-day motorcycle endurance range.",
                    score=0.0,
                    rank=6,
                    recommendation_reason="Distance exceeds motorcycle safety threshold.",
                    verification_status=status,
                    data_provenance={**route_provenance, "mode_benchmark": rate_meta.get("provenance", {})},
                )

            bikes_needed = max(1, math.ceil(party_size / 2))
            total_cost = round(((base + road_dist * per_km) * bikes_needed), 2)
            cost_per_person = round(total_cost / party_size, 2)
            rest_stops = math.floor(road_dist / 120.0) * 0.4
            duration = round((road_dist / speed) + rest_stops, 1)

            group_score = 1.0 if party_size <= 2 else max(0.2, round(0.8 / bikes_needed, 2))
            group_label = "Optimal" if party_size <= 2 else "Limited"
            notes = "Ideal for 1-2 riders." if party_size <= 2 else f"Group of {party_size} requires convoy of {bikes_needed} motorcycles."

            return IntercityOptionSchema(
                transport_mode=TransportModeEnum.BIKE,
                mode_name="Motorcycle / Touring Bike",
                origin=origin_name,
                destination=dest_name,
                is_available=True,
                distance_km=road_dist,
                distance_type="verified_road" if is_verified else "estimated_road_winding",
                estimated_duration_hours=duration,
                estimated_cost_per_person=cost_per_person,
                estimated_total_cost=total_cost,
                cost_per_km=round(per_km, 2),
                group_suitability_score=group_score,
                group_suitability_label=group_label,
                group_suitability_notes=notes,
                score=0.0,
                rank=1,
                recommendation_reason="",
                advantages=rate_meta.get("advantages", []),
                limitations=rate_meta.get("limitations", []),
                verification_status=status,
                data_provenance={**route_provenance, "mode_benchmark": rate_meta.get("provenance", {})},
            )

        # BUS
        elif mode_key == "bus":
            speed = rate_meta.get("speed_kmh", 45.0)
            per_km_pax = rate_meta.get("per_km_per_person_rate", 1.85)
            base_pax = rate_meta.get("base_fare_per_person", 120.0)

            cost_per_person = round(base_pax + road_dist * per_km_pax, 2)
            total_cost = round(cost_per_person * party_size, 2)
            duration = round((road_dist / speed) + 0.5, 1)

            return IntercityOptionSchema(
                transport_mode=TransportModeEnum.BUS,
                mode_name="Intercity Bus (KSRTC / Private Sleeper)",
                origin=origin_name,
                destination=dest_name,
                is_available=True,
                distance_km=road_dist,
                distance_type="verified_road" if is_verified else "estimated_road_winding",
                estimated_duration_hours=duration,
                estimated_cost_per_person=cost_per_person,
                estimated_total_cost=total_cost,
                cost_per_km=round(per_km_pax, 2),
                group_suitability_score=0.90,
                group_suitability_label="High",
                group_suitability_notes=f"Readily accommodates {party_size} traveler{'s' if party_size > 1 else ''} with per-seat ticketing.",
                score=0.0,
                rank=1,
                recommendation_reason="",
                advantages=rate_meta.get("advantages", []),
                limitations=rate_meta.get("limitations", []),
                verification_status=status,
                data_provenance={**route_provenance, "mode_benchmark": rate_meta.get("provenance", {})},
            )

        # TRAIN
        elif mode_key == "train":
            if not rail_available or rail_dist is None:
                return IntercityOptionSchema(
                    transport_mode=TransportModeEnum.TRAIN,
                    mode_name="Indian Railways (Express / Sleeper)",
                    origin=origin_name,
                    destination=dest_name,
                    is_available=False,
                    unavailability_reason="No direct or practical railway railhead connection between these endpoints.",
                    distance_km=None,
                    distance_type="unavailable",
                    group_suitability_score=0.0,
                    group_suitability_label="Unavailable",
                    group_suitability_notes="Railway route not operated between selected points.",
                    score=0.0,
                    rank=6,
                    recommendation_reason="Rail route unavailable for this corridor.",
                    verification_status=VerificationStatusEnum.UNAVAILABLE,
                    data_provenance={**route_provenance, "mode_benchmark": rate_meta.get("provenance", {})},
                )

            speed = rate_meta.get("speed_kmh", 55.0)
            per_km_pax = rate_meta.get("per_km_per_person_rate", 1.25)
            base_pax = rate_meta.get("base_fare_per_person", 90.0)

            cost_per_person = round(base_pax + rail_dist * per_km_pax, 2)
            total_cost = round(cost_per_person * party_size, 2)
            duration = round((rail_dist / speed) + 0.5, 1)

            return IntercityOptionSchema(
                transport_mode=TransportModeEnum.TRAIN,
                mode_name="Indian Railways (Express / Sleeper)",
                origin=origin_name,
                destination=dest_name,
                is_available=True,
                distance_km=rail_dist,
                distance_type="verified_rail" if is_verified else "estimated_rail",
                estimated_duration_hours=duration,
                estimated_cost_per_person=cost_per_person,
                estimated_total_cost=total_cost,
                cost_per_km=round(per_km_pax, 2),
                group_suitability_score=0.95,
                group_suitability_label="Excellent",
                group_suitability_notes=f"Spacious sleeper berths and shared seating ideal for groups of {party_size}.",
                score=0.0,
                rank=1,
                recommendation_reason="",
                advantages=rate_meta.get("advantages", []),
                limitations=rate_meta.get("limitations", []),
                verification_status=status,
                data_provenance={**route_provenance, "mode_benchmark": rate_meta.get("provenance", {})},
            )

        # FLIGHT
        elif mode_key == "flight":
            min_dist = rate_meta.get("min_practical_distance_km", 250.0)
            if not flight_available or not air_dist or air_dist < min_dist:
                reason = (
                    f"Straight-line air distance ({air_dist or 'under 250'} km) is below commercial aviation viability threshold (minimum {min_dist} km)."
                    if air_dist and air_dist < min_dist
                    else "No active commercial air route or direct regional airport service operates between these endpoints."
                )
                return IntercityOptionSchema(
                    transport_mode=TransportModeEnum.FLIGHT,
                    mode_name="Commercial Flight",
                    origin=origin_name,
                    destination=dest_name,
                    is_available=False,
                    unavailability_reason=reason,
                    distance_km=air_dist,
                    distance_type="straight_line_air" if air_dist else "unavailable",
                    group_suitability_score=0.0,
                    group_suitability_label="Unavailable",
                    group_suitability_notes="Flight route not feasible for this distance/corridor.",
                    score=0.0,
                    rank=6,
                    recommendation_reason="Commercial flight not viable for route distance.",
                    verification_status=VerificationStatusEnum.UNAVAILABLE,
                    data_provenance={**route_provenance, "mode_benchmark": rate_meta.get("provenance", {})},
                )

            speed = rate_meta.get("speed_kmh", 550.0)
            per_km_pax = rate_meta.get("per_km_per_person_rate", 5.5)
            base_pax = rate_meta.get("base_fare_per_person", 2400.0)
            buffer = rate_meta.get("airport_buffer_hours", 3.0)

            cost_per_person = round(base_pax + air_dist * per_km_pax, 2)
            total_cost = round(cost_per_person * party_size, 2)
            duration = round((air_dist / speed) + buffer, 1)

            group_score = 0.85 if party_size <= 3 else 0.65
            group_label = "Good" if party_size <= 3 else "Cost-Intensive"
            notes = f"Fixed per-person airfare multiplies across all {party_size} travelers."

            return IntercityOptionSchema(
                transport_mode=TransportModeEnum.FLIGHT,
                mode_name="Commercial Flight",
                origin=origin_name,
                destination=dest_name,
                is_available=True,
                distance_km=air_dist,
                distance_type="straight_line_air",
                estimated_duration_hours=duration,
                estimated_cost_per_person=cost_per_person,
                estimated_total_cost=total_cost,
                cost_per_km=round(per_km_pax, 2),
                group_suitability_score=group_score,
                group_suitability_label=group_label,
                group_suitability_notes=notes,
                score=0.0,
                rank=1,
                recommendation_reason="",
                advantages=rate_meta.get("advantages", []),
                limitations=rate_meta.get("limitations", []),
                verification_status=status,
                data_provenance={
                    **route_provenance,
                    "note": "Flight distance is explicitly calculated as straight-line Great-Circle air distance, not road or rail network distance.",
                    "mode_benchmark": rate_meta.get("provenance", {}),
                },
            )

        # BOAT
        elif mode_key == "boat":
            if not boat_available:
                return IntercityOptionSchema(
                    transport_mode=TransportModeEnum.BOAT,
                    mode_name="Passenger Ferry / Coastal Cruise",
                    origin=origin_name,
                    destination=dest_name,
                    is_available=False,
                    unavailability_reason=boat_notes or f"Inland destination topography: No navigable passenger waterway connects {origin_name} to {dest_name}.",
                    distance_km=None,
                    distance_type="unavailable",
                    group_suitability_score=0.0,
                    group_suitability_label="Unavailable",
                    group_suitability_notes="Waterway ferry route does not exist for this inland route.",
                    score=0.0,
                    rank=6,
                    recommendation_reason="No passenger waterway operates on this route.",
                    verification_status=VerificationStatusEnum.UNAVAILABLE,
                    data_provenance={**route_provenance, "mode_benchmark": rate_meta.get("provenance", {})},
                )

            speed = rate_meta.get("speed_kmh", 28.0)
            per_km_pax = rate_meta.get("per_km_per_person_rate", 3.8)
            base_pax = rate_meta.get("base_fare_per_person", 350.0)

            cost_per_person = round(base_pax + road_dist * per_km_pax, 2)
            total_cost = round(cost_per_person * party_size, 2)
            duration = round((road_dist / speed) + 1.0, 1)

            return IntercityOptionSchema(
                transport_mode=TransportModeEnum.BOAT,
                mode_name="Passenger Ferry / Coastal Cruise",
                origin=origin_name,
                destination=dest_name,
                is_available=True,
                distance_km=road_dist,
                distance_type="verified_waterway" if is_verified else "estimated_waterway",
                estimated_duration_hours=duration,
                estimated_cost_per_person=cost_per_person,
                estimated_total_cost=total_cost,
                cost_per_km=round(per_km_pax, 2),
                group_suitability_score=0.80,
                group_suitability_label="Moderate",
                group_suitability_notes=f"Subject to seasonal ferry operating schedules for group of {party_size}.",
                score=0.0,
                rank=1,
                recommendation_reason="",
                advantages=rate_meta.get("advantages", []),
                limitations=rate_meta.get("limitations", []),
                verification_status=status,
                data_provenance={**route_provenance, "mode_benchmark": rate_meta.get("provenance", {})},
            )

        raise TravelGenieException(status_code=400, detail=f"Unsupported transportation mode '{mode_key}'.")

    def _rank_options(
        self,
        options: List[IntercityOptionSchema],
        budget: Optional[float],
        user_preferred_mode: Optional[str],
    ) -> List[IntercityOptionSchema]:
        """
        Rank available options using multi-attribute utility theory:
        Composite Score = (w_budget * S_budget + w_duration * S_duration + w_cost * S_cost + w_group * S_group) * S_reliability
        """
        available_opts = [o for o in options if o.is_available and o.estimated_total_cost is not None and o.estimated_duration_hours is not None]
        unavailable_opts = [o for o in options if not o.is_available]

        if not available_opts:
            for idx, o in enumerate(unavailable_opts, start=1):
                o.rank = idx
            return unavailable_opts

        min_cost = min(o.estimated_total_cost for o in available_opts)
        min_duration = min(o.estimated_duration_hours for o in available_opts)

        for opt in available_opts:
            # 1. Budget Compatibility & Score
            if budget is not None and budget > 0.0:
                cost = opt.estimated_total_cost or 0.0
                if cost <= budget:
                    opt.budget_compatibility = BudgetCompatibilityEnum.WITHIN_BUDGET
                    # Utility scales from 0.7 to 1.0 based on how far below budget it is
                    s_budget = 1.0 - 0.3 * (cost / budget)
                else:
                    opt.budget_compatibility = BudgetCompatibilityEnum.OVER_BUDGET
                    # Penalty function for exceeding budget
                    over_ratio = (cost - budget) / budget
                    s_budget = max(0.05, 1.0 / (1.0 + 3.0 * over_ratio))
            else:
                opt.budget_compatibility = BudgetCompatibilityEnum.NOT_SPECIFIED
                s_budget = 0.85

            # 2. Duration Utility
            s_duration = min(1.0, min_duration / max(0.1, opt.estimated_duration_hours or 1.0))

            # 3. Cost Utility
            s_cost = min(1.0, min_cost / max(1.0, opt.estimated_total_cost or 1.0))

            # 4. Group Suitability Utility
            s_group = opt.group_suitability_score

            # 5. Reliability Multiplier
            s_reliability = 1.0 if opt.verification_status == VerificationStatusEnum.VERIFIED else 0.90

            # 6. User preference bonus
            pref_bonus = 0.05 if (user_preferred_mode and user_preferred_mode.lower() == opt.transport_mode.value) else 0.0

            raw_score = (
                0.30 * s_budget
                + 0.25 * s_duration
                + 0.25 * s_cost
                + 0.20 * s_group
                + pref_bonus
            ) * s_reliability

            opt.score = round(min(1.0, max(0.0, raw_score)), 4)

            # Synthesize transparent reason
            reason_parts = []
            if opt.budget_compatibility == BudgetCompatibilityEnum.OVER_BUDGET:
                reason_parts.append(f"Estimated group cost (₹{opt.estimated_total_cost:,.0f}) exceeds your transportation budget (₹{budget:,.0f})")
            elif opt.estimated_total_cost == min_cost:
                reason_parts.append("Lowest overall group expenditure on this route")

            if opt.estimated_duration_hours == min_duration:
                reason_parts.append(f"Fastest travel time ({opt.estimated_duration_hours} hrs)")

            if opt.group_suitability_score >= 0.95:
                reason_parts.append(f"Well-suited for party size")

            if not reason_parts:
                reason_parts.append(f"Balanced balance of {opt.estimated_duration_hours} hrs journey and ₹{opt.estimated_cost_per_person:,.0f} per-person cost")

            opt.recommendation_reason = ". ".join(reason_parts) + "."

        # Sort available options descending by score
        available_opts.sort(key=lambda x: x.score, reverse=True)

        for idx, opt in enumerate(available_opts, start=1):
            opt.rank = idx

        # Unavailable options at the end
        for idx, opt in enumerate(unavailable_opts, start=len(available_opts) + 1):
            opt.rank = idx
            opt.score = 0.0
            opt.budget_compatibility = BudgetCompatibilityEnum.NOT_SPECIFIED

        return available_opts + unavailable_opts
