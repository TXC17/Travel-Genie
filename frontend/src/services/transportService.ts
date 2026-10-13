import { apiClient } from './api';
import { IntercityRecommendationParams, IntercityRecommendationResponse } from '../types';

export const transportService = {
  async getIntercityRecommendations(
    params: IntercityRecommendationParams
  ): Promise<IntercityRecommendationResponse> {
    const res = await apiClient.get<IntercityRecommendationResponse>(
      '/transport/intercity-recommendations',
      {
        params: {
          origin: params.origin,
          destination: params.destination,
          party_size: params.party_size || 1,
          budget: params.budget,
          user_preferred_mode: params.user_preferred_mode,
        },
      }
    );
    return res.data;
  },
};
