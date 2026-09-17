/**
 * Central TypeScript Interfaces matching Backend Domain Models and DTOs.
 */

export type DestinationId = 'dandeli' | 'coorg' | 'hampi' | 'goa' | string;

export interface Destination {
  id: string;
  name: string;
  state: string;
  description: string;
  latitude: number;
  longitude: number;
  hero_image_url?: string;
  best_season: string;
  is_active: boolean;
}

export interface SeasonalData {
  month: number;
  month_name: string;
  suitability_score: number; // 0.0 - 1.0
  climate_type: string;
  avg_temp_min: number;
  avg_temp_max: number;
  rainfall_level: 'Low' | 'Moderate' | 'High' | 'Monsoon';
  crowd_demand: 'Low' | 'Moderate' | 'High';
  advisory_notice?: string;
}

export interface Attraction {
  id: string;
  destination_id: string;
  name: string;
  category: string;
  description: string;
  latitude: number;
  longitude: number;
  average_visit_duration: number; // in hours
  entry_fee: number; // in INR
  popularity_score: number; // 0.0 - 1.0
  rating: number; // 1.0 - 5.0
  opening_time?: string;
  closing_time?: string;
  best_time_to_visit?: string;
  tags?: string[];
  is_verified?: boolean;
}

export interface ScoreBreakdown {
  interest_score: number;
  season_score: number;
  popularity_score: number;
  rating_score: number;
  budget_score: number;
  composite_score: number;
  reason: string;
}

export interface ScoredAttraction {
  attraction: Attraction;
  composite_score: number;
  rank: number;
  breakdown: ScoreBreakdown;
}

export interface RouteLeg {
  from_attraction_id: string;
  from_attraction_name: string;
  to_attraction_id: string;
  to_attraction_name: string;
  distance_km: number;
  travel_time_hours: number;
  transport_mode: string;
  estimated_transit_cost: number;
  provenance_method?: string;
  provenance_classification?: string;
}

export interface ScheduledVisitItem {
  attraction: Attraction;
  visit_order: number;
  arrival_time: string;
  departure_time: string;
  visit_duration_hours: number;
  travel_time_from_prev_hours: number;
  distance_from_prev_km: number;
  item_admission_fee: number;
  waiting_time_hours: number;
  crowd_estimate_score: number;
  crowd_level: 'Low' | 'Moderate' | 'High';
  visit_notes?: string;
  provenance_classification?: string;
}

export interface DayOptimizationMetrics {
  original_route_distance_km: number;
  optimized_route_distance_km: number;
  distance_reduction_km: number;
  distance_reduction_pct: number;
  original_travel_time_hours: number;
  optimized_travel_time_hours: number;
  travel_time_reduction_hours: number;
  solver_status: string;
}

export interface DeferredAttraction {
  attraction_id: string;
  attraction_name: string;
  original_day_number: number;
  reason: string;
  violating_constraint: string;
  mcdm_score?: number;
}

export interface OptimizedDaySchedule {
  day_number: number;
  date?: string;
  cluster_id: number;
  attraction_count: number;
  feasibility_status: 'FEASIBLE' | 'FEASIBLE_AFTER_PRUNING' | 'INFEASIBLE_ALL_PRUNED';
  recommended_transport: string;
  day_start_time: string;
  day_end_time: string;
  total_sightseeing_duration_hours: number;
  total_travel_duration_hours: number;
  total_waiting_duration_hours: number;
  total_day_duration_hours: number;
  total_travel_distance_km: number;
  day_estimated_admission_cost: number;
  day_estimated_transit_cost: number;
  day_total_estimated_cost: number;
  route_sequence: number[];
  ordered_attractions: Attraction[];
  optimization_metrics: DayOptimizationMetrics;
  items: ScheduledVisitItem[];
  legs: RouteLeg[];
  constraint_violations: string[];
}

export interface MultiDayTripOptimizationResponse {
  destination_id: string;
  trip_id?: string;
  total_days: number;
  total_scheduled_attractions: number;
  total_deferred_attractions: number;
  total_travel_distance_km: number;
  total_travel_duration_hours: number;
  total_sightseeing_duration_hours: number;
  total_day_duration_hours: number;
  total_estimated_cost: number;
  aggregate_distance_reduction_pct: number;
  days: OptimizedDaySchedule[];
  deferred_attractions: DeferredAttraction[];
  provenance_metadata?: Record<string, any>;
}

export interface ConstraintChangeItem {
  field: string;
  old_value: any;
  new_value: any;
}

export interface RemovedAttractionItem {
  attraction_id: string;
  name: string;
  reason: string;
}

export interface AddedAttractionItem {
  attraction_id: string;
  name: string;
  day_number: number;
  reason: string;
}

export interface MovedAttractionItem {
  attraction_id: string;
  name: string;
  from_day: number;
  to_day: number;
}

export interface ReplanningDiff {
  is_replanned: boolean;
  changed_constraints: ConstraintChangeItem[];
  removed_attractions: RemovedAttractionItem[];
  added_attractions: AddedAttractionItem[];
  moved_attractions: MovedAttractionItem[];
  distance_change_km: number;
  travel_time_change_hours: number;
  budget_change: number;
  reasoning: string[];
}

export interface ExtractedTripConstraints {
  destination_id?: string;
  destination_name?: string;
  duration_days?: number;
  total_budget?: number;
  party_size?: number;
  interests?: string[];
  pace?: 'Relaxed' | 'Moderate' | 'Intense';
  preferred_transport?: 'walking' | 'auto' | 'car' | 'taxi' | 'rental' | 'public';
  start_date?: string;
  travel_month?: number;
  max_daily_travel_hours?: number;
  budget_tier?: string;
  is_complete: boolean;
  missing_fields: string[];
  clarification_question?: string;
  extraction_method?: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  sender: 'user' | 'assistant' | 'system';
  content: string;
  extracted_constraints?: Record<string, any>;
  created_at?: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  trip_id?: string;
  title: string;
  created_at?: string;
  messages: ChatMessage[];
}

export interface SendMessageResponse {
  session_id: string;
  message_id: string;
  sender: string;
  content: string;
  extracted_constraints: ExtractedTripConstraints;
  itinerary?: MultiDayTripOptimizationResponse;
  persisted_itinerary_id?: string;
  replanning_diff?: ReplanningDiff;
  is_clarification: boolean;
  clarification_question?: string;
}

export interface PipelineStageTelemetry {
  stage_name: string;
  status: string;
  duration_ms: number;
  details: Record<string, any>;
}

export interface PipelineDiagnostics {
  pipeline_id: string;
  status: string;
  total_duration_ms: number;
  candidate_attractions_count: number;
  recommended_attractions_count: number;
  clusters_count: number;
  total_scheduled_count: number;
  total_deferred_count: number;
  distance_reduction_pct: number;
  stages: PipelineStageTelemetry[];
}

export interface GenerateItineraryResponse {
  trip_id: string;
  itinerary_id: string;
  version: number;
  title: string;
  destination_id: string;
  constraints: ExtractedTripConstraints;
  itinerary: MultiDayTripOptimizationResponse;
  diagnostics: PipelineDiagnostics;
  explanation: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
