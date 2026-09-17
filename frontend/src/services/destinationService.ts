import { apiClient } from './api';
import { Destination, Attraction, SeasonalData } from '../types';

export interface SeasonalComparisonItem {
  destination_id: string;
  destination_name: string;
  state: string;
  month: number;
  month_name: string;
  suitability_score: number;
  climate_type: string;
  rainfall_level: string;
  crowd_demand: string;
  water_sports_available: boolean;
  advisory_notice?: string;
  is_recommended: boolean;
}

export interface SeasonalComparisonResponse {
  selected_destination_id?: string;
  travel_month: number;
  travel_month_name: string;
  destinations_ranked: SeasonalComparisonItem[];
  better_alternatives_available: boolean;
  recommendation_summary: string;
}

export const destinationService = {
  async getDestinations(): Promise<Destination[]> {
    const res = await apiClient.get<Destination[]>('/destinations');
    return res.data;
  },

  async getDestination(id: string): Promise<Destination & { seasonal_data: SeasonalData[] }> {
    const res = await apiClient.get<Destination & { seasonal_data: SeasonalData[] }>(`/destinations/${id}`);
    return res.data;
  },

  async getAttractions(destinationId?: string, category?: string): Promise<Attraction[]> {
    const params: Record<string, string> = {};
    if (destinationId) params.destination_id = destinationId;
    if (category) params.category = category;
    const res = await apiClient.get<Attraction[]>('/attractions', { params });
    return res.data;
  },

  async getSeasonalComparison(month: number): Promise<SeasonalComparisonResponse> {
    const res = await apiClient.get<SeasonalComparisonResponse>('/recommendations/seasonal-compare', {
      params: { travel_month: month },
    });
    return res.data;
  },
};
