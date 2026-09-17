"""
Seasonal Climate and Multi-Destination Suitability Analyzer.
Evaluates weather matrices, identifies climate advisories (monsoon, extreme heat),
and computes destination suitability rankings for any given month of the year.
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.destination import Destination, SeasonalData
from app.schemas.recommendation import (
    DestinationSeasonalComparisonItem,
    SeasonalComparisonResponse,
)


class SeasonalAnalyzer:
    """
    Evaluates weather suitability, generates warnings, and recommends optimal destinations by month.
    """

    MONTH_NAMES = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December",
    }

    @staticmethod
    def compare_destinations_by_month(
        db: Session, travel_month: int, selected_destination_id: Optional[str] = None
    ) -> SeasonalComparisonResponse:
        """
        Rank all supported destinations for a given travel month and check if better alternatives exist.
        """
        month_name = SeasonalAnalyzer.MONTH_NAMES.get(travel_month, f"Month {travel_month}")

        # Query all active seasonal records for this month
        records = (
            db.query(SeasonalData, Destination)
            .join(Destination, SeasonalData.destination_id == Destination.id)
            .filter(SeasonalData.month == travel_month)
            .filter(Destination.is_active == True)
            .all()
        )

        ranked_items: List[DestinationSeasonalComparisonItem] = []
        selected_item: Optional[DestinationSeasonalComparisonItem] = None

        for seasonal, dest in records:
            item = DestinationSeasonalComparisonItem(
                destination_id=dest.id,
                destination_name=dest.name,
                state=dest.state,
                month=seasonal.month,
                month_name=seasonal.month_name,
                suitability_score=seasonal.suitability_score,
                climate_type=seasonal.climate_type,
                rainfall_level=seasonal.rainfall_level,
                crowd_demand=seasonal.crowd_demand,
                water_sports_available=seasonal.water_sports_available,
                advisory_notice=seasonal.advisory_notice,
                is_recommended=seasonal.suitability_score >= 0.75,
            )
            ranked_items.append(item)
            if selected_destination_id and dest.id == selected_destination_id:
                selected_item = item

        # Sort destinations by suitability score descending
        ranked_items.sort(key=lambda x: x.suitability_score, reverse=True)

        better_alternatives = False
        summary_bullets = []

        if selected_item:
            if selected_item.suitability_score < 0.60:
                better_alternatives = True
                top_dest = ranked_items[0] if ranked_items else None
                if top_dest and top_dest.destination_id != selected_item.destination_id:
                    summary_bullets.append(
                        f"{selected_item.destination_name} has sub-optimal conditions ({selected_item.climate_type}, {selected_item.rainfall_level} rainfall) with suitability score {selected_item.suitability_score:.2f}."
                    )
                    summary_bullets.append(
                        f"Consider '{top_dest.destination_name}' instead ({top_dest.climate_type}, suitability {top_dest.suitability_score:.2f})."
                    )
            else:
                summary_bullets.append(
                    f"{selected_item.destination_name} has favorable conditions in {month_name} ({selected_item.climate_type}, suitability {selected_item.suitability_score:.2f})."
                )
        else:
            top_dest = ranked_items[0] if ranked_items else None
            if top_dest:
                summary_bullets.append(
                    f"Top destination for {month_name} is '{top_dest.destination_name}' with suitability score {top_dest.suitability_score:.2f} ({top_dest.climate_type})."
                )

        if selected_item and selected_item.advisory_notice:
            summary_bullets.append(f"Advisory: {selected_item.advisory_notice}")

        summary = " ".join(summary_bullets)

        return SeasonalComparisonResponse(
            selected_destination_id=selected_destination_id,
            travel_month=travel_month,
            travel_month_name=month_name,
            destinations_ranked=ranked_items,
            better_alternatives_available=better_alternatives,
            recommendation_summary=summary,
        )
