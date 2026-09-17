"""
Unit tests for SQLAlchemy Database Models and Entity Relationships.
"""

from app.models.user import User
from app.models.destination import Destination, SeasonalData
from app.models.attraction import AttractionCategory, Attraction
from app.models.trip import Trip, TripPreference
from app.models.itinerary import Itinerary, ItineraryDay, ItineraryItem
from app.models.collaboration import TripMember, UserVote
from app.models.chat import ChatSession, ChatMessage
from app.core.security import get_password_hash, verify_password


def test_user_password_hashing(db_session):
    """Test user creation and bcrypt password verification."""
    raw_password = "supersecretpassword123"
    hashed = get_password_hash(raw_password)
    user = User(
        email="test@travelgenie.ai",
        hashed_password=hashed,
        full_name="Test Traveler",
    )
    db_session.add(user)
    db_session.commit()

    fetched = db_session.query(User).filter(User.email == "test@travelgenie.ai").first()
    assert fetched is not None
    assert fetched.full_name == "Test Traveler"
    assert verify_password(raw_password, fetched.hashed_password) is True
    assert verify_password("wrongpassword", fetched.hashed_password) is False


def test_destination_and_seasonal_relationship(db_session):
    """Test Destination to SeasonalData cascade and foreign key constraints."""
    dest = Destination(
        id="test_dest",
        name="Test Destination",
        state="Karnataka",
        description="A beautiful test region.",
        latitude=15.0,
        longitude=75.0,
        best_season="November to February",
    )
    seasonal = SeasonalData(
        destination_id="test_dest",
        month=12,
        month_name="December",
        suitability_score=1.0,
        climate_type="Pleasant",
        rainfall_level="Low",
        crowd_demand="High",
        water_sports_available=True,
    )
    dest.seasonal_records.append(seasonal)
    db_session.add(dest)
    db_session.commit()

    fetched_dest = db_session.query(Destination).filter(Destination.id == "test_dest").first()
    assert fetched_dest is not None
    assert len(fetched_dest.seasonal_records) == 1
    assert fetched_dest.seasonal_records[0].month == 12
    assert fetched_dest.seasonal_records[0].suitability_score == 1.0


def test_attraction_provenance_and_category(db_session):
    """Test Attraction model persistence, category relationship, and provenance metadata."""
    category = AttractionCategory(
        id="test_heritage",
        name="Test Heritage",
        description="Historic monuments",
    )
    db_session.add(category)
    db_session.commit()

    attraction = Attraction(
        id="test_monument",
        destination_id="test_dest",
        category="test_heritage",
        category_id="test_heritage",
        name="Ancient Test Monument",
        description="Remarkable monolithic stone sculpture.",
        latitude=15.33,
        longitude=76.46,
        average_visit_duration=2.0,
        entry_fee=40.0,
        popularity_score=0.95,
        rating=4.8,
        tags=["heritage", "monument"],
        provenance={
            "coordinates_source": "OpenStreetMap Node Benchmark",
            "fee_source": "ASI Monument Notification",
            "verification_date": "2026-08",
        },
        is_verified=True,
        duration_estimation_method="curated_empirical_average",
    )
    db_session.add(attraction)
    db_session.commit()

    fetched = db_session.query(Attraction).filter(Attraction.id == "test_monument").first()
    assert fetched is not None
    assert fetched.name == "Ancient Test Monument"
    assert fetched.is_verified is True
    assert fetched.provenance["fee_source"] == "ASI Monument Notification"
    assert fetched.category_rel.name == "Test Heritage"


def test_trip_and_itinerary_hierarchy(db_session):
    """Test full Trip -> Preference -> Itinerary -> Day -> Item hierarchy."""
    user = User(
        email="hierarchy_user@travelgenie.ai",
        hashed_password=get_password_hash("pass123"),
        full_name="Hierarchy User",
    )
    dest = Destination(
        id="test_dest_2",
        name="Test Destination 2",
        state="Karnataka",
        description="A beautiful test region.",
        latitude=15.0,
        longitude=75.0,
        best_season="November to February",
    )
    attr = Attraction(
        id="test_monument_2",
        destination_id="test_dest_2",
        category="heritage",
        name="Ancient Test Monument 2",
        description="Monolithic stone sculpture.",
        latitude=15.33,
        longitude=76.46,
        average_visit_duration=2.0,
        entry_fee=40.0,
        is_verified=True,
        duration_estimation_method="curated_empirical_average",
    )
    db_session.add_all([user, dest, attr])
    db_session.commit()

    trip = Trip(
        creator_id=user.id,
        destination_id="test_dest_2",
        title="3-Day Historical Excursion",
        start_date="2026-11-10",
        end_date="2026-11-12",
        number_of_days=3,
        party_size=2,
        total_budget=15000.0,
    )
    pref = TripPreference(
        interests=["heritage", "nature"],
        pace="Moderate",
        preferred_transport="auto",
        max_daily_travel_hours=4.0,
    )
    trip.preferences = pref

    itinerary = Itinerary(
        version=1,
        total_estimated_cost=8400.0,
        total_travel_distance_km=42.5,
        total_travel_duration_hours=2.5,
        total_sightseeing_duration_hours=14.0,
        optimization_metrics={"distance_reduction_pct": 32.4},
    )
    day1 = ItineraryDay(
        day_number=1,
        date="2026-11-10",
        cluster_id=0,
        day_travel_distance_km=14.0,
        day_travel_duration_hours=0.8,
        day_sightseeing_duration_hours=5.0,
        day_estimated_cost=2800.0,
        recommended_transport="auto",
    )
    item1 = ItineraryItem(
        attraction_id="test_monument",
        visit_order=1,
        arrival_time="09:00",
        departure_time="11:00",
        visit_duration_hours=2.0,
        item_cost=80.0,
        crowd_estimate_score=0.45,
        crowd_level="Moderate",
    )
    day1.items.append(item1)
    itinerary.days.append(day1)
    trip.itineraries.append(itinerary)

    db_session.add(trip)
    db_session.commit()

    fetched_trip = db_session.query(Trip).filter(Trip.id == trip.id).first()
    assert fetched_trip is not None
    assert fetched_trip.preferences.pace == "Moderate"
    assert len(fetched_trip.itineraries) == 1
    assert len(fetched_trip.itineraries[0].days) == 1
    assert fetched_trip.itineraries[0].days[0].items[0].attraction_id == "test_monument"
