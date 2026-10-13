import { apiClient } from './api';
import {
  Accommodation,
  AccommodationRecommendationRequest,
  AccommodationRecommendationResponse,
} from '../types';

export interface AccommodationFilterParams {
  destination_id: string;
  budget_tier?: string;
  min_rating?: number;
  max_price_per_night?: number;
  accommodation_type?: string;
}

export const accommodationService = {
  /**
   * Fetch list of curated accommodations for a destination with optional filters.
   */
  async getAccommodations(params: AccommodationFilterParams): Promise<Accommodation[]> {
    const res = await apiClient.get<Accommodation[]>('/accommodations', {
      params,
    });
    return res.data;
  },

  /**
   * Fetch single accommodation by ID with full details.
   */
  async getAccommodation(id: string): Promise<Accommodation> {
    const res = await apiClient.get<Accommodation>(`/accommodations/${id}`);
    return res.data;
  },

  /**
   * Calculate deterministic budget-aware accommodation recommendations.
   */
  async getRecommendations(
    request: AccommodationRecommendationRequest
  ): Promise<AccommodationRecommendationResponse> {
    const res = await apiClient.post<AccommodationRecommendationResponse>(
      '/accommodations/recommendations',
      request
    );
    return res.data;
  },
};
