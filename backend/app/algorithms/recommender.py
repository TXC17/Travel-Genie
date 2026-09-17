"""
Multi-Criteria Decision Making (MCDM) Explainable Recommender Algorithm.
Ranks candidate attractions using multi-attribute utility theory, cosine interest matching,
seasonal climate filters, popularity heuristics, and budget constraints.
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from app.models.attraction import Attraction
from app.schemas.recommendation import (
    MCDMWeightsSchema,
    ScoreBreakdown,
    ScoredAttractionResponse,
    RecommendationRequest,
)
from app.schemas.attraction import AttractionResponse


class MCDMRecommender:
    """
    Deterministic, transparent Multi-Criteria Decision Making (MCDM) engine.
    Calculates weighted utility scores and generates structured attribution proofs.
    """

    MONTH_NAMES = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December",
    }

    def __init__(self, default_weights: Optional[MCDMWeightsSchema] = None):
        self.weights = default_weights or MCDMWeightsSchema()

    def compute_interest_similarity(
        self, user_interests: List[str], attraction_category: str, attraction_tags: List[str]
    ) -> float:
        """
        Compute cosine similarity between user interest profile vector and attraction semantic tags.
        """
        if not user_interests:
            return 0.5  # Neutral prior if no specific interests stated

        user_set = {i.lower().strip() for i in user_interests}
        
        # Build binary/term frequency attraction features dictionary
        attr_terms = {attraction_category.lower().strip(): 1.0}
        for tag in attraction_tags:
            tag_clean = tag.lower().strip()
            attr_terms[tag_clean] = 1.0

        # Feature vocabulary across union of terms
        vocabulary = list(user_set.union(attr_terms.keys()))
        
        user_vec = [1.0 if term in user_set else 0.0 for term in vocabulary]
        attr_vec = [attr_terms.get(term, 0.0) for term in vocabulary]

        dot_product = sum(u * a for u, a in zip(user_vec, attr_vec))
        mag_user = math.sqrt(sum(u * u for u in user_vec))
        mag_attr = math.sqrt(sum(a * a for a in attr_vec))

        if mag_user == 0 or mag_attr == 0:
            return 0.0

        similarity = dot_product / (mag_user * mag_attr)
        return round(min(1.0, max(0.0, similarity)), 4)

    def compute_season_score(
        self, attraction: Attraction, travel_month: int
    ) -> float:
        """
        Fetch seasonal suitability score for target month M in [1, 12].
        """
        seasonal_map = attraction.seasonal_scores or {}
        month_key = str(travel_month)
        
        if month_key in seasonal_map:
            return float(seasonal_map[month_key])
        
        return 0.75

    def compute_budget_score(
        self, attraction_fee: float, total_budget: float, number_of_days: int, party_size: int
    ) -> float:
        """
        Compute budget affordability score comparing entry fee against daily sightseeing threshold.
        Uses a smooth monotonic utility curve: S_budget = 1.0 / (1.0 + (Fee / B_thresh)).
        """
        if attraction_fee <= 0.0:
            return 1.0

        effective_party = max(1, party_size)
        effective_days = max(1, number_of_days)
        
        daily_budget_per_person = (total_budget * 0.25) / (effective_party * effective_days)
        per_attraction_threshold = max(50.0, daily_budget_per_person / 3.0)

        # Smooth diminishing utility curve strictly bounded in (0.0, 1.0]
        ratio = attraction_fee / per_attraction_threshold
        return round(1.0 / (1.0 + (0.5 * ratio)), 4)

    def generate_explanation(
        self,
        attraction: Attraction,
        breakdown: Dict[str, float],
        travel_month: int,
    ) -> str:
        """
        Generate deterministic explainability text justifying why this attraction was recommended.
        """
        month_name = self.MONTH_NAMES.get(travel_month, f"Month {travel_month}")
        reasons = []

        if breakdown["interest_score"] >= 0.60:
            reasons.append(f"Strong match for category '{attraction.category}'")
        elif breakdown["interest_score"] >= 0.35:
            reasons.append(f"Aligns with travel preferences in '{attraction.category}'")

        if breakdown["season_score"] >= 0.90:
            reasons.append(f"Peak seasonal conditions in {month_name}")
        elif breakdown["season_score"] <= 0.40:
            reasons.append(f"Sub-optimal weather conditions in {month_name}")

        if attraction.entry_fee == 0.0:
            reasons.append("Free admission")
        elif breakdown["budget_score"] >= 0.85:
            reasons.append(f"Nominal admission fee (₹{int(attraction.entry_fee)})")

        if breakdown["popularity_score"] >= 0.85:
            reasons.append("Highly rated marquee landmark")

        return "; ".join(reasons) if reasons else "Recommended based on overall multi-criteria balance."

    def rank_attractions(
        self,
        attractions: List[Attraction],
        request: RecommendationRequest,
    ) -> List[ScoredAttractionResponse]:
        """
        Evaluate and rank candidate attractions using MCDM weighted utility scoring.
        """
        weights = request.custom_weights or self.weights
        total_weight = (
            weights.weight_interest
            + weights.weight_season
            + weights.weight_popularity
            + weights.weight_rating
            + weights.weight_budget
        )
        if total_weight <= 0:
            total_weight = 1.0

        scored_results: List[Tuple[float, Attraction, ScoreBreakdown]] = []

        for attr in attractions:
            # 1. Interest Matching
            s_interest = self.compute_interest_similarity(
                request.interests, attr.category, attr.tags or []
            )

            # 2. Seasonal Climate Suitability
            s_season = self.compute_season_score(attr, request.travel_month)

            # 3. Normalized Popularity
            s_pop = min(1.0, max(0.0, float(attr.popularity_score or 0.5)))

            # 4. Normalized Star Rating (Rating / 5.0)
            s_rating = min(1.0, max(0.0, float(attr.rating or 4.0) / 5.0))

            # 5. Budget Affordability
            s_budget = self.compute_budget_score(
                float(attr.entry_fee or 0.0),
                request.total_budget,
                request.number_of_days,
                request.party_size,
            )

            # Weighted Composite Sum
            composite = (
                (weights.weight_interest * s_interest)
                + (weights.weight_season * s_season)
                + (weights.weight_popularity * s_pop)
                + (weights.weight_rating * s_rating)
                + (weights.weight_budget * s_budget)
            ) / total_weight

            breakdown_dict = {
                "interest_score": round(s_interest, 3),
                "season_score": round(s_season, 3),
                "popularity_score": round(s_pop, 3),
                "rating_score": round(s_rating, 3),
                "budget_score": round(s_budget, 3),
                "composite_score": round(composite, 3),
            }

            reason_text = self.generate_explanation(attr, breakdown_dict, request.travel_month)
            breakdown_obj = ScoreBreakdown(
                interest_score=breakdown_dict["interest_score"],
                season_score=breakdown_dict["season_score"],
                popularity_score=breakdown_dict["popularity_score"],
                rating_score=breakdown_dict["rating_score"],
                budget_score=breakdown_dict["budget_score"],
                composite_score=breakdown_dict["composite_score"],
                reason=reason_text,
            )

            scored_results.append((composite, attr, breakdown_obj))

        # Sort descending by composite score, then by popularity
        scored_results.sort(
            key=lambda item: (item[0], item[1].popularity_score), reverse=True
        )

        response_list: List[ScoredAttractionResponse] = []
        for rank, (score, attr, breakdown) in enumerate(scored_results, start=1):
            response_list.append(
                ScoredAttractionResponse(
                    attraction=AttractionResponse.model_validate(attr),
                    composite_score=round(score, 3),
                    rank=rank,
                    breakdown=breakdown,
                    weights_used=weights,
                )
            )

        return response_list
