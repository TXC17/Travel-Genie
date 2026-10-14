"""
Chat, Conversational AI, and Smart Replanning Business Logic Service.
Orchestrates natural language parsing, the deterministic recommendation/clustering/routing pipeline,
diff calculation, and database persistence.
"""

from datetime import date, timedelta
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
from app.services.pipeline_service import PlanningPipelineService
from app.core.exceptions import EntityNotFoundException, AuthorizationException


class ChatService:
    def __init__(self):
        self.conversation_engine = ConversationalEngine()
        self.recommender = MCDMRecommender()
        self.clusterer = SpatialDayClusterer()
        self.optimizer = IntraDayRouteOptimizer()
        self.pipeline_service = PlanningPipelineService()

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

    def update_session_title(
        self, db: Session, session_id: str, user_id: str, title: str
    ) -> ChatSession:
        """Update the title of a specific chat session."""
        session = self.get_session_by_id(db, session_id, user_id)
        session.title = title.strip() or "Travel Plan"
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def delete_session(self, db: Session, session_id: str, user_id: str) -> bool:
        """Delete a chat session and its associated messages."""
        session = self.get_session_by_id(db, session_id, user_id)
        db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
        db.delete(session)
        db.commit()
        return True

    def _persist_optimized_itinerary(
        self,
        db: Session,
        user_id: str,
        constraints: ExtractedTripConstraintsSchema,
        itinerary_data: MultiDayTripOptimizationResponse,
        session: ChatSession,
    ) -> str:
        """
        Persist the generated itinerary hierarchy into the database and synchronize
        parent Trip and TripPreference records during conversational replanning.
        """
        # 1. Find or create trip
        trip = None
        if session.trip_id:
            trip = db.query(Trip).filter(Trip.id == session.trip_id).first()

        dest = db.query(Destination).filter(Destination.id == constraints.destination_id).first()
        dest_name = dest.name if dest else (constraints.destination_name or (constraints.destination_id or "Trip").title())

        duration_val = constraints.duration_days or (trip.number_of_days if trip else 3)
        start_date_val = constraints.start_date or (trip.start_date if trip else "2026-11-01")
        end_date_val = PlanningPipelineService.calculate_persisted_end_date(start_date_val, duration_val)

        if not trip:
            trip = Trip(
                creator_id=user_id,
                destination_id=constraints.destination_id or "hampi",
                title=f"{dest_name} {duration_val}-Day Trip",
                start_date=start_date_val,
                end_date=end_date_val,
                number_of_days=duration_val,
                total_budget=constraints.total_budget or 15000.0,
                party_size=constraints.party_size or 1,
            )
            db.add(trip)
            db.flush()

            # Create preferences
            pref = TripPreference(
                trip_id=trip.id,
                interests=constraints.interests or ["heritage"],
                pace=(constraints.pace.capitalize() if constraints.pace else "Moderate"),
                preferred_transport=constraints.preferred_transport or "auto",
                budget_tier=constraints.budget_tier or "standard",
            )
            db.add(pref)
            db.flush()

            session.trip_id = trip.id
        else:
            # Synchronize existing Trip record
            trip.number_of_days = duration_val
            trip.start_date = start_date_val
            trip.end_date = end_date_val
            if constraints.total_budget is not None:
                trip.total_budget = constraints.total_budget
            if constraints.party_size is not None:
                trip.party_size = constraints.party_size
            if constraints.destination_id is not None and constraints.destination_id != trip.destination_id:
                trip.destination_id = constraints.destination_id

            # Synchronize title if standard title format or duration/destination changed
            trip.title = f"{dest_name} {duration_val}-Day Trip"

            # Synchronize TripPreference
            pref = db.query(TripPreference).filter(TripPreference.trip_id == trip.id).first()
            if not pref:
                pref = TripPreference(
                    trip_id=trip.id,
                    interests=constraints.interests or ["heritage"],
                    pace=(constraints.pace.capitalize() if constraints.pace else "Moderate"),
                    preferred_transport=constraints.preferred_transport or "auto",
                    budget_tier=constraints.budget_tier or "standard",
                )
                db.add(pref)
                db.flush()
            else:
                if constraints.pace is not None:
                    p_val = constraints.pace.capitalize() if isinstance(constraints.pace, str) else constraints.pace
                    if p_val in ["Relaxed", "Moderate", "Intense"]:
                        pref.pace = p_val
                if constraints.preferred_transport is not None:
                    pref.preferred_transport = constraints.preferred_transport
                if constraints.interests is not None and len(constraints.interests) > 0:
                    pref.interests = constraints.interests
                if constraints.budget_tier is not None:
                    pref.budget_tier = constraints.budget_tier
                if constraints.max_daily_travel_hours is not None:
                    pref.max_daily_travel_hours = constraints.max_daily_travel_hours
                if hasattr(pref, "dietary_preference") and hasattr(constraints, "dietary_preference"):
                    d_val = getattr(constraints, "dietary_preference", None)
                    if d_val is not None:
                        setattr(pref, "dietary_preference", d_val)
                db.add(pref)
                db.flush()

            db.add(trip)
            db.flush()

        # Update session title if default
        if session.title in ["New Travel Plan", "Trip Planning Chat", "Trip Planning", ""] or (session.title and "Day Trip" in session.title):
            session.title = f"{dest_name} {duration_val}-Day Trip"
        db.add(session)

        # 2. Delegate itinerary persistence to canonical PlanningPipelineService
        db_itinerary = self.pipeline_service.persist_itinerary(
            db=db,
            trip_id=trip.id,
            itinerary_data=itinerary_data,
        )
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

        # 3. Check for pure greetings / small-talk / help when user is not specifying new constraints
        is_greeting = self.conversation_engine.is_pure_greeting(request.content)
        is_thanks = self.conversation_engine.is_pure_thanks(request.content)
        is_help = self.conversation_engine.is_help_query(request.content)

        if is_thanks:
            reply_text = "You're very welcome! 😊 Let me know if you would like to adjust any stops, change your travel pace, or plan another trip."
            assistant_msg = ChatMessage(
                session_id=session.id,
                sender="assistant",
                content=reply_text,
                extracted_constraints=prev_constraints.model_dump() if prev_constraints else {},
            )
            db.add(assistant_msg)
            db.commit()
            db.refresh(assistant_msg)
            return SendMessageResponse(
                session_id=session.id,
                message_id=assistant_msg.id,
                sender="assistant",
                content=reply_text,
                extracted_constraints=prev_constraints or ExtractedTripConstraintsSchema(is_complete=False, missing_fields=["destination", "duration_days"]),
                itinerary=None,
                is_clarification=True,
                clarification_question=reply_text,
            )

        if is_help:
            reply_text = (
                "I am Travel Genie! 🧞‍♂️ I build mathematically optimal, time-feasible itineraries for "
                "Hampi, Coorg, Dandeli, and Goa using Multi-Criteria Scoring (MCDM), Spatial K-Means clustering, and Google OR-Tools.\n\n"
                "To get started, tell me your destination and duration (e.g. *'Plan a 3-day Hampi trip with auto and ₹15,000 budget'*)."
            )
            assistant_msg = ChatMessage(
                session_id=session.id,
                sender="assistant",
                content=reply_text,
                extracted_constraints=prev_constraints.model_dump() if prev_constraints else {},
            )
            db.add(assistant_msg)
            db.commit()
            db.refresh(assistant_msg)
            return SendMessageResponse(
                session_id=session.id,
                message_id=assistant_msg.id,
                sender="assistant",
                content=reply_text,
                extracted_constraints=prev_constraints or ExtractedTripConstraintsSchema(is_complete=False, missing_fields=["destination", "duration_days"]),
                itinerary=None,
                is_clarification=True,
                clarification_question=reply_text,
            )

        if is_greeting and prev_constraints and prev_constraints.is_complete:
            dest_name = prev_constraints.destination_name or prev_constraints.destination_id.title()
            reply_text = (
                f"Hello! 👋 How can I help you with your {dest_name} trip? "
                f"You can ask to change days (e.g. *'make it 2 days'*), adjust budget (e.g. *'budget below 12000'*), or change transport mode."
            )
            assistant_msg = ChatMessage(
                session_id=session.id,
                sender="assistant",
                content=reply_text,
                extracted_constraints=prev_constraints.model_dump(),
            )
            db.add(assistant_msg)
            db.commit()
            db.refresh(assistant_msg)
            return SendMessageResponse(
                session_id=session.id,
                message_id=assistant_msg.id,
                sender="assistant",
                content=reply_text,
                extracted_constraints=prev_constraints,
                itinerary=None,
                is_clarification=True,
                clarification_question=reply_text,
            )

        # 4. NLU Constraint Extraction
        current_constraints = self.conversation_engine.extract_constraints(
            request.content, previous_constraints=prev_constraints
        )

        user_msg.extracted_constraints = current_constraints.model_dump()
        db.add(user_msg)
        db.commit()

        # 5. Clarification check
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

        # 5. Deterministic Pipeline Execution via Canonical PlanningPipelineService
        dest_id = current_constraints.destination_id or "hampi"
        duration_k = current_constraints.duration_days or 3
        transport = current_constraints.preferred_transport or "auto"
        pace = current_constraints.pace or "Moderate"
        budget = current_constraints.total_budget or 15000.0
        party_size = current_constraints.party_size or 1
        start_date = current_constraints.start_date or "2026-11-01"

        # Check if an existing trip in this session has selected an accommodation
        existing_trip = None
        if session.trip_id:
            existing_trip = db.query(Trip).filter(Trip.id == session.trip_id).first()
        selected_acc_id = existing_trip.selected_accommodation_id if existing_trip else None

        optimized_itinerary, _ = self.pipeline_service.optimize_itinerary_plan(
            db=db,
            destination_id=dest_id,
            duration_days=duration_k,
            start_date=start_date,
            travel_month=current_constraints.travel_month or 11,
            interests=current_constraints.interests or ["heritage"],
            total_budget=budget,
            party_size=party_size,
            preferred_transport=transport,
            pace=pace,
            selected_accommodation_id=selected_acc_id,
            return_to_accommodation=True,
        )

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
