"""
Unit tests for Database Seeder and Seed Data Integrity.
"""

from app.utils.seed import seed_database
from app.models.destination import Destination, SeasonalData
from app.models.attraction import AttractionCategory, Attraction
from app.models.user import User


def test_seed_database_execution(db_session):
    """Verify that seed_database inserts all curated entities and enforces provenance."""
    stats = seed_database(db_session)

    assert stats["destinations"] == 4
    assert stats["categories"] == 5
    assert stats["seasonal_records"] == 48
    assert stats["total_attractions"] >= 34
    assert stats["users"] >= 1

    # Verify destinations exist
    destinations = db_session.query(Destination).all()
    dest_ids = [d.id for d in destinations]
    assert "dandeli" in dest_ids
    assert "coorg" in dest_ids
    assert "hampi" in dest_ids
    assert "goa" in dest_ids

    # Verify all attractions have valid coordinates, non-negative fees, and provenance
    attractions = db_session.query(Attraction).all()
    for attr in attractions:
        assert attr.latitude != 0.0
        assert attr.longitude != 0.0
        assert attr.entry_fee >= 0.0
        assert attr.average_visit_duration > 0.0
        assert attr.popularity_score >= 0.0 and attr.popularity_score <= 1.0
        assert isinstance(attr.provenance, dict)
        assert "verification_date" in attr.provenance or "source" in attr.provenance
        assert attr.duration_estimation_method is not None

    # Verify 12 seasonal climate records per destination
    for dest_id in ["dandeli", "coorg", "hampi", "goa"]:
        records = db_session.query(SeasonalData).filter(SeasonalData.destination_id == dest_id).all()
        assert len(records) == 12
        months = [r.month for r in records]
        assert set(months) == set(range(1, 13))


def test_seed_idempotency(db_session):
    """Verify that executing the seeder multiple times does not produce duplicate records."""
    stats_first = seed_database(db_session)
    stats_second = seed_database(db_session)

    # Second pass should not create additional destinations or categories
    assert stats_second["destinations"] == 0
    assert stats_second["categories"] == 0
    assert stats_second["seasonal_records"] == 0
    assert stats_second["total_attractions"] == 0
    assert stats_second["users"] == 0
