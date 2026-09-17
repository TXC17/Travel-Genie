"""
Phase 8 End-to-End Planning Pipeline Runner & Observability Engine.
Integrates Phase 4 (MCDM), Phase 5 (K-Means), Phase 6 (OR-Tools/Held-Karp), and Phase 7 (NLG/Persistence)
into an observable, deterministic production workflow.
"""

import time
import uuid
from typing import List, Dict, Any, Optional
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
from app.schemas.optimization import MultiDayTripOptimizationRequest
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

    def __init__(self):
        self.recommender = MCDMRecommender()
        self.clusterer = SpatialDayClusterer()
        self.optimizer = IntraDayRouteOptimizer()
        self.conversation_engine = ConversationalEngine()

    def generate_itinerary(
        self, db: Session, user_id: str, request: GenerateItineraryRequest
    ) -> GenerateItineraryResponse:
        pipeline_id = str(uuid.uuid4())
        total_start = time.perf_counter()
        stages: List[PipelineStageTelemetrySchema] = []

        # 1. Destination Validation
        dest = db.query(Destination).filter(Destination.id == request.destination_id).first()
        if not dest:
            raise EntityNotFoundException("Destination", request.destination_id)

        # 2. Stage 1: Candidate Fetching & MCDM Recommendation (Phase 4)
        s1_start = time.perf_counter()
        all_attractions = db.query(Attraction).filter(Attraction.destination_id == request.destination_id).all()
        if not all_attractions:
            raise EntityNotFoundException("Attractions for destination", request.destination_id)

        rec_req = RecommendationRequest(
            destination_id=request.destination_id,
            travel_month=request.travel_month,
            interests=request.interests,
            total_budget=request.total_budget,
            number_of_days=request.duration_days,
            party_size=request.party_size,
        )
        scored_candidates = self.recommender.rank_attractions(all_attractions, rec_req)

        max_candidates = min(len(all_attractions), request.duration_days * 4)
        scored_subset = scored_candidates[:max_candidates]
        candidate_entities = [sc.attraction for sc in scored_subset]
        mcdm_scores_map = {sc.attraction.id: sc.composite_score for sc in scored_subset}

        s1_duration = (time.perf_counter() - s1_start) * 1000
        stages.append(
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
        )

        # 3. Stage 2: Spatial K-Means Day Partitioning (Phase 5)
        s2_start = time.perf_counter()
        partition_res = self.clusterer.partition_days(
            destination_id=request.destination_id,
            attractions=candidate_entities,
            requested_k=request.duration_days,
        )
        s2_duration = (time.perf_counter() - s2_start) * 1000
        stages.append(
            PipelineStageTelemetrySchema(
                stage_name="SPATIAL_CLUSTERING",
                status="SUCCESS",
                duration_ms=round(s2_duration, 2),
                details={
                    "requested_k": request.duration_days,
                    "effective_k": partition_res.effective_k,
                    "total_clustered": partition_res.total_attractions,
                    "total_inertia_km2": partition_res.total_inertia_km2,
                },
            )
        )

        # 4. Stage 3: Google OR-Tools Route Optimization & Constraint Scheduling (Phase 6)
        s3_start = time.perf_counter()
        opt_req = MultiDayTripOptimizationRequest(
            destination_id=request.destination_id,
            clusters=partition_res.clusters,
            start_date=request.start_date,
            preferred_transport=request.preferred_transport,
            pace=request.pace,
            day_start_time="09:00",
            total_budget=request.total_budget,
            party_size=request.party_size,
            mcdm_scores_map=mcdm_scores_map,
        )
        optimized_itinerary = self.optimizer.optimize_multi_day_trip(opt_req)
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
                },
            )
        )

        # 5. Stage 4: Database Persistence (Phase 7)
        s4_start = time.perf_counter()
        trip_title = f"{dest.name} {request.duration_days}-Day Trip"
        trip = Trip(
            creator_id=user_id,
            destination_id=request.destination_id,
            title=trip_title,
            start_date=request.start_date,
            end_date=request.start_date,
            number_of_days=request.duration_days,
            party_size=request.party_size,
            total_budget=request.total_budget,
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

        db_itinerary = Itinerary(
            trip_id=trip.id,
            version=1,
            is_current=True,
            total_estimated_cost=optimized_itinerary.total_estimated_cost,
            total_travel_distance_km=optimized_itinerary.total_travel_distance_km,
            total_travel_duration_hours=optimized_itinerary.total_travel_duration_hours,
            total_sightseeing_duration_hours=optimized_itinerary.total_sightseeing_duration_hours,
            optimization_metrics={
                "distance_reduction_pct": optimized_itinerary.aggregate_distance_reduction_pct,
                "total_scheduled_attractions": optimized_itinerary.total_scheduled_attractions,
                "total_deferred_attractions": optimized_itinerary.total_deferred_attractions,
            },
        )
        db.add(db_itinerary)
        db.flush()

        for day in optimized_itinerary.days:
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

        db.commit()
        s4_duration = (time.perf_counter() - s4_start) * 1000
        stages.append(
            PipelineStageTelemetrySchema(
                stage_name="DATABASE_PERSISTENCE",
                status="SUCCESS",
                duration_ms=round(s4_duration, 2),
                details={"trip_id": trip.id, "itinerary_id": db_itinerary.id, "version": 1},
            )
        )

        # 6. Stage 5: Factual Natural Language Explanation (Phase 7)
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
            candidate_attractions_count=len(all_attractions),
            recommended_attractions_count=len(candidate_entities),
            clusters_count=partition_res.effective_k,
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
            version=1,
            title=trip_title,
            destination_id=request.destination_id,
            constraints=constraints_schema,
            itinerary=optimized_itinerary,
            diagnostics=diagnostics,
            explanation=explanation,
        )
