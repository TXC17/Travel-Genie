"""
Unit tests for Database Seeder and Seed Data Integrity.
"""

import json
from app.utils.seed import seed_database, get_data_dir
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
    assert stats["accommodations"] >= 16

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
    assert stats_second["accommodations"] == 0


def test_destinations_and_transport_rates_provenance_schema():
    """Verify data provenance documentation for destination coordinates and local transport rates."""
    data_dir = get_data_dir()

    # 1. Verify destinations.json provenance
    dest_path = data_dir / "destinations.json"
    with open(dest_path, "r", encoding="utf-8") as f:
        destinations = json.load(f)

    assert len(destinations) == 4
    for d in destinations:
        assert "provenance" in d
        prov = d["provenance"]
        assert "coordinates_source" in prov
        assert "coordinate_type" in prov
        assert prov["verification_status"] in ["SUBSTANTIATED_BENCHMARK", "UNVERIFIED"]
        # Confirm Hampi, Coorg, and Goa are substantiated benchmarks while Dandeli is an empirical centroid
        if d["id"] in ["hampi", "coorg", "goa"]:
            assert prov["verification_status"] == "SUBSTANTIATED_BENCHMARK"
        else:
            assert prov["verification_status"] == "UNVERIFIED"
            assert d["id"] == "dandeli"

    # 2. Verify transport_rates.json provenance and numeric preservation
    rates_path = data_dir / "transport_rates.json"
    with open(rates_path, "r", encoding="utf-8") as f:
        rates = json.load(f)

    assert set(rates.keys()) == {"walking", "auto", "taxi", "rental", "public"}

    # Verify preserved numeric rates
    assert rates["walking"]["speed_kmh"] == 4.5
    assert rates["auto"]["speed_kmh"] == 25.0
    assert rates["auto"]["base_fare"] == 30.0
    assert rates["auto"]["per_km_rate"] == 15.0
    assert rates["taxi"]["speed_kmh"] == 35.0
    assert rates["taxi"]["base_fare"] == 150.0
    assert rates["taxi"]["per_km_rate"] == 20.0
    assert rates["rental"]["daily_base_cost"] == 1200.0
    assert rates["rental"]["per_km_fuel"] == 6.0
    assert rates["public"]["base_fare"] == 15.0
    assert rates["public"]["per_km_rate"] == 4.0

    # Verify provenance metadata on each transport mode
    for mode, data in rates.items():
        assert "provenance" in data
        prov = data["provenance"]
        assert "method" in prov
        assert "rate_type" in prov
        assert "source" in prov
        assert "verification_status" in prov
        assert prov["verification_status"] in ["VERIFIED_BENCHMARK", "EMPIRICAL_ESTIMATE", "UNVERIFIED_ASSUMPTION"]
