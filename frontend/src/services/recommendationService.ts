import { apiClient } from './api';
import { ScoredAttraction } from '../types';

export interface RecommendationPayload {
  destination_id: string;
  travel_month: number;
  interests: string[];
  total_budget: number;
  number_of_days: number;
  party_size: number;
}

export const recommendationService = {
  async getRecommendations(payload: RecommendationPayload): Promise<ScoredAttraction[]> {
    const res = await apiClient.post<ScoredAttraction[]>('/recommendations/attractions', payload);
    return res.data;
  },

  async getMcdmWeights(): Promise<Record<string, number>> {
    const res = await apiClient.get<Record<string, number>>('/recommendations/mcdm-weights');
    return res.data;
  },
};
