import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { destinationService, SeasonalComparisonResponse } from '../services/destinationService';
import { Destination } from '../types';
import {
  Compass,
  MapPin,
  Sparkles,
  Route,
  Clock,
  ShieldCheck,
  ArrowRight,
  TrendingDown,
  Calendar,
  Layers,
} from 'lucide-react';

const DESTINATION_META: Record<string, { emoji: string; badgeColor: string }> = {
  hampi: { emoji: '🏛️', badgeColor: 'bg-amber-100 text-amber-800' },
  coorg: { emoji: '☕', badgeColor: 'bg-emerald-100 text-emerald-800' },
  dandeli: { emoji: '🌲', badgeColor: 'bg-emerald-100 text-emerald-800' },
  goa: { emoji: '🏖️', badgeColor: 'bg-amber-100 text-amber-800' },
};

const ALL_MONTHS = [
  { m: 1, short: 'Jan', name: 'January', emoji: '❄️', season: 'Peak' },
  { m: 2, short: 'Feb', name: 'February', emoji: '🌤️', season: 'Mild' },
  { m: 3, short: 'Mar', name: 'March', emoji: '☀️', season: 'Warm' },
  { m: 4, short: 'Apr', name: 'April', emoji: '☀️', season: 'Hot' },
  { m: 5, short: 'May', name: 'May', emoji: '☀️', season: 'Hot' },
  { m: 6, short: 'Jun', name: 'June', emoji: '🌧️', season: 'Monsoon' },
  { m: 7, short: 'Jul', name: 'July', emoji: '🌧️', season: 'Monsoon' },
  { m: 8, short: 'Aug', name: 'August', emoji: '🌧️', season: 'Monsoon' },
  { m: 9, short: 'Sep', name: 'September', emoji: '🌤️', season: 'Post-Rain' },
  { m: 10, short: 'Oct', name: 'October', emoji: '🍂', season: 'Pleasant' },
  { m: 11, short: 'Nov', name: 'November', emoji: '🌤️', season: 'Prime' },
  { m: 12, short: 'Dec', name: 'December', emoji: '❄️', season: 'Peak' },
];

const MONTH_NAMES_SHORT = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [selectedMonth, setSelectedMonth] = useState<number>(11); // November default
  const [seasonalData, setSeasonalData] = useState<SeasonalComparisonResponse | null>(null);

  useEffect(() => {
    loadData();
  }, [selectedMonth]);

  const loadData = async () => {
    try {
      const [dests, seasonal] = await Promise.all([
        destinationService.getDestinations(),
        destinationService.getSeasonalComparison(selectedMonth),
      ]);
      setDestinations(dests);
      setSeasonalData(seasonal);
    } catch (err) {
      console.error('Failed to load landing page data', err);
    }
  };

  return (
    <div className="space-y-16 py-8">
      {/* Hero Section */}
      <section className="liquid-glass relative rounded-3xl p-8 md:p-16 overflow-hidden shadow-md bg-gradient-to-br from-emerald-200/95 via-teal-100/90 to-amber-100/85 dark:from-neutral-950 dark:via-neutral-950 dark:to-neutral-950 border-2 border-emerald-400/90 dark:border-neutral-800">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-emerald-400/30 dark:bg-emerald-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="max-w-3xl relative z-10 space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-700/15 dark:bg-emerald-950/60 border border-emerald-500/40 dark:border-emerald-500/40 text-emerald-950 dark:text-emerald-300 text-xs font-bold uppercase tracking-wider">
            <Sparkles className="w-4 h-4 text-emerald-800 dark:text-emerald-400" />
            <span>AI-Driven Optimization Engine</span>
          </div>

          <h1 className="text-3xl md:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight text-slate-950 dark:text-white">
            Next-Gen Itinerary Planning with{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-800 via-teal-800 to-amber-700 dark:from-emerald-400 dark:via-amber-300 dark:to-emerald-400">
              OR-Tools & MCDM
            </span>
          </h1>

          <p className="text-slate-800 dark:text-neutral-300 text-sm md:text-base leading-relaxed font-medium">
            Travel Genie combines deterministic <strong className="text-slate-950 dark:text-white font-extrabold">Multi-Criteria Decision Making</strong>,{' '}
            <strong className="text-slate-950 dark:text-white font-extrabold">Spatial K-Means Clustering</strong>, and{' '}
            <strong className="text-slate-950 dark:text-white font-extrabold">Google OR-Tools Route Optimization</strong> with natural-language AI to build
            mathematically optimal, time-feasible travel itineraries.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-4">
            <Link
              to="/plan"
              className="liquid-btn px-6 py-3.5 bg-emerald-700 hover:bg-emerald-800 dark:bg-emerald-400 dark:hover:bg-emerald-300 text-white dark:text-black font-extrabold rounded-xl shadow-lg shadow-emerald-900/25 dark:shadow-emerald-500/30 transition-all flex items-center gap-2 text-sm cursor-pointer"
            >
              <Compass className="w-5 h-5 text-white dark:text-black" />
              <span>Start Planning Itinerary</span>
            </Link>

            <Link
              to="/chat"
              className="liquid-btn px-6 py-3.5 bg-white hover:bg-slate-50 dark:bg-neutral-900 dark:hover:bg-neutral-850 text-slate-900 dark:text-white font-bold rounded-xl border-2 border-emerald-400/80 dark:border-neutral-800 shadow-sm transition-all flex items-center gap-2 text-sm cursor-pointer"
            >
              <Sparkles className="w-5 h-5 text-emerald-700 dark:text-emerald-400" />
              <span>Try AI Chat Planner</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Seasonal Climate & Destination Suitability Section */}
      <section className="liquid-glass rounded-3xl p-6 sm:p-10 border border-slate-300/80 dark:border-neutral-800 shadow-sm space-y-8 bg-gradient-to-b from-white/95 to-slate-100/70 dark:from-transparent dark:to-transparent">
        {/* Header with Badges & Highlight Text */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-slate-100 dark:border-neutral-800">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 rounded-full text-xs font-black uppercase tracking-wider border border-emerald-200/80 dark:border-emerald-800">
              <Calendar className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Climate & Season Intelligence</span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Seasonal Climate & Destination Suitability
            </h2>

            <div className="p-3.5 bg-gradient-to-r from-emerald-50/90 via-emerald-50/60 to-amber-50/80 dark:from-emerald-950/40 dark:via-neutral-950 dark:to-amber-950/40 border border-emerald-200/70 dark:border-emerald-800/60 rounded-2xl flex items-start gap-3 text-xs sm:text-sm text-slate-700 dark:text-neutral-300 shadow-xs">
              <Sparkles className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-slate-800 dark:text-neutral-200 leading-relaxed">
                  <strong>Plan Around Optimal Weather:</strong> Select your intended travel month on the calendar below to instantly compare seasonal climates, rainfall risks, tourist crowd levels, and identify the highest-rated destination for that period.
                </p>
              </div>
            </div>
          </div>

          {/* Month Quick Badge / Active Summary */}
          {seasonalData && (
            <div className="liquid-card shrink-0 bg-white dark:bg-neutral-900 text-slate-900 dark:text-white px-4 py-3 rounded-2xl shadow-md border border-slate-200 dark:border-neutral-850 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 flex items-center justify-center font-black text-sm border border-emerald-200/60 dark:border-emerald-500/30">
                {MONTH_NAMES_SHORT[selectedMonth]}
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 dark:text-neutral-400 uppercase tracking-wider block">
                  Active Month View
                </span>
                <span className="text-sm font-extrabold text-slate-900 dark:text-white">
                  {seasonalData.travel_month_name} 2026
                </span>
              </div>
            </div>
          )}
        </div>

        {/* 12-Month Interactive Calendar Bar */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-slate-700 dark:text-neutral-300 uppercase tracking-wider flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <span>Interactive 12-Month Calendar Selector:</span>
            </span>
            <span className="text-[11px] font-bold text-emerald-700 dark:text-emerald-400">
              Click any month to recalculate suitability scores
            </span>
          </div>

          <div className="grid grid-cols-3 sm:grid-cols-6 lg:grid-cols-12 gap-2 p-2.5 bg-slate-200/70 dark:bg-neutral-950 border border-slate-300/80 dark:border-neutral-800 rounded-2xl">
            {ALL_MONTHS.map((item) => {
              const isSelected = selectedMonth === item.m;
              return (
                <button
                  key={`cal-month-${item.m}`}
                  type="button"
                  onClick={() => setSelectedMonth(item.m)}
                  className={`liquid-btn py-2.5 px-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex flex-col items-center justify-center gap-0.5 ${
                    isSelected
                      ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black font-extrabold shadow-md shadow-emerald-600/25 dark:shadow-emerald-500/30 ring-2 ring-emerald-500/30 dark:ring-emerald-400/50 scale-105'
                      : 'bg-white dark:bg-neutral-900 hover:bg-emerald-50 dark:hover:bg-neutral-850 text-slate-700 dark:text-neutral-200 hover:text-emerald-900 dark:hover:text-emerald-300 border border-slate-300/70 dark:border-neutral-800 hover:border-emerald-400 dark:hover:border-emerald-500/60 shadow-xs'
                  }`}
                >
                  <span className="text-base">{item.emoji}</span>
                  <span className="font-extrabold">{item.short}</span>
                  <span className={`text-[9px] font-medium ${isSelected ? 'text-emerald-100 dark:text-emerald-950' : 'text-slate-500 dark:text-neutral-400'}`}>
                    {item.season}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Dynamic Seasonal Recommendation Highlight Banner */}
        {seasonalData?.destinations_ranked?.[0] && (
          <div className="liquid-card p-4 bg-gradient-to-r from-emerald-100/90 via-emerald-50/80 to-amber-100/70 dark:bg-emerald-950/30 border border-emerald-300/80 dark:border-emerald-800/60 rounded-2xl flex flex-wrap items-center justify-between gap-3 text-xs sm:text-sm">
            <div className="flex items-center gap-2.5">
              <span className="text-xl">🏆</span>
              <div>
                <span className="font-bold text-slate-900 dark:text-white">
                  Top Recommended Destination for {seasonalData.travel_month_name}:
                </span>{' '}
                <span className="font-extrabold text-emerald-800 dark:text-emerald-300">
                  {seasonalData.destinations_ranked[0].destination_name} ({Math.round(seasonalData.destinations_ranked[0].suitability_score * 100)}% Suitability)
                </span>
                <span className="text-xs text-slate-600 dark:text-neutral-400 block sm:inline sm:ml-2">
                  • Climate: {seasonalData.destinations_ranked[0].climate_type} • Rainfall: {seasonalData.destinations_ranked[0].rainfall_level}
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => navigate(`/plan?destination=${seasonalData.destinations_ranked[0].destination_id}&month=${selectedMonth}`)}
              className="liquid-btn px-4 py-2 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-black font-extrabold rounded-xl text-xs flex items-center gap-1.5 shadow-sm transition-all cursor-pointer hover:scale-105 shrink-0"
            >
              <span>Plan Trip to {seasonalData.destinations_ranked[0].destination_name}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Destination Comparison Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {destinations.map((dest) => {
            const comp = seasonalData?.destinations_ranked?.find((c) => c.destination_id === dest.id);
            const isTop = seasonalData?.destinations_ranked?.[0]?.destination_id === dest.id;
            const destMeta = DESTINATION_META[dest.id.toLowerCase()] || { emoji: '📍', badgeColor: 'bg-emerald-100 text-emerald-800' };

            const suitabilityPct = comp ? Math.round(comp.suitability_score * 100) : 80;

            return (
              <div
                key={dest.id}
                onClick={() => navigate(`/plan?destination=${dest.id}`)}
                className={`liquid-card rounded-3xl p-5 border-2 transition-all cursor-pointer flex flex-col justify-between group ${
                  isTop
                    ? 'border-emerald-500 dark:border-emerald-500 bg-emerald-50/40 dark:bg-neutral-900 shadow-md ring-2 ring-emerald-500/20 dark:ring-emerald-500/20'
                    : 'border-slate-300/80 dark:border-neutral-800 bg-white/95 dark:bg-neutral-900 hover:border-emerald-400 dark:hover:border-emerald-500/60'
                }`}
              >
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-extrabold px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-neutral-900 text-slate-700 dark:text-neutral-300 uppercase flex items-center gap-1 border border-slate-200/80 dark:border-neutral-800">
                      <span>{destMeta.emoji}</span>
                      <span>{dest.state}</span>
                    </span>

                    {isTop && (
                      <span className="text-[10px] font-black px-2.5 py-0.5 rounded-full bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black uppercase tracking-wider shadow-xs">
                        ⭐ Top Pick
                      </span>
                    )}
                  </div>

                  <h3 className="text-lg font-extrabold text-slate-900 dark:text-white group-hover:text-emerald-700 dark:group-hover:text-emerald-400 transition-colors">
                    {dest.name}
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-neutral-400 line-clamp-2 leading-relaxed">
                    {dest.description}
                  </p>
                </div>

                {comp && (
                  <div className="space-y-3 pt-3 border-t border-slate-200 dark:border-neutral-800 text-xs mt-3">
                    {/* Suitability Score Bar */}
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] font-bold text-slate-600 dark:text-neutral-400">Suitability Index:</span>
                        <span className={`text-xs font-black ${
                          suitabilityPct >= 80 ? 'text-emerald-700 dark:text-emerald-400' : suitabilityPct >= 60 ? 'text-amber-700 dark:text-amber-400' : 'text-slate-600 dark:text-neutral-400'
                        }`}>
                          {suitabilityPct}%
                        </span>
                      </div>
                      <div className="w-full h-2 bg-slate-200 dark:bg-neutral-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            suitabilityPct >= 80 ? 'bg-emerald-500' : suitabilityPct >= 60 ? 'bg-amber-500' : 'bg-slate-400'
                          }`}
                          style={{ width: `${suitabilityPct}%` }}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-1.5 text-[11px] font-semibold">
                      <div className="bg-emerald-50/60 dark:bg-neutral-900 p-2 rounded-xl border border-emerald-200/70 dark:border-neutral-800">
                        <span className="text-slate-500 dark:text-neutral-500 block text-[9px] uppercase font-bold">Climate</span>
                        <span className="text-slate-900 dark:text-neutral-200 font-bold capitalize">{comp.climate_type}</span>
                      </div>
                      <div className="bg-amber-50/60 dark:bg-neutral-900 p-2 rounded-xl border border-amber-200/70 dark:border-neutral-800">
                        <span className="text-slate-500 dark:text-neutral-500 block text-[9px] uppercase font-bold">Crowd</span>
                        <span className="text-slate-900 dark:text-neutral-200 font-bold capitalize">{comp.crowd_demand}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1 text-emerald-700 dark:text-emerald-400 font-extrabold text-xs group-hover:translate-x-0.5 transition-transform">
                      <span>Explore {dest.name}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* Algorithmic Pipeline Architecture Overview */}
      <section className="liquid-glass rounded-3xl p-8 md:p-12 space-y-8 border border-slate-300/80 dark:border-neutral-800 bg-gradient-to-b from-white/95 via-emerald-50/30 to-teal-50/30 dark:from-transparent dark:to-transparent">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <div className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">
            <Layers className="w-4 h-4" />
            <span>Academic System Architecture</span>
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-white">
            Deterministic Optimization Pipeline
          </h2>
          <p className="text-slate-600 dark:text-neutral-400 text-xs md:text-sm">
            Strict separation of concerns ensures all routes, prices, and timings are mathematically verified.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="liquid-card p-6 rounded-2xl border border-emerald-200/90 dark:border-neutral-800 bg-emerald-50/70 dark:bg-neutral-900 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white dark:bg-emerald-950/70 dark:text-emerald-300 font-bold flex items-center justify-center text-sm shadow-xs">
              01
            </div>
            <h3 className="font-bold text-slate-900 dark:text-white text-base">Phase 4: MCDM Scoring</h3>
            <p className="text-xs text-slate-600 dark:text-neutral-400 leading-relaxed">
              Multi-Attribute Utility Theory combining interest cosine similarity, 12-month climate, popularity, rating, and budget.
            </p>
          </div>

          <div className="liquid-card p-6 rounded-2xl border border-amber-200/90 dark:border-neutral-800 bg-amber-50/70 dark:bg-neutral-900 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-amber-600 text-white dark:bg-purple-950/70 dark:text-purple-300 font-bold flex items-center justify-center text-sm shadow-xs">
              02
            </div>
            <h3 className="font-bold text-slate-900 dark:text-white text-base">Phase 5: Spatial Clustering</h3>
            <p className="text-xs text-slate-600 dark:text-neutral-400 leading-relaxed">
              Adaptive K-Means with Equirectangular projection partitioning attractions into coherent geographic sightseeing zones.
            </p>
          </div>

          <div className="liquid-card p-6 rounded-2xl border border-teal-200/90 dark:border-neutral-800 bg-teal-50/70 dark:bg-neutral-900 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-teal-600 text-white dark:bg-amber-950/70 dark:text-amber-300 font-bold flex items-center justify-center text-sm shadow-xs">
              03
            </div>
            <h3 className="font-bold text-slate-900 dark:text-white text-base">Phase 6: OR-Tools Routing</h3>
            <p className="text-xs text-slate-600 dark:text-neutral-400 leading-relaxed">
              Open TSP solver with Held-Karp fallback, road detour factors, daily pace limits, and MCDM-priority pruning.
            </p>
          </div>

          <div className="liquid-card p-6 rounded-2xl border border-purple-200/90 dark:border-slate-800 bg-purple-50/70 dark:bg-neutral-900 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-purple-600 text-white dark:bg-rose-950/70 dark:text-rose-300 font-bold flex items-center justify-center text-sm shadow-xs">
              04
            </div>
            <h3 className="font-bold text-slate-900 dark:text-white text-base">Phase 7: AI & Replanning</h3>
            <p className="text-xs text-slate-600 dark:text-neutral-400 leading-relaxed">
              Gemini NLU & NLG explanation layer with contextual constraint merging and structured replanning audit diffs.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
