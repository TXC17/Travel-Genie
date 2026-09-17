"""
Google OR-Tools Route Optimization and Intra-Day Constraint Scheduling Engine.
Solves intra-day Traveling Salesperson Problem (TSP), enforces time-window bounds,
calculates timeline arrivals/departures, and iteratively prunes infeasible stops via MCDM scores.
Equipped with dual-engine architecture: Google OR-Tools with deterministic Held-Karp/2-Opt fallback.
"""

import math
from typing import List, Dict, Tuple, Optional, Any
import numpy as np

# Dynamically attempt importing Google OR-Tools; support graceful fallback if OS binary collision occurs
ORTOOLS_AVAILABLE = False
try:
    from ortools.constraint_solver import routing_enums_pb2, pywrapcp
    ORTOOLS_AVAILABLE = True
except (ImportError, OSError):
    ORTOOLS_AVAILABLE = False

from app.models.attraction import Attraction
from app.schemas.attraction import AttractionResponse
from app.schemas.clustering import ClusterDaySchema
from app.schemas.optimization import (
    RouteLegSchema,
    ScheduledVisitItemSchema,
    DayOptimizationMetricsSchema,
    DeferredAttractionSchema,
    OptimizedDayScheduleSchema,
    DayOptimizationRequest,
    MultiDayTripOptimizationRequest,
    MultiDayTripOptimizationResponse,
)


class IntraDayRouteOptimizer:
    """
    Intra-Day Route Optimization and Scheduling Solver.
    Minimizes travel distance/time while strictly respecting time windows,
    operating hours, visit durations, and daily pace limits.
    """

    EARTH_RADIUS_KM = 6371.0088
    ROAD_WINDING_FACTOR = 1.30  # Standard regional detour coefficient

    TRANSPORT_SPEEDS_KMH = {
        "walking": 4.5,
        "auto": 25.0,
        "car": 35.0,
        "taxi": 35.0,
        "rental": 40.0,
        "public": 20.0,
    }

    TRANSPORT_RATES = {
        "walking": {"per_km": 0.0, "base": 0.0},
        "auto": {"per_km": 15.0, "base": 30.0},
        "car": {"per_km": 22.0, "base": 100.0},
        "taxi": {"per_km": 22.0, "base": 100.0},
        "rental": {"per_km": 12.0, "base": 400.0},
        "public": {"per_km": 4.0, "base": 10.0},
    }

    PACE_HOURS_LIMIT = {
        "Relaxed": 6.0,
        "Moderate": 8.0,
        "Intense": 10.0,
    }

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Great-Circle distance in km."""
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return IntraDayRouteOptimizer.EARTH_RADIUS_KM * c

    @staticmethod
    def estimate_road_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Estimate road travel distance in km using Great-Circle distance with road winding factor."""
        straight_dist = IntraDayRouteOptimizer.haversine_distance_km(lat1, lon1, lat2, lon2)
        return straight_dist * IntraDayRouteOptimizer.ROAD_WINDING_FACTOR

    @staticmethod
    def parse_time_to_hours(time_str: Optional[str], default_val: float) -> float:
        """Convert HH:MM or HH:MM:SS string to decimal hours (e.g. '09:30:00' -> 9.5)."""
        if not time_str:
            return default_val
        parts = str(time_str).split(":")
        try:
            h = float(parts[0])
            m = float(parts[1]) if len(parts) > 1 else 0.0
            s = float(parts[2]) if len(parts) > 2 else 0.0
            return h + (m / 60.0) + (s / 3600.0)
        except (ValueError, IndexError):
            return default_val

    @staticmethod
    def format_hours_to_time(hours_val: float) -> str:
        """Convert decimal hours (e.g. 9.5) to HH:MM format."""
        h = int(hours_val) % 24
        m = int(round((hours_val - int(hours_val)) * 60))
        if m >= 60:
            h = (h + 1) % 24
            m = 0
        return f"{h:02d}:{m:02d}"

    def build_distance_and_time_matrices(
        self, attractions: List[AttractionResponse], transport_mode: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Construct NxN distance (km) and travel duration (hours) matrices.
        """
        n = len(attractions)
        dist_matrix = np.zeros((n, n), dtype=float)
        time_matrix = np.zeros((n, n), dtype=float)
        speed = self.TRANSPORT_SPEEDS_KMH.get(transport_mode, 25.0)

        for i in range(n):
            for j in range(n):
                if i != j:
                    d = self.estimate_road_distance_km(
                        attractions[i].latitude,
                        attractions[i].longitude,
                        attractions[j].latitude,
                        attractions[j].longitude,
                    )
                    t = d / speed
                    dist_matrix[i, j] = d
                    time_matrix[i, j] = t

        return dist_matrix, time_matrix

    def _solve_tsp_held_karp_open(self, dist_matrix: np.ndarray) -> List[int]:
        """
        Solve open Hamiltonian path starting at node 0 minimizing total travel distance
        using the Held-Karp dynamic programming algorithm with global mathematical optimality.
        """
        n = dist_matrix.shape[0]
        if n <= 1:
            return [0]
        if n == 2:
            return [0, 1]

        memo = {}

        def get_min_path(mask, curr):
            if mask == (1 << n) - 1:
                return 0.0, [curr]

            state = (mask, curr)
            if state in memo:
                return memo[state]

            min_cost = float("inf")
            best_path = []

            for nxt in range(n):
                if not (mask & (1 << nxt)):
                    cost, path = get_min_path(mask | (1 << nxt), nxt)
                    total_cost = dist_matrix[curr, nxt] + cost
                    if total_cost < min_cost:
                        min_cost = total_cost
                        best_path = [curr] + path

            memo[state] = (min_cost, best_path)
            return min_cost, best_path

        _, opt_path = get_min_path(1, 0)
        return opt_path

    def solve_tsp_sequence(
        self, dist_matrix: np.ndarray, time_matrix: np.ndarray
    ) -> Tuple[List[int], str]:
        """
        Solve optimal open Hamiltonian visit path through all nodes.
        Uses Google OR-Tools if available; otherwise uses exact Held-Karp dynamic programming.
        """
        n = dist_matrix.shape[0]
        if n <= 1:
            return [0], "OPTIMAL"
        if n == 2:
            return [0, 1], "OPTIMAL"

        if ORTOOLS_AVAILABLE:
            try:
                int_dist_matrix = (dist_matrix * 1000).astype(int)

                # Open TSP with fixed start at node 0 and dummy terminal node n
                extended_matrix = np.zeros((n + 1, n + 1), dtype=int)
                extended_matrix[:n, :n] = int_dist_matrix
                extended_matrix[:n, n] = 0
                extended_matrix[n, :] = 0

                manager = pywrapcp.RoutingIndexManager(n + 1, 1, [0], [n])
                routing = pywrapcp.RoutingModel(manager)

                def distance_callback(from_index, to_index):
                    from_node = manager.IndexToNode(from_index)
                    to_node = manager.IndexToNode(to_index)
                    return int(extended_matrix[from_node][to_node])

                transit_callback_index = routing.RegisterTransitCallback(distance_callback)
                routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

                search_parameters = pywrapcp.DefaultRoutingSearchParameters()
                search_parameters.first_solution_strategy = (
                    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
                )
                search_parameters.local_search_metaheuristic = (
                    routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
                )
                search_parameters.time_limit.milliseconds = 500

                solution = routing.SolveWithParameters(search_parameters)

                if solution:
                    ordered_nodes = []
                    index = routing.Start(0)
                    while not routing.IsEnd(index):
                        node = manager.IndexToNode(index)
                        if node < n:
                            ordered_nodes.append(node)
                        index = solution.Value(routing.NextVar(index))

                    if len(ordered_nodes) == n:
                        return ordered_nodes, "OPTIMAL_ORTOOLS"
            except Exception:
                pass

        # Exact Held-Karp Dynamic Programming Solver
        opt_path = self._solve_tsp_held_karp_open(dist_matrix)
        return opt_path, "OPTIMAL_HELD_KARP"

    def simulate_day_timeline(
        self,
        attractions: List[AttractionResponse],
        sequence: List[int],
        dist_matrix: np.ndarray,
        time_matrix: np.ndarray,
        transport_mode: str,
        start_time_hours: float,
        max_daily_hours: float,
    ) -> Tuple[bool, List[ScheduledVisitItemSchema], List[RouteLegSchema], Dict[str, float], Optional[str]]:
        """
        Simulate sequential visit timeline, checking opening hours, waiting times, and daily limit.
        Returns: (is_feasible, items, legs, duration_metrics, violation_reason)
        """
        items: List[ScheduledVisitItemSchema] = []
        legs: List[RouteLegSchema] = []

        curr_time = start_time_hours
        total_sightseeing = 0.0
        total_travel = 0.0
        total_waiting = 0.0
        total_dist = 0.0
        total_adm_cost = 0.0
        total_transit_cost = 0.0

        transit_rates = self.TRANSPORT_RATES.get(transport_mode, {"per_km": 15.0, "base": 30.0})

        for order_idx, node_idx in enumerate(sequence, start=1):
            attr = attractions[node_idx]
            visit_dur = max(0.5, float(attr.average_visit_duration or 1.5))
            adm_fee = float(attr.entry_fee or 0.0)

            # Operating hours check
            open_hours = self.parse_time_to_hours(attr.opening_time, 6.0)
            close_hours = self.parse_time_to_hours(attr.closing_time, 22.0)

            # Check if operating window is shorter than dwell time
            if (close_hours - open_hours) < visit_dur:
                violation_msg = (
                    f"Attraction '{attr.name}' is only open for {close_hours - open_hours:.1f}h "
                    f"({self.format_hours_to_time(open_hours)} - {self.format_hours_to_time(close_hours)}), "
                    f"which is less than the required visit duration ({visit_dur:.1f}h)."
                )
                return False, [], [], {}, violation_msg

            travel_time_from_prev = 0.0
            dist_from_prev = 0.0
            leg_cost = 0.0

            if order_idx > 1:
                prev_node_idx = sequence[order_idx - 2]
                dist_from_prev = float(dist_matrix[prev_node_idx, node_idx])
                travel_time_from_prev = float(time_matrix[prev_node_idx, node_idx])
                leg_cost = (dist_from_prev * transit_rates["per_km"]) + (
                    transit_rates["base"] if order_idx == 2 else 0.0
                )

                curr_time += travel_time_from_prev
                total_travel += travel_time_from_prev
                total_dist += dist_from_prev
                total_transit_cost += leg_cost

                legs.append(
                    RouteLegSchema(
                        from_attraction_id=attractions[prev_node_idx].id,
                        from_attraction_name=attractions[prev_node_idx].name,
                        to_attraction_id=attr.id,
                        to_attraction_name=attr.name,
                        distance_km=round(dist_from_prev, 3),
                        travel_time_hours=round(travel_time_from_prev, 3),
                        transport_mode=transport_mode,
                        estimated_transit_cost=round(leg_cost, 2),
                        provenance_method="haversine_with_road_winding_factor",
                    )
                )

            # Arrival time at this attraction
            arrival_hours = curr_time

            waiting_time = 0.0
            if arrival_hours < open_hours:
                waiting_time = open_hours - arrival_hours
                curr_time = open_hours
                total_waiting += waiting_time

            # Start of visit
            start_visit_hours = curr_time
            curr_time += visit_dur
            departure_hours = curr_time
            total_sightseeing += visit_dur
            total_adm_cost += adm_fee

            # Check if visit extends past closing time
            if departure_hours > (close_hours + 0.1):  # 6-min grace threshold
                violation_msg = (
                    f"Visit at '{attr.name}' departs at {self.format_hours_to_time(departure_hours)}, "
                    f"which exceeds official closing time ({self.format_hours_to_time(close_hours)})."
                )
                return False, [], [], {}, violation_msg

            items.append(
                ScheduledVisitItemSchema(
                    attraction=attr,
                    visit_order=order_idx,
                    arrival_time=self.format_hours_to_time(arrival_hours),
                    departure_time=self.format_hours_to_time(departure_hours),
                    visit_duration_hours=round(visit_dur, 2),
                    travel_time_from_prev_hours=round(travel_time_from_prev, 3),
                    distance_from_prev_km=round(dist_from_prev, 3),
                    item_admission_fee=round(adm_fee, 2),
                    waiting_time_hours=round(waiting_time, 3),
                    crowd_estimate_score=round(float(attr.popularity_score or 0.5), 2),
                    crowd_level="High" if (attr.popularity_score or 0.5) > 0.8 else "Moderate",
                    visit_notes=f"Recommended visit window {self.format_hours_to_time(start_visit_hours)} - {self.format_hours_to_time(departure_hours)}",
                )
            )

        total_day_duration = curr_time - start_time_hours
        if total_day_duration > max_daily_hours:
            violation_msg = (
                f"Total day duration ({total_day_duration:.2f}h) exceeds the {max_daily_hours:.1f}h pace limit."
            )
            return False, [], [], {}, violation_msg

        metrics = {
            "total_sightseeing": round(total_sightseeing, 2),
            "total_travel": round(total_travel, 3),
            "total_waiting": round(total_waiting, 3),
            "total_day_duration": round(total_day_duration, 2),
            "total_dist": round(total_dist, 3),
            "total_adm_cost": round(total_adm_cost, 2),
            "total_transit_cost": round(total_transit_cost, 2),
            "total_cost": round(total_adm_cost + total_transit_cost, 2),
        }

        return True, items, legs, metrics, None

    def optimize_day_schedule(
        self, request: DayOptimizationRequest
    ) -> Tuple[OptimizedDayScheduleSchema, List[DeferredAttractionSchema]]:
        """
        Optimize intra-day sequence, validating daily constraints and iteratively pruning
        the lowest MCDM-scoring attractions when a cluster is time-infeasible.
        """
        candidate_attractions = list(request.cluster.attractions)
        deferred_attractions: List[DeferredAttractionSchema] = []

        start_time_hours = self.parse_time_to_hours(request.day_start_time, 9.0)
        max_daily_hours = self.PACE_HOURS_LIMIT.get(request.pace, 8.0)
        mcdm_scores = request.mcdm_scores_map or {}

        while candidate_attractions:
            # 1. Build distance and travel time matrices
            dist_matrix, time_matrix = self.build_distance_and_time_matrices(
                candidate_attractions, request.preferred_transport
            )

            # 2. Compute Baseline (Unoptimized) Route Metrics
            n = len(candidate_attractions)
            orig_dist = 0.0
            orig_time = 0.0
            for k in range(n - 1):
                orig_dist += dist_matrix[k, k + 1]
                orig_time += time_matrix[k, k + 1]

            # 3. Solve Optimized TSP Sequence
            opt_sequence, solver_mode = self.solve_tsp_sequence(dist_matrix, time_matrix)
            opt_dist = 0.0
            opt_time = 0.0
            for k in range(len(opt_sequence) - 1):
                i1, i2 = opt_sequence[k], opt_sequence[k + 1]
                opt_dist += dist_matrix[i1, i2]
                opt_time += time_matrix[i1, i2]

            # 4. Simulate Daily Timeline & Check Hard Constraints
            is_feasible, items, legs, metrics, violation_reason = self.simulate_day_timeline(
                candidate_attractions,
                opt_sequence,
                dist_matrix,
                time_matrix,
                request.preferred_transport,
                start_time_hours,
                max_daily_hours,
            )

            if is_feasible:
                # Calculate optimization savings
                dist_red_km = max(0.0, orig_dist - opt_dist)
                dist_red_pct = (
                    ((orig_dist - opt_dist) / orig_dist * 100.0) if orig_dist > 0.0 else 0.0
                )
                time_red_hours = max(0.0, orig_time - opt_time)

                opt_metrics = DayOptimizationMetricsSchema(
                    original_route_distance_km=round(orig_dist, 3),
                    optimized_route_distance_km=round(opt_dist, 3),
                    distance_reduction_km=round(dist_red_km, 3),
                    distance_reduction_pct=round(max(0.0, dist_red_pct), 2),
                    original_travel_time_hours=round(orig_time, 3),
                    optimized_travel_time_hours=round(opt_time, 3),
                    travel_time_reduction_hours=round(time_red_hours, 3),
                    solver_status=solver_mode,
                )

                feasibility_status = "FEASIBLE" if not deferred_attractions else "FEASIBLE_AFTER_PRUNING"

                day_schedule = OptimizedDayScheduleSchema(
                    day_number=request.day_number,
                    cluster_id=request.cluster.cluster_id,
                    attraction_count=len(items),
                    feasibility_status=feasibility_status,
                    recommended_transport=request.preferred_transport,
                    day_start_time=request.day_start_time,
                    day_end_time=self.format_hours_to_time(start_time_hours + metrics["total_day_duration"]),
                    total_sightseeing_duration_hours=metrics["total_sightseeing"],
                    total_travel_duration_hours=metrics["total_travel"],
                    total_waiting_duration_hours=metrics["total_waiting"],
                    total_day_duration_hours=metrics["total_day_duration"],
                    total_travel_distance_km=metrics["total_dist"],
                    day_estimated_admission_cost=metrics["total_adm_cost"],
                    day_estimated_transit_cost=metrics["total_transit_cost"],
                    day_total_estimated_cost=metrics["total_cost"],
                    route_sequence=opt_sequence,
                    ordered_attractions=[candidate_attractions[i] for i in opt_sequence],
                    optimization_metrics=opt_metrics,
                    items=items,
                    legs=legs,
                    constraint_violations=[],
                )

                return day_schedule, deferred_attractions

            # 5. Day is Infeasible: Prune the lowest MCDM-scoring attraction
            lowest_idx = 0
            lowest_score = float("inf")
            for idx, a in enumerate(candidate_attractions):
                score = mcdm_scores.get(a.id, float(a.popularity_score or 0.5))
                if score < lowest_score:
                    lowest_score = score
                    lowest_idx = idx

            pruned_attr = candidate_attractions.pop(lowest_idx)
            violating_type = "daily_time_limit" if "pace limit" in violation_reason else (
                "visit_duration" if "less than the required visit duration" in violation_reason else "opening_hours"
            )

            deferred_attractions.append(
                DeferredAttractionSchema(
                    attraction_id=pruned_attr.id,
                    attraction_name=pruned_attr.name,
                    original_day_number=request.day_number,
                    reason=f"Deferred: {violation_reason} (Pruned lowest MCDM score: {lowest_score:.2f})",
                    violating_constraint=violating_type,
                    mcdm_score=round(lowest_score, 3) if lowest_score != float("inf") else None,
                )
            )

        # Fallback for empty day if all attractions were pruned
        fallback_metrics = DayOptimizationMetricsSchema(
            original_route_distance_km=0.0,
            optimized_route_distance_km=0.0,
            distance_reduction_km=0.0,
            distance_reduction_pct=0.0,
            original_travel_time_hours=0.0,
            optimized_travel_time_hours=0.0,
            travel_time_reduction_hours=0.0,
            solver_status="INFEASIBLE_ALL_PRUNED",
        )
        empty_schedule = OptimizedDayScheduleSchema(
            day_number=request.day_number,
            cluster_id=request.cluster.cluster_id,
            attraction_count=0,
            feasibility_status="INFEASIBLE_ALL_PRUNED",
            recommended_transport=request.preferred_transport,
            day_start_time=request.day_start_time,
            day_end_time=request.day_start_time,
            total_sightseeing_duration_hours=0.0,
            total_travel_duration_hours=0.0,
            total_waiting_duration_hours=0.0,
            total_day_duration_hours=0.0,
            total_travel_distance_km=0.0,
            day_estimated_admission_cost=0.0,
            day_estimated_transit_cost=0.0,
            day_total_estimated_cost=0.0,
            route_sequence=[],
            ordered_attractions=[],
            optimization_metrics=fallback_metrics,
            items=[],
            legs=[],
            constraint_violations=["All candidate attractions were pruned due to infeasibility."],
        )
        return empty_schedule, deferred_attractions

    def optimize_multi_day_trip(
        self, request: MultiDayTripOptimizationRequest
    ) -> MultiDayTripOptimizationResponse:
        """
        Optimize full multi-day trip by iterating across all Phase 5 spatial day clusters.
        """
        days_schedules: List[OptimizedDayScheduleSchema] = []
        all_deferred: List[DeferredAttractionSchema] = []

        total_scheduled = 0
        total_dist = 0.0
        total_travel_time = 0.0
        total_sightseeing_time = 0.0
        total_day_time = 0.0
        total_cost = 0.0

        total_orig_dist = 0.0
        total_opt_dist = 0.0

        for day_idx, cluster in enumerate(request.clusters, start=1):
            day_req = DayOptimizationRequest(
                destination_id=request.destination_id,
                trip_id=request.trip_id,
                day_number=day_idx,
                cluster=cluster,
                preferred_transport=request.preferred_transport,
                pace=request.pace,
                day_start_time=request.day_start_time,
                mcdm_scores_map=request.mcdm_scores_map,
            )

            day_schedule, day_deferred = self.optimize_day_schedule(day_req)
            days_schedules.append(day_schedule)
            all_deferred.extend(day_deferred)

            total_scheduled += day_schedule.attraction_count
            total_dist += day_schedule.total_travel_distance_km
            total_travel_time += day_schedule.total_travel_duration_hours
            total_sightseeing_time += day_schedule.total_sightseeing_duration_hours
            total_day_time += day_schedule.total_day_duration_hours
            total_cost += day_schedule.day_total_estimated_cost

            total_orig_dist += day_schedule.optimization_metrics.original_route_distance_km
            total_opt_dist += day_schedule.optimization_metrics.optimized_route_distance_km

        agg_dist_red_pct = (
            ((total_orig_dist - total_opt_dist) / total_orig_dist * 100.0)
            if total_orig_dist > 0.0
            else 0.0
        )

        return MultiDayTripOptimizationResponse(
            destination_id=request.destination_id,
            trip_id=request.trip_id,
            total_days=len(days_schedules),
            total_scheduled_attractions=total_scheduled,
            total_deferred_attractions=len(all_deferred),
            total_travel_distance_km=round(total_dist, 3),
            total_travel_duration_hours=round(total_travel_time, 3),
            total_sightseeing_duration_hours=round(total_sightseeing_time, 2),
            total_day_duration_hours=round(total_day_time, 2),
            total_estimated_cost=round(total_cost, 2),
            aggregate_distance_reduction_pct=round(max(0.0, agg_dist_red_pct), 2),
            days=days_schedules,
            deferred_attractions=all_deferred,
        )
