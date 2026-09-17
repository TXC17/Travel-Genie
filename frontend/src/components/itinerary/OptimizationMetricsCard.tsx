import React from 'react';
import { MultiDayTripOptimizationResponse } from '../../types';
import { TrendingDown, Navigation, Clock, DollarSign, Award, ShieldCheck } from 'lucide-react';

interface OptimizationMetricsCardProps {
  itinerary: MultiDayTripOptimizationResponse;
}

export const OptimizationMetricsCard: React.FC<OptimizationMetricsCardProps> = ({
  itinerary,
}) => {
  return (
    <div className="bg-gradient-to-br from-slate-900 via-teal-950 to-slate-900 text-white rounded-2xl p-6 md:p-8 shadow-xl border border-teal-800/40 relative overflow-hidden">
      {/* Decorative Glow */}
      <div className="absolute top-0 right-0 -mt-8 -mr-8 w-48 h-48 bg-teal-500/10 rounded-full blur-3xl" />

      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 relative z-10">
        <div>
          <div className="flex items-center gap-2 text-teal-400 text-xs font-bold uppercase tracking-wider mb-1">
            <Award className="w-4 h-4" />
            <span>Google OR-Tools & Held-Karp Solver</span>
          </div>
          <h3 className="text-xl md:text-2xl font-bold">
            Optimization & Efficiency Benchmarks
          </h3>
        </div>

        <div className="flex items-center gap-2 bg-teal-500/20 border border-teal-400/30 px-4 py-2 rounded-xl text-teal-300 font-bold text-sm">
          <TrendingDown className="w-4 h-4" />
          <span>{itinerary.aggregate_distance_reduction_pct}% Route Distance Saved</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 relative z-10">
        <div className="bg-white/5 border border-white/10 p-4 rounded-xl backdrop-blur-sm">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <Navigation className="w-3.5 h-3.5 text-teal-400" />
            <span>Total Road Travel</span>
          </div>
          <p className="text-xl md:text-2xl font-bold text-white">
            {itinerary.total_travel_distance_km} <span className="text-sm font-normal text-slate-400">km</span>
          </p>
        </div>

        <div className="bg-white/5 border border-white/10 p-4 rounded-xl backdrop-blur-sm">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <Clock className="w-3.5 h-3.5 text-teal-400" />
            <span>Travel Time</span>
          </div>
          <p className="text-xl md:text-2xl font-bold text-white">
            {itinerary.total_travel_duration_hours} <span className="text-sm font-normal text-slate-400">hrs</span>
          </p>
        </div>

        <div className="bg-white/5 border border-white/10 p-4 rounded-xl backdrop-blur-sm">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <Clock className="w-3.5 h-3.5 text-emerald-400" />
            <span>Sightseeing Time</span>
          </div>
          <p className="text-xl md:text-2xl font-bold text-white">
            {itinerary.total_sightseeing_duration_hours} <span className="text-sm font-normal text-slate-400">hrs</span>
          </p>
        </div>

        <div className="bg-white/5 border border-white/10 p-4 rounded-xl backdrop-blur-sm">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <DollarSign className="w-3.5 h-3.5 text-amber-400" />
            <span>Est. Total Cost</span>
          </div>
          <p className="text-xl md:text-2xl font-bold text-amber-300">
            ₹{itinerary.total_estimated_cost.toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
};
