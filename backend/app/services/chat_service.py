"""
Chat, Conversational AI, and Smart Replanning Business Logic Service.
Orchestrates natural language parsing, the deterministic recommendation/clustering/routing pipeline,
diff calculation, and database persistence.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage
from app.models.trip import Trip, TripPreference
from app.models.itinerary import Itinerary, ItineraryDay, ItineraryItem
from app.models.destination import Destination
from app.models.attraction import Attraction
from app.algorithms.conversation import ConversationalEngine
from app.algorithms.recommender import MCDMRecommender
from app.algorithms.clustering import SpatialDayClusterer
from app.algorithms.route_optimizer import IntraDayRouteOptimizer
from app.schemas.chat import (
    ChatSessionCreateRequest,
    SendMessageRequest,
    SendMessageResponse,
    ExtractedTripConstraintsSchema,
    ReplanningDiffSchema,
    ConstraintChangeItemSchema,
    RemovedAttractionItemSchema,
    AddedAttractionItemSchema,
    MovedAttractionItemSchema,
)
from app.schemas.optimization import (
    MultiDayTripOptimizationRequest,
    MultiDayTripOptimizationResponse,
)
from app.core.exceptions import EntityNotFoundException, AuthorizationException


class ChatService:
    def __init__(self):
        self.conversation_engine = ConversationalEngine()
        self.recommender = MCDMRecommender()
        self.clusterer = SpatialDayClusterer()
        self.optimizer = IntraDayRouteOptimizer()

    def create_session(
        self, db: Session, user_id: str, request: ChatSessionCreateRequest
    ) -> ChatSession:
        """Create a new conversational planning session for a user."""
        session = ChatSession(
            user_id=user_id,
            trip_id=request.trip_id,
            title=request.title or "Trip Planning Chat",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_user_sessions(self, db: Session, user_id: str) -> List[ChatSession]:
        """List all chat sessions belonging to the user."""
        return (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .all()
        )

    def get_session_by_id(self, db: Session, session_id: str, user_id: str) -> ChatSession:
        """Fetch a specific chat session, verifying ownership."""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise EntityNotFoundException("ChatSession", session_id)
        if session.user_id != user_id:
            raise AuthorizationException("Not authorized to access this chat session")
        return session

    def _persist_optimized_itinerary(
        self,
        db: Session,
        user_id: str,
        constraints: ExtractedTripConstraintsSchema,
        itinerary_data: MultiDayTripOptimizationResponse,
        session: ChatSession,
    ) -> str:
        """
        Persist the generated itinerary hierarchy into the database.
        """
        # 1. Find or create trip
        trip = None
        if session.trip_id:
            trip = db.query(Trip).filter(Trip.id == session.trip_id).first()

        if not trip:
            dest = db.query(Destination).filter(Destination.id == constraints.destination_id).first()
            dest_name = dest.name if dest else (constraints.destination_name or "Trip")
            trip = Trip(
                creator_id=user_id,
                destination_id=constraints.destination_id or "hampi",
                title=f"{dest_name} {constraints.duration_days or 3}-Day Trip",
                start_date=constraints.start_date or "2026-11-01",
                end_date="2026-11-03",
                number_of_days=constraints.duration_days or 3,
                total_budget=constraints.total_budget or 15000.0,
                party_size=constraints.party_size or 1,
            )
            db.add(trip)
            db.flush()

            # Create preferences
            pref = TripPreference(
                trip_id=trip.id,
                interests=constraints.interests or ["heritage"],
                pace=constraints.pace or "Moderate",
                preferred_transport=constraints.preferred_transport or "auto",
                budget_tier=constraints.budget_tier or "standard",
            )
            db.add(pref)
            db.flush()

            session.trip_id = trip.id
            db.add(session)

        # 2. Mark previous itineraries as non-current
        db.query(Itinerary).filter(Itinerary.trip_id == trip.id).update({"is_current": False})

        # Calculate version
        latest_itinerary = (
            db.query(Itinerary)
            .filter(Itinerary.trip_id == trip.id)
            .order_by(Itinerary.version.desc())
            .first()
        )
        version = (latest_itinerary.version + 1) if latest_itinerary else 1

        # 3. Create Itinerary
        db_itinerary = Itinerary(
            trip_id=trip.id,
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

        db.commit()
        return db_itinerary.id

    def _compute_replanning_diff(
        self,
        prev_constraints: ExtractedTripConstraintsSchema,
        new_constraints: ExtractedTripConstraintsSchema,
        prev_itinerary: MultiDayTripOptimizationResponse,
        new_itinerary: MultiDayTripOptimizationResponse,
    ) -> ReplanningDiffSchema:
        """
        Compute deterministic structured diff between previous and updated itineraries.
        """
        changes: List[ConstraintChangeItemSchema] = []

        # 1. Compare Constraints
        for field in ["duration_days", "total_budget", "party_size", "pace", "preferred_transport"]:
            old_val = getattr(prev_constraints, field, None)
            new_val = getattr(new_constraints, field, None)
            if old_val != new_val and old_val is not None and new_val is not None:
                changes.append(
                    ConstraintChangeItemSchema(field=field, old_value=old_val, new_value=new_val)
                )

        # 2. Compare Attraction Sets & Daily Placements
        prev_attraction_days: Dict[str, Tuple[str, int]] = {}
        for day in prev_itinerary.days:
            for item in day.items:
                prev_attraction_days[item.attraction.id] = (item.attraction.name, day.day_number)

        new_attraction_days: Dict[str, Tuple[str, int]] = {}
        for day in new_itinerary.days:
            for item in day.items:
                new_attraction_days[item.attraction.id] = (item.attraction.name, day.day_number)

        removed: List[RemovedAttractionItemSchema] = []
        for a_id, (name, day_num) in prev_attraction_days.items():
            if a_id not in new_attraction_days:
                reason = "Removed due to reduced trip duration or budget/time limit adjustment."
                removed.append(RemovedAttractionItemSchema(attraction_id=a_id, name=name, reason=reason))

        added: List[AddedAttractionItemSchema] = []
        for a_id, (name, day_num) in new_attraction_days.items():
            if a_id not in prev_attraction_days:
                reason = "Added to fill optimal daily schedule capacity."
                added.append(AddedAttractionItemSchema(attraction_id=a_id, name=name, day_number=day_num, reason=reason))

        moved: List[MovedAttractionItemSchema] = []
        for a_id, (name, new_day) in new_attraction_days.items():
            if a_id in prev_attraction_days:
                old_day = prev_attraction_days[a_id][1]
                if old_day != new_day:
                    moved.append(MovedAttractionItemSchema(attraction_id=a_id, name=name, from_day=old_day, to_day=new_day))

        # 3. Numeric Deltas
        dist_diff = round(new_itinerary.total_travel_distance_km - prev_itinerary.total_travel_distance_km, 2)
        time_diff = round(new_itinerary.total_travel_duration_hours - prev_itinerary.total_travel_duration_hours, 2)
        cost_diff = round(new_itinerary.total_estimated_cost - prev_itinerary.total_estimated_cost, 2)

        reasoning = []
        if changes:
            reasoning.append(f"Updated constraints ({len(changes)} modified)")
        if removed:
            reasoning.append(f"Pruned {len(removed)} attractions to accommodate new limits")
        if moved:
            reasoning.append(f"Re-clustered and moved {len(moved)} attractions across days")

        return ReplanningDiffSchema(
            is_replanned=True,
            changed_constraints=changes,
            removed_attractions=removed,
            added_attractions=added,
            moved_attractions=moved,
            distance_change_km=dist_diff,
            travel_time_change_hours=time_diff,
            budget_change=cost_diff,
            reasoning=reasoning,
        )

    def process_message(
        self, db: Session, session_id: str, user_id: str, request: SendMessageRequest
    ) -> SendMessageResponse:
        """
        Process incoming conversational request, orchestrating NLU, pipeline execution,
        smart replanning diffing, itinerary persistence, and factual explanation generation.
        """
        session = self.get_session_by_id(db, session_id, user_id)

        # 1. Save User Message
        user_msg = ChatMessage(
            session_id=session.id,
            sender="user",
            content=request.content,
            extracted_constraints={},
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # 2. Retrieve session history & previous state
        prev_constraints = None
        prev_itinerary_data = None

        past_msgs = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

        for m in past_msgs:
            if m.extracted_constraints and isinstance(m.extracted_constraints, dict):
                if m.extracted_constraints.get("destination_id"):
                    prev_constraints = ExtractedTripConstraintsSchema.model_validate(m.extracted_constraints)

        # 3. NLU Constraint Extraction
        current_constraints = self.conversation_engine.extract_constraints(
            request.content, previous_constraints=prev_constraints
        )

        user_msg.extracted_constraints = current_constraints.model_dump()
        db.add(user_msg)
        db.commit()

        # 4. Clarification check
        if not current_constraints.is_complete:
            clarification_text = current_constraints.clarification_question or (
                "Could you specify which destination you'd like to visit and for how many days?"
            )
            assistant_msg = ChatMessage(
                session_id=session.id,
                sender="assistant",
                content=clarification_text,
                extracted_constraints=current_constraints.model_dump(),
            )
            db.add(assistant_msg)
            db.commit()
            db.refresh(assistant_msg)

            return SendMessageResponse(
                session_id=session.id,
                message_id=assistant_msg.id,
                sender="assistant",
                content=clarification_text,
                extracted_constraints=current_constraints,
                itinerary=None,
                is_clarification=True,
                clarification_question=clarification_text,
            )

        # 5. Deterministic Pipeline Execution
        dest_id = current_constraints.destination_id or "hampi"
        duration_k = current_constraints.duration_days or 3
        transport = current_constraints.preferred_transport or "auto"
        pace = current_constraints.pace or "Moderate"
        budget = current_constraints.total_budget or 15000.0
        party_size = current_constraints.party_size or 1

        # A. Phase 4: Fetch Candidate Attractions & MCDM Ranking
        all_attractions = db.query(Attraction).filter(Attraction.destination_id == dest_id).all()
        if not all_attractions:
            raise EntityNotFoundException("Attractions for destination", dest_id)

        from app.schemas.recommendation import RecommendationRequest
        rec_req = RecommendationRequest(
            destination_id=dest_id,
            travel_month=current_constraints.travel_month or 11,
            interests=current_constraints.interests or ["heritage"],
            total_budget=budget,
            number_of_days=duration_k,
            party_size=party_size,
        )

        scored_candidates = self.recommender.rank_attractions(
            attractions=all_attractions,
            request=rec_req,
        )

        max_candidates = min(len(all_attractions), duration_k * 4)
        scored_subset = scored_candidates[:max_candidates]
        candidate_attr_entities = [sc.attraction for sc in scored_subset]
        mcdm_scores_map = {sc.attraction.id: sc.composite_score for sc in scored_subset}

        # B. Phase 5: Spatial K-Means Day Partitioning
        partition_res = self.clusterer.partition_days(
            destination_id=dest_id,
            attractions=candidate_attr_entities,
            requested_k=duration_k,
        )

        # C. Phase 6: OR-Tools Route Optimization & Constraint Scheduling
        opt_req = MultiDayTripOptimizationRequest(
            destination_id=dest_id,
            clusters=partition_res.clusters,
            start_date=current_constraints.start_date or "2026-11-01",
            preferred_transport=transport,
            pace=pace,
            day_start_time="09:00",
            total_budget=budget,
            party_size=party_size,
            mcdm_scores_map=mcdm_scores_map,
        )
        optimized_itinerary = self.optimizer.optimize_multi_day_trip(opt_req)

        # 6. Smart Replanning Diff
        replanning_diff = None
        if prev_constraints and prev_constraints.is_complete and session.trip_id:
            # Reconstruct previous itinerary summary from DB if available
            prev_db_itinerary = (
                db.query(Itinerary)
                .filter(Itinerary.trip_id == session.trip_id)
                .order_by(Itinerary.version.desc())
                .first()
            )
            if prev_db_itinerary:
                # We have a valid prior itinerary state to compare against
                replanning_diff = self._compute_replanning_diff_from_db(
                    prev_constraints, current_constraints, prev_db_itinerary, optimized_itinerary
                )

        # 7. Itinerary Persistence
        persisted_id = self._persist_optimized_itinerary(
            db=db,
            user_id=user_id,
            constraints=current_constraints,
            itinerary_data=optimized_itinerary,
            session=session,
        )

        # 8. Natural Language Explanation
        explanation = self.conversation_engine.generate_explanation(
            itinerary=optimized_itinerary,
            replanning_diff=replanning_diff,
        )

        # 9. Save Assistant Message
        assistant_msg = ChatMessage(
            session_id=session.id,
            sender="assistant",
            content=explanation,
            extracted_constraints=current_constraints.model_dump(),
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)

        return SendMessageResponse(
            session_id=session.id,
            message_id=assistant_msg.id,
            sender="assistant",
            content=explanation,
            extracted_constraints=current_constraints,
            itinerary=optimized_itinerary,
            persisted_itinerary_id=persisted_id,
            replanning_diff=replanning_diff,
            is_clarification=False,
            clarification_question=None,
        )

    def _compute_replanning_diff_from_db(
        self,
        prev_constraints: ExtractedTripConstraintsSchema,
        new_constraints: ExtractedTripConstraintsSchema,
        prev_db_itinerary: Itinerary,
        new_itinerary: MultiDayTripOptimizationResponse,
    ) -> ReplanningDiffSchema:
        """
        Compute diff between previous database itinerary and newly optimized itinerary.
        """
        changes = []
        for field in ["duration_days", "total_budget", "party_size", "pace", "preferred_transport"]:
            old_val = getattr(prev_constraints, field, None)
            new_val = getattr(new_constraints, field, None)
            if old_val != new_val and old_val is not None and new_val is not None:
                changes.append(
                    ConstraintChangeItemSchema(field=field, old_value=old_val, new_value=new_val)
                )

        # Extract previous stops
        prev_stops: Dict[str, int] = {}
        for day in prev_db_itinerary.days:
            for item in day.items:
                prev_stops[item.attraction_id] = day.day_number

        # Extract new stops
        new_stops: Dict[str, Tuple[str, int]] = {}
        for day in new_itinerary.days:
            for item in day.items:
                new_stops[item.attraction.id] = (item.attraction.name, day.day_number)

        removed = []
        for a_id, old_day in prev_stops.items():
            if a_id not in new_stops:
                removed.append(
                    RemovedAttractionItemSchema(
                        attraction_id=a_id,
                        name=a_id.replace("_", " ").title(),
                        reason="Adjusted due to duration/budget replanning.",
                    )
                )

        moved = []
        for a_id, (name, new_day) in new_stops.items():
            if a_id in prev_stops:
                old_day = prev_stops[a_id]
                if old_day != new_day:
                    moved.append(
                        MovedAttractionItemSchema(attraction_id=a_id, name=name, from_day=old_day, to_day=new_day)
                    )

        dist_diff = round(new_itinerary.total_travel_distance_km - prev_db_itinerary.total_travel_distance_km, 2)
        time_diff = round(new_itinerary.total_travel_duration_hours - prev_db_itinerary.total_travel_duration_hours, 2)
        cost_diff = round(new_itinerary.total_estimated_cost - prev_db_itinerary.total_estimated_cost, 2)

        return ReplanningDiffSchema(
            is_replanned=True,
            changed_constraints=changes,
            removed_attractions=removed,
            added_attractions=[],
            moved_attractions=moved,
            distance_change_km=dist_diff,
            travel_time_change_hours=time_diff,
            budget_change=cost_diff,
            reasoning=[f"Updated itinerary following changes to {', '.join([c.field for c in changes])}"],
        )
