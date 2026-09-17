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
    <div className="liquid-glass text-slate-900 dark:text-white rounded-3xl p-6 md:p-8 shadow-md bg-gradient-to-br from-emerald-100/95 via-slate-100 to-teal-100/90 dark:from-neutral-950 dark:via-black dark:to-neutral-950 border-2 border-emerald-300 dark:border-neutral-800 relative overflow-hidden">
      {/* Decorative Glow */}
      <div className="absolute top-0 right-0 -mt-8 -mr-8 w-48 h-48 bg-emerald-500/20 dark:bg-emerald-500/10 rounded-full blur-3xl" />

      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 relative z-10">
        <div>
          <div className="flex items-center gap-2 text-emerald-950 dark:text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1">
            <Award className="w-4 h-4 text-emerald-700 dark:text-emerald-400" />
            <span>Google OR-Tools & Held-Karp Solver</span>
          </div>
          <h3 className="text-xl md:text-2xl font-extrabold text-slate-950 dark:text-white">
            Optimization & Efficiency Benchmarks
          </h3>
        </div>

        <div className="liquid-btn flex items-center gap-2 bg-emerald-700/15 dark:bg-emerald-500/15 border-2 border-emerald-500/40 dark:border-emerald-400/40 px-4 py-2 rounded-xl text-emerald-950 dark:text-emerald-300 font-extrabold text-sm shadow-xs">
          <TrendingDown className="w-4 h-4 text-emerald-700 dark:text-emerald-400" />
          <span>{itinerary.aggregate_distance_reduction_pct}% Route Distance Saved</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 relative z-10">
        <div className="liquid-btn bg-white/95 dark:bg-neutral-900/80 border-2 border-slate-300 dark:border-neutral-800 p-4 rounded-xl shadow-xs">
          <div className="flex items-center gap-1.5 text-slate-600 dark:text-neutral-400 text-xs mb-1 font-semibold">
            <Navigation className="w-3.5 h-3.5 text-emerald-700 dark:text-emerald-400" />
            <span>Total Road Travel</span>
          </div>
          <p className="text-xl md:text-2xl font-black text-slate-950 dark:text-white">
            {itinerary.total_travel_distance_km} <span className="text-sm font-semibold text-slate-600 dark:text-neutral-400">km</span>
          </p>
        </div>

        <div className="liquid-btn bg-white/95 dark:bg-neutral-900/80 border-2 border-slate-300 dark:border-neutral-800 p-4 rounded-xl shadow-xs">
          <div className="flex items-center gap-1.5 text-slate-600 dark:text-neutral-400 text-xs mb-1 font-semibold">
            <Clock className="w-3.5 h-3.5 text-emerald-700 dark:text-emerald-400" />
            <span>Travel Time</span>
          </div>
          <p className="text-xl md:text-2xl font-black text-slate-950 dark:text-white">
            {itinerary.total_travel_duration_hours} <span className="text-sm font-semibold text-slate-600 dark:text-neutral-400">hrs</span>
          </p>
        </div>

        <div className="liquid-btn bg-white/95 dark:bg-neutral-900/80 border-2 border-slate-300 dark:border-neutral-800 p-4 rounded-xl shadow-xs">
          <div className="flex items-center gap-1.5 text-slate-600 dark:text-neutral-400 text-xs mb-1 font-semibold">
            <Clock className="w-3.5 h-3.5 text-emerald-700 dark:text-emerald-400" />
            <span>Sightseeing Time</span>
          </div>
          <p className="text-xl md:text-2xl font-black text-slate-950 dark:text-white">
            {itinerary.total_sightseeing_duration_hours} <span className="text-sm font-semibold text-slate-600 dark:text-neutral-400">hrs</span>
          </p>
        </div>

        <div className="liquid-btn bg-white/95 dark:bg-neutral-900/80 border-2 border-slate-300 dark:border-neutral-800 p-4 rounded-xl shadow-xs">
          <div className="flex items-center gap-1.5 text-slate-600 dark:text-neutral-400 text-xs mb-1 font-semibold">
            <DollarSign className="w-3.5 h-3.5 text-amber-700 dark:text-amber-400" />
            <span>Est. Total Cost</span>
          </div>
          <p className="text-xl md:text-2xl font-black text-amber-800 dark:text-amber-300">
            ₹{itinerary.total_estimated_cost.toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
};
