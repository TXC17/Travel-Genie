"""
Phase 8 End-to-End Planning Pipeline Runner & Observability Engine.
Integrates Phase 4 (MCDM), Phase 5 (K-Means), Phase 6 (OR-Tools/Held-Karp), and Phase 7 (NLG/Persistence)
into an observable, deterministic production workflow.
"""

import time
import uuid
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.destination import Destination
from app.models.attraction import Attraction
from app.models.trip import Trip, TripPreference
from app.models.itinerary import Itinerary, ItineraryDay, ItineraryItem
from app.algorithms.recommender import MCDMRecommender
from app.algorithms.clustering import SpatialDayClusterer
from app.algorithms.route_optimizer import IntraDayRouteOptimizer
from app.algorithms.conversation import ConversationalEngine
from app.schemas.recommendation import RecommendationRequest
from app.schemas.optimization import (
    MultiDayTripOptimizationRequest,
    MultiDayTripOptimizationResponse,
    OptimizedDayScheduleSchema,
    DayOptimizationMetricsSchema,
)
from app.schemas.chat import ExtractedTripConstraintsSchema
from app.schemas.pipeline import (
    GenerateItineraryRequest,
    GenerateItineraryResponse,
    PipelineDiagnosticsSchema,
    PipelineStageTelemetrySchema,
)
from app.core.exceptions import EntityNotFoundException, OptimizationConstraintException


class PlanningPipelineService:
    """
    Orchestrates the full deterministic travel planning pipeline with stage telemetry and diagnostics.
    """

    @staticmethod
    def calculate_persisted_end_date(start_date_str: str, duration_days: int) -> str:
        """
        Calculate inclusive trip end date: start_date + (duration_days - 1) days.
        Ensures a 1-day trip has identical start_date and end_date, while
        multi-day trips span the exact inclusive calendar duration.
        """
        d_start = date.fromisoformat(start_date_str)
        d_end = d_start + timedelta(days=max(0, duration_days - 1))
        return d_end.isoformat()

    def __init__(self):
        self.recommender = MCDMRecommender()
        self.clusterer = SpatialDayClusterer()
        self.optimizer = IntraDayRouteOptimizer()
        self.conversation_engine = ConversationalEngine()

    def optimize_itinerary_plan(
        self,
        db: Session,
        destination_id: str,
        duration_days: int,
        start_date: str = "2026-11-01",
        travel_month: Optional[int] = None,
        interests: Optional[List[str]] = None,
        total_budget: float = 15000.0,
        party_size: int = 1,
        preferred_transport: str = "auto",
        pace: str = "Moderate",
        selected_accommodation_id: Optional[str] = None,
        return_to_accommodation: bool = True,
    ) -> Tuple[MultiDayTripOptimizationResponse, Dict[str, Any]]:
        """
        Execute canonical itinerary optimization pipeline:
        1. Destination validation
        2. MCDM attraction recommendation (Phase 4)
        3. Spatial K-Means day partitioning with AUDIT-09 cluster rebalancing (Phase 5)
        4. OR-Tools route optimization with accommodation awareness (Phase 6)
        5. AUDIT-09 leisure/rest-day schedule allocation when requested duration > effective clusters
        """
        # 1. Destination Validation
        dest = db.query(Destination).filter(Destination.id == destination_id).first()
        if not dest:
            raise EntityNotFoundException("Destination", destination_id)

        # 2. Stage 1: Candidate Fetching & MCDM Recommendation (Phase 4)
        s1_start = time.perf_counter()
        all_attractions = db.query(Attraction).filter(Attraction.destination_id == destination_id).all()
        if not all_attractions:
            raise EntityNotFoundException("Attractions for destination", destination_id)

        rec_req = RecommendationRequest(
            destination_id=destination_id,
            travel_month=travel_month,
            interests=interests or ["heritage"],
            total_budget=total_budget,
            number_of_days=duration_days,
            party_size=party_size,
        )
        scored_candidates = self.recommender.rank_attractions(all_attractions, rec_req)

        max_candidates = min(len(all_attractions), duration_days * 4)
        scored_subset = scored_candidates[:max_candidates]
        candidate_entities = [sc.attraction for sc in scored_subset]
        mcdm_scores_map = {sc.attraction.id: sc.composite_score for sc in scored_subset}

        s1_duration = (time.perf_counter() - s1_start) * 1000
        stages = [
            PipelineStageTelemetrySchema(
                stage_name="MCDM_RECOMMENDATION",
                status="SUCCESS",
                duration_ms=round(s1_duration, 2),
                details={
                    "total_available": len(all_attractions),
                    "candidates_ranked": len(scored_candidates),
                    "selected_for_clustering": len(candidate_entities),
                },
            )
        ]

        # 3. Stage 2: Spatial K-Means Day Partitioning (Phase 5)
        s2_start = time.perf_counter()
        partition_res = self.clusterer.partition_days(
            destination_id=destination_id,
            attractions=candidate_entities,
            requested_k=duration_days,
        )
        s2_duration = (time.perf_counter() - s2_start) * 1000
        stages.append(
            PipelineStageTelemetrySchema(
                stage_name="SPATIAL_CLUSTERING",
                status="SUCCESS",
                duration_ms=round(s2_duration, 2),
                details={
                    "requested_k": duration_days,
                    "effective_k": partition_res.effective_k,
                    "total_clustered": partition_res.total_attractions,
                    "total_inertia_km2": partition_res.total_inertia_km2,
                },
            )
        )

        # 4. Stage 3: Google OR-Tools Route Optimization & Constraint Scheduling
        s3_start = time.perf_counter()

        selected_acc_id = None
        accommodation_endpoint = None
        if selected_accommodation_id:
            from app.models.accommodation import Accommodation
            acc = db.query(Accommodation).filter(
                Accommodation.id == selected_accommodation_id,
                Accommodation.is_active == True,
            ).first()
            if acc and acc.destination_id.lower() == destination_id.lower():
                selected_acc_id = acc.id
                from app.schemas.optimization import RouteEndpointSchema
                accommodation_endpoint = RouteEndpointSchema(
                    id=acc.id,
                    name=acc.name,
                    latitude=acc.latitude,
                    longitude=acc.longitude,
                    endpoint_type="accommodation",
                )

        opt_req = MultiDayTripOptimizationRequest(
            destination_id=destination_id,
            clusters=partition_res.clusters,
            start_date=start_date,
            preferred_transport=preferred_transport,
            pace=pace,
            day_start_time="09:00",
            total_budget=total_budget,
            party_size=party_size,
            accommodation=accommodation_endpoint,
            return_to_accommodation=return_to_accommodation,
            mcdm_scores_map=mcdm_scores_map,
        )
        optimized_itinerary = self.optimizer.optimize_multi_day_trip(opt_req)

        # AUDIT-09: Explicitly allocate leisure/rest days when requested duration exceeds effective sightseeing clusters
        current_scheduled_days = len(optimized_itinerary.days)
        leisure_days_added = 0
        if current_scheduled_days < duration_days:
            start_d = date.fromisoformat(str(start_date)) if isinstance(start_date, str) else start_date
            has_acc = accommodation_endpoint is not None
            for leisure_day_num in range(current_scheduled_days + 1, duration_days + 1):
                day_offset = leisure_day_num - 1
                leisure_date = (start_d + timedelta(days=day_offset)).isoformat()
                leisure_metrics = DayOptimizationMetricsSchema(
                    original_route_distance_km=0.0,
                    optimized_route_distance_km=0.0,
                    distance_reduction_km=0.0,
                    distance_reduction_pct=0.0,
                    original_travel_time_hours=0.0,
                    optimized_travel_time_hours=0.0,
                    travel_time_reduction_hours=0.0,
                    solver_status="LEISURE_DAY",
                )
                leisure_schedule = OptimizedDayScheduleSchema(
                    day_number=leisure_day_num,
                    date=leisure_date,
                    cluster_id=-1,
                    attraction_count=0,
                    feasibility_status="LEISURE_DAY",
                    recommended_transport="leisure",
                    day_start_time="10:00",
                    day_end_time="18:00",
                    total_sightseeing_duration_hours=0.0,
                    total_travel_duration_hours=0.0,
                    total_waiting_duration_hours=0.0,
                    total_day_duration_hours=0.0,
                    total_travel_distance_km=0.0,
                    day_estimated_admission_cost=0.0,
                    day_estimated_transit_cost=0.0,
                    day_total_estimated_cost=0.0,
                    start_location_type="accommodation" if has_acc else "destination",
                    start_location_name=accommodation_endpoint.name if has_acc else None,
                    end_location_type="accommodation" if has_acc else "destination",
                    end_location_name=accommodation_endpoint.name if has_acc else None,
                    is_round_trip=False,
                    accommodation_origin_leg=None,
                    accommodation_return_leg=None,
                    attraction_to_attraction_distance_km=0.0,
                    attraction_to_attraction_duration_hours=0.0,
                    route_sequence=[],
                    ordered_attractions=[],
                    optimization_metrics=leisure_metrics,
                    items=[],
                    legs=[],
                    constraint_violations=[],
                    provenance_metadata={
                        "day_type": "leisure_day",
                        "description": "Free exploration and leisure day at traveler's own pace.",
                        "provenance_classification": "user_schedule_allocation",
                    },
                )
                optimized_itinerary.days.append(leisure_schedule)
                leisure_days_added += 1

            optimized_itinerary.total_days = duration_days

        s3_duration = (time.perf_counter() - s3_start) * 1000
        stages.append(
            PipelineStageTelemetrySchema(
                stage_name="ROUTE_OPTIMIZATION_AND_SCHEDULING",
                status="SUCCESS",
                duration_ms=round(s3_duration, 2),
                details={
                    "total_scheduled": optimized_itinerary.total_scheduled_attractions,
                    "total_deferred": optimized_itinerary.total_deferred_attractions,
                    "distance_reduction_pct": optimized_itinerary.aggregate_distance_reduction_pct,
                    "total_travel_distance_km": optimized_itinerary.total_travel_distance_km,
                    "accommodation_aware": accommodation_endpoint is not None,
                    "accommodation_name": accommodation_endpoint.name if accommodation_endpoint else None,
                    "leisure_days_allocated": leisure_days_added,
                },
            )
        )

        context = {
            "destination": dest,
            "all_attractions": all_attractions,
            "candidate_entities": candidate_entities,
            "partition_res": partition_res,
            "scored_candidates": scored_candidates,
            "accommodation_endpoint": accommodation_endpoint,
            "selected_accommodation_id": selected_acc_id,
            "stages": stages,
        }
        return optimized_itinerary, context

    def persist_itinerary(
        self,
        db: Session,
        trip_id: str,
        itinerary_data: MultiDayTripOptimizationResponse,
    ) -> Itinerary:
        """
        Persist the optimized itinerary hierarchy (Itinerary, ItineraryDay, ItineraryItem)
        for a trip, updating existing versioning and marking previous versions non-current.
        """
        # 1. Mark previous itineraries as non-current
        db.query(Itinerary).filter(Itinerary.trip_id == trip_id).update({"is_current": False})

        # 2. Calculate version
        latest_itinerary = (
            db.query(Itinerary)
            .filter(Itinerary.trip_id == trip_id)
            .order_by(Itinerary.version.desc())
            .first()
        )
        version = (latest_itinerary.version + 1) if latest_itinerary else 1

        # 3. Create Itinerary
        db_itinerary = Itinerary(
            trip_id=trip_id,
            version=version,
            is_current=True,
            total_estimated_cost=itinerary_data.total_estimated_cost,
            total_travel_distance_km=itinerary_data.total_travel_distance_km,
            total_travel_duration_hours=itinerary_data.total_travel_duration_hours,
            total_sightseeing_duration_hours=itinerary_data.total_sightseeing_duration_hours,
            optimization_metrics={
                "distance_reduction_pct": itinerary_data.aggregate_distance_reduction_pct,
                "total_scheduled_attractions": itinerary_data.total_scheduled_attractions,
                "total_deferred_attractions": itinerary_data.total_deferred_attractions,
            },
        )
        db.add(db_itinerary)
        db.flush()

        # 4. Create Days and Items
        for day in itinerary_data.days:
            db_day = ItineraryDay(
                itinerary_id=db_itinerary.id,
                day_number=day.day_number,
                date=day.date or f"Day {day.day_number}",
                cluster_id=day.cluster_id,
                day_travel_distance_km=day.total_travel_distance_km,
                day_travel_duration_hours=day.total_travel_duration_hours,
                day_sightseeing_duration_hours=day.total_sightseeing_duration_hours,
                day_estimated_cost=day.day_total_estimated_cost,
                recommended_transport=day.recommended_transport,
            )
            db.add(db_day)
            db.flush()

            for item in day.items:
                db_item = ItineraryItem(
                    itinerary_day_id=db_day.id,
                    attraction_id=item.attraction.id,
                    visit_order=item.visit_order,
                    arrival_time=item.arrival_time,
                    departure_time=item.departure_time,
                    visit_duration_hours=item.visit_duration_hours,
                    travel_time_from_prev_hours=item.travel_time_from_prev_hours,
                    distance_from_prev_km=item.distance_from_prev_km,
                    item_cost=item.item_admission_fee,
                    crowd_estimate_score=item.crowd_estimate_score,
                    crowd_level=item.crowd_level,
                    visit_notes=item.visit_notes,
                )
                db.add(db_item)

        db.flush()
        return db_itinerary

    def generate_itinerary(
        self, db: Session, user_id: str, request: GenerateItineraryRequest
    ) -> GenerateItineraryResponse:
        pipeline_id = str(uuid.uuid4())
        total_start = time.perf_counter()

        optimized_itinerary, context = self.optimize_itinerary_plan(
            db=db,
            destination_id=request.destination_id,
            duration_days=request.duration_days,
            start_date=request.start_date,
            travel_month=request.travel_month,
            interests=request.interests,
            total_budget=request.total_budget,
            party_size=request.party_size,
            preferred_transport=request.preferred_transport,
            pace=request.pace,
            selected_accommodation_id=getattr(request, "selected_accommodation_id", None),
            return_to_accommodation=getattr(request, "return_to_accommodation", True),
        )

        dest = context["destination"]
        selected_acc_id = context["selected_accommodation_id"]
        stages = context["stages"]

        # Stage 4: Database Persistence (Phase 7)
        s4_start = time.perf_counter()
        trip_title = f"{dest.name} {request.duration_days}-Day Trip"
        persisted_end_date = self.calculate_persisted_end_date(request.start_date, request.duration_days)

        trip = Trip(
            creator_id=user_id,
            destination_id=request.destination_id,
            title=trip_title,
            start_date=request.start_date,
            end_date=persisted_end_date,
            number_of_days=request.duration_days,
            party_size=request.party_size,
            total_budget=request.total_budget,
            selected_accommodation_id=selected_acc_id,
        )
        db.add(trip)
        db.flush()

        pref = TripPreference(
            trip_id=trip.id,
            interests=request.interests,
            pace=request.pace,
            preferred_transport=request.preferred_transport,
            budget_tier="standard",
        )
        db.add(pref)
        db.flush()

        db_itinerary = self.persist_itinerary(db, trip.id, optimized_itinerary)
        db.commit()

        s4_duration = (time.perf_counter() - s4_start) * 1000
        stages.append(
            PipelineStageTelemetrySchema(
                stage_name="DATABASE_PERSISTENCE",
                status="SUCCESS",
                duration_ms=round(s4_duration, 2),
                details={"trip_id": trip.id, "itinerary_id": db_itinerary.id, "version": db_itinerary.version},
            )
        )

        # Stage 5: Factual Natural Language Explanation (Phase 7)
        s5_start = time.perf_counter()
        explanation = self.conversation_engine.generate_explanation(optimized_itinerary)
        s5_duration = (time.perf_counter() - s5_start) * 1000
        stages.append(
            PipelineStageTelemetrySchema(
                stage_name="NLG_EXPLANATION",
                status="SUCCESS",
                duration_ms=round(s5_duration, 2),
                details={"explanation_length_chars": len(explanation)},
            )
        )

        total_duration = (time.perf_counter() - total_start) * 1000

        diagnostics = PipelineDiagnosticsSchema(
            pipeline_id=pipeline_id,
            status="COMPLETED",
            total_duration_ms=round(total_duration, 2),
            candidate_attractions_count=len(context["all_attractions"]),
            recommended_attractions_count=len(context["candidate_entities"]),
            clusters_count=context["partition_res"].effective_k,
            total_scheduled_count=optimized_itinerary.total_scheduled_attractions,
            total_deferred_count=optimized_itinerary.total_deferred_attractions,
            distance_reduction_pct=optimized_itinerary.aggregate_distance_reduction_pct,
            stages=stages,
        )

        constraints_schema = ExtractedTripConstraintsSchema(
            destination_id=request.destination_id,
            destination_name=dest.name,
            duration_days=request.duration_days,
            total_budget=request.total_budget,
            party_size=request.party_size,
            interests=request.interests,
            pace=request.pace,
            preferred_transport=request.preferred_transport,
            start_date=request.start_date,
            travel_month=request.travel_month,
            is_complete=True,
        )

        return GenerateItineraryResponse(
            trip_id=trip.id,
            itinerary_id=db_itinerary.id,
            version=db_itinerary.version,
            title=trip_title,
            destination_id=request.destination_id,
            constraints=constraints_schema,
            itinerary=optimized_itinerary,
            diagnostics=diagnostics,
            explanation=explanation,
        )
