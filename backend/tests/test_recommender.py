"""
Unit and Integration Tests for MCDM Recommender and Seasonal Analytics.
Comprehensive validation covering interest cosine similarity, normalization,
budget sensitivity, seasonal constraints, reproducibility, and edge cases.
"""

import pytest
from fastapi import status
from app.algorithms.recommender import MCDMRecommender
from app.algorithms.seasonal_analyzer import SeasonalAnalyzer
from app.models.attraction import Attraction
from app.schemas.recommendation import (
    RecommendationRequest,
    MCDMWeightsSchema,
)
from app.utils.seed import seed_database


def test_cosine_interest_similarity():
    """Verify mathematical properties of interest cosine similarity."""
    recommender = MCDMRecommender()

    # Single-term user query matching 1 of 4 attraction terms: cos(u, v) = 1 / sqrt(4) = 0.50
    sim_exact = recommender.compute_interest_similarity(
        user_interests=["heritage"],
        attraction_category="heritage",
        attraction_tags=["temple", "unesco", "monument"],
    )
    assert sim_exact == 0.50

    # Multi-term complete match: cos(u, v) = 2 / (sqrt(2) * sqrt(2)) = 1.0
    sim_multi = recommender.compute_interest_similarity(
        user_interests=["heritage", "temple"],
        attraction_category="heritage",
        attraction_tags=["temple"],
    )
    assert sim_multi == 1.0

    # Partial overlap: cos(u, v) = 1 / (sqrt(2) * sqrt(3)) = 0.4082
    sim_partial = recommender.compute_interest_similarity(
        user_interests=["temple", "spiritual"],
        attraction_category="culture_religious",
        attraction_tags=["temple", "prayer"],
    )
    assert 0.40 <= sim_partial <= 0.42

    # Orthogonal non-matching interests
    sim_none = recommender.compute_interest_similarity(
        user_interests=["coastal", "beach"],
        attraction_category="adventure",
        attraction_tags=["rafting", "jungle"],
    )
    assert sim_none == 0.0


def test_empty_missing_interests():
    """Verify that empty or missing user interests yield the neutral 0.5 prior."""
    recommender = MCDMRecommender()
    sim_empty = recommender.compute_interest_similarity(
        user_interests=[],
        attraction_category="nature",
        attraction_tags=["waterfall", "trekking"],
    )
    assert sim_empty == 0.5


def test_popularity_and_rating_normalization():
    """Verify that popularity and star ratings are cleanly normalized to [0.0, 1.0]."""
    recommender = MCDMRecommender()
    attr = Attraction(
        id="test_attr_norm",
        destination_id="coorg",
        category="nature",
        name="Scenic Falls",
        description="Waterfall",
        latitude=12.0,
        longitude=75.0,
        average_visit_duration=1.5,
        entry_fee=50.0,
        popularity_score=0.95,
        rating=4.5,
        tags=["waterfall"],
        seasonal_scores={"12": 1.0},
        duration_estimation_method="curated_empirical_average",
    )
    req = RecommendationRequest(
        destination_id="coorg",
        travel_month=12,
        interests=["nature"],
        total_budget=10000.0,
        number_of_days=2,
        party_size=1,
    )
    ranked = recommender.rank_attractions([attr], req)
    assert len(ranked) == 1
    # 4.5 / 5.0 = 0.90
    assert ranked[0].breakdown.rating_score == 0.90
    # Popularity = 0.95
    assert ranked[0].breakdown.popularity_score == 0.95


def test_budget_scoring_sensitivity():
    """Verify that affordable attractions receive higher budget scores than exorbitant ones."""
    recommender = MCDMRecommender()

    # Free admission (0.0 INR) should always be 1.0
    score_free = recommender.compute_budget_score(
        attraction_fee=0.0, total_budget=5000.0, number_of_days=3, party_size=2
    )
    assert score_free == 1.0

    # Expensive fee (1500 INR) under modest budget should get degraded
    score_expensive = recommender.compute_budget_score(
        attraction_fee=1500.0, total_budget=5000.0, number_of_days=3, party_size=2
    )
    assert score_expensive < score_free
    assert score_expensive < 0.5


def test_seasonal_scoring_and_hard_constraints():
    """Verify that seasonal scores reflect monthly climate curves and penalize monsoon closures."""
    recommender = MCDMRecommender()
    attr = Attraction(
        id="dudhsagar",
        destination_id="goa",
        category="adventure",
        name="Dudhsagar Falls",
        description="Waterfall",
        latitude=15.3,
        longitude=74.3,
        average_visit_duration=4.0,
        entry_fee=500.0,
        popularity_score=0.96,
        rating=4.7,
        tags=["waterfall"],
        seasonal_scores={"7": 0.0, "12": 0.95},
        duration_estimation_method="official_safari_schedule",
    )
    # Month 7 (July monsoon closure)
    score_july = recommender.compute_season_score(attr, travel_month=7)
    assert score_july == 0.0

    # Month 12 (Peak winter season)
    score_dec = recommender.compute_season_score(attr, travel_month=12)
    assert score_dec == 0.95

    # Month without explicit index uses 0.75 fallback
    score_fallback = recommender.compute_season_score(attr, travel_month=4)
    assert score_fallback == 0.75


def test_deterministic_reproducibility(client, db_session):
    """Verify that ranking the same candidate set multiple times produces bit-for-bit identical scores."""
    seed_database(db_session)
    req = {
        "destination_id": "hampi",
        "travel_month": 11,
        "interests": ["heritage", "culture_religious"],
        "total_budget": 12000.0,
        "number_of_days": 3,
        "party_size": 2,
    }
    res1 = client.post("/api/v1/recommendations/attractions", json=req)
    res2 = client.post("/api/v1/recommendations/attractions", json=req)

    assert res1.status_code == status.HTTP_200_OK
    assert res2.status_code == status.HTTP_200_OK
    data1 = res1.json()
    data2 = res2.json()

    assert len(data1) == len(data2)
    for i in range(len(data1)):
        assert data1[i]["attraction"]["id"] == data2[i]["attraction"]["id"]
        assert data1[i]["composite_score"] == data2[i]["composite_score"]
        assert data1[i]["breakdown"] == data2[i]["breakdown"]


def test_edge_case_missing_and_none_values():
    """Verify recommender resilience when attraction has empty tags, zero fee, and None defaults."""
    recommender = MCDMRecommender()
    attr = Attraction(
        id="sparse_attraction",
        destination_id="hampi",
        category="heritage",
        name="Sparse Monument",
        description="Basic description",
        latitude=15.3,
        longitude=76.4,
        average_visit_duration=1.0,
        entry_fee=0.0,
        popularity_score=None,  # Tests None popularity fallback to 0.5
        rating=None,            # Tests None rating fallback to 4.0
        tags=[],                # Empty tags
        seasonal_scores={},     # Empty seasonal map
        duration_estimation_method="curated_empirical_average",
    )
    req = RecommendationRequest(
        destination_id="hampi",
        travel_month=1,
        interests=["heritage"],
        total_budget=5000.0,
        number_of_days=2,
        party_size=1,
    )
    ranked = recommender.rank_attractions([attr], req)
    assert len(ranked) == 1
    assert ranked[0].composite_score > 0.0
    assert ranked[0].breakdown.popularity_score == 0.50
    assert ranked[0].breakdown.rating_score == 0.80  # 4.0 / 5.0


def test_mcdm_custom_weights_sensitivity(client, db_session):
    """Test that adjusting criteria weights directly alters attraction ranking."""
    seed_database(db_session)

    # 1. Heavily favor budget (weight_budget = 1.0, others = 0.0)
    budget_request = {
        "destination_id": "hampi",
        "travel_month": 12,
        "interests": ["heritage"],
        "total_budget": 5000.0,
        "number_of_days": 2,
        "party_size": 1,
        "custom_weights": {
            "weight_interest": 0.0,
            "weight_season": 0.0,
            "weight_popularity": 0.0,
            "weight_rating": 0.0,
            "weight_budget": 1.0,
        },
    }
    res_budget = client.post("/api/v1/recommendations/attractions", json=budget_request)
    assert res_budget.status_code == status.HTTP_200_OK
    data_budget = res_budget.json()
    # Under 100% budget weight, the top items must have INR 0 admission fee
    assert data_budget[0]["attraction"]["entry_fee"] == 0.0
    assert data_budget[0]["breakdown"]["budget_score"] == 1.0

    # 2. Heavily favor popularity (weight_popularity = 1.0, others = 0.0)
    pop_request = {
        "destination_id": "hampi",
        "travel_month": 12,
        "interests": ["heritage"],
        "total_budget": 5000.0,
        "number_of_days": 2,
        "party_size": 1,
        "custom_weights": {
            "weight_interest": 0.0,
            "weight_season": 0.0,
            "weight_popularity": 1.0,
            "weight_rating": 0.0,
            "weight_budget": 0.0,
        },
    }
    res_pop = client.post("/api/v1/recommendations/attractions", json=pop_request)
    assert res_pop.status_code == status.HTTP_200_OK
    data_pop = res_pop.json()
    # Virupaksha / Vittala have highest popularity (0.99)
    assert data_pop[0]["breakdown"]["popularity_score"] >= 0.95


def test_recommendation_explainability_attribution(client, db_session):
    """Verify that recommended attractions contain transparent score breakdowns and reasons."""
    seed_database(db_session)

    req = {
        "destination_id": "coorg",
        "travel_month": 11,
        "interests": ["nature", "culture_religious"],
        "total_budget": 15000.0,
        "number_of_days": 3,
        "party_size": 2,
    }
    response = client.post("/api/v1/recommendations/attractions", json=req)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 10  # All 10 Coorg attractions ranked

    top_item = data[0]
    assert "breakdown" in top_item
    assert "reason" in top_item["breakdown"]
    assert len(top_item["breakdown"]["reason"]) > 0
    assert top_item["composite_score"] >= data[-1]["composite_score"]


def test_seasonal_comparison_and_alternatives(client, db_session):
    """Test comparing destinations across monsoon vs dry winter seasons."""
    seed_database(db_session)

    # In July (monsoon), Goa and Dandeli have high rainfall / water sport restrictions
    res_july = client.get("/api/v1/recommendations/seasonal-compare?travel_month=7&destination_id=goa")
    assert res_july.status_code == status.HTTP_200_OK
    data_july = res_july.json()
    assert data_july["travel_month"] == 7
    assert data_july["travel_month_name"] == "July"
    assert data_july["better_alternatives_available"] is True
    assert len(data_july["destinations_ranked"]) == 4

    # In December (peak winter), Hampi and Goa have optimal conditions
    res_dec = client.get("/api/v1/recommendations/seasonal-compare?travel_month=12&destination_id=hampi")
    assert res_dec.status_code == status.HTTP_200_OK
    data_dec = res_dec.json()
    assert data_dec["better_alternatives_available"] is False
    assert data_dec["destinations_ranked"][0]["suitability_score"] == 1.0


def test_get_mcdm_weights(client):
    """Test retrieving baseline criteria weights."""
    response = client.get("/api/v1/recommendations/weights")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["weight_interest"] == 0.35
    assert data["weight_season"] == 0.25
    assert data["weight_popularity"] == 0.15
    assert data["weight_rating"] == 0.15
    assert data["weight_budget"] == 0.10
