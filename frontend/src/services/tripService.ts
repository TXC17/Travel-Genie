import { apiClient } from './api';
import { GenerateItineraryResponse } from '../types';

export interface GenerateTripPayload {
  destination_id: string;
  duration_days: number;
  total_budget: number;
  party_size: number;
  interests: string[];
  pace: string;
  preferred_transport: string;
  travel_month: number;
  start_date: string;
}

export interface TripDetail {
  id: string;
  destination_id: string;
  title: string;
  start_date: string;
  end_date: string;
  number_of_days?: number;
  party_size: number;
  total_budget: number;
  created_at: string;
  itineraries?: any[];
  preferences?: any;
}

export const tripService = {
  async generateItinerary(payload: GenerateTripPayload): Promise<GenerateItineraryResponse> {
    const res = await apiClient.post<GenerateItineraryResponse>('/trips/generate-itinerary', payload);
    return res.data;
  },

  async getUserTrips(): Promise<TripDetail[]> {
    const res = await apiClient.get<TripDetail[]>('/trips');
    return res.data;
  },

  async getTrip(id: string): Promise<TripDetail> {
    const res = await apiClient.get<TripDetail>(`/trips/${id}`);
    return res.data;
  },

  async updateTrip(id: string, payload: { title?: string }): Promise<TripDetail> {
    const res = await apiClient.put<TripDetail>(`/trips/${id}/preferences`, payload);
    return res.data;
  },

  async deleteTrip(id: string): Promise<void> {
    await apiClient.delete(`/trips/${id}`);
  },
};
