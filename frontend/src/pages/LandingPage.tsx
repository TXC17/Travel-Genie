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
      <section className="relative rounded-3xl bg-gradient-to-br from-slate-900 via-teal-950 to-slate-900 text-white p-8 md:p-16 overflow-hidden shadow-2xl border border-teal-800/30">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-teal-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="max-w-3xl relative z-10 space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-500/20 border border-teal-400/30 text-teal-300 text-xs font-bold uppercase tracking-wider">
            <Sparkles className="w-4 h-4 text-teal-400" />
            <span>AI-Driven Optimization Engine</span>
          </div>

          <h1 className="text-3xl md:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
            Next-Gen Itinerary Planning with{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 via-emerald-300 to-cyan-400">
              OR-Tools & MCDM
            </span>
          </h1>

          <p className="text-slate-300 text-sm md:text-base leading-relaxed">
            Travel Genie combines deterministic <strong>Multi-Criteria Decision Making</strong>,{' '}
            <strong>Spatial K-Means Clustering</strong>, and{' '}
            <strong>Google OR-Tools Route Optimization</strong> with natural-language AI to build
            mathematically optimal, time-feasible travel itineraries.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-4">
            <Link
              to="/plan"
              className="px-6 py-3.5 bg-teal-500 hover:bg-teal-400 text-slate-900 font-bold rounded-xl shadow-lg shadow-teal-500/30 transition-all flex items-center gap-2 text-sm cursor-pointer"
            >
              <Compass className="w-5 h-5" />
              <span>Start Planning Itinerary</span>
            </Link>

            <Link
              to="/chat"
              className="px-6 py-3.5 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-xl border border-white/20 backdrop-blur-sm transition-all flex items-center gap-2 text-sm cursor-pointer"
            >
              <Sparkles className="w-5 h-5 text-teal-300" />
              <span>Try AI Chat Planner</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Seasonal Explorer Section */}
      <section className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-teal-600 text-xs font-bold uppercase tracking-wider mb-1">
              <Calendar className="w-4 h-4" />
              <span>Phase 4 Climate Intelligence</span>
            </div>
            <h2 className="text-2xl md:text-3xl font-bold text-slate-900">
              Seasonal Climate & Destination Suitability
            </h2>
          </div>

          {/* Month Selector */}
          <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-xl">
            {[1, 4, 7, 10, 11, 12].map((m) => {
              const monthNames = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
              return (
                <button
                  key={`month-btn-${m}`}
                  onClick={() => setSelectedMonth(m)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                    selectedMonth === m
                      ? 'bg-teal-600 text-white shadow'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {monthNames[m]}
                </button>
              );
            })}
          </div>
        </div>

        {/* Destination Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {destinations.map((dest) => {
            const comp = seasonalData?.destinations_ranked?.find((c) => c.destination_id === dest.id);
            const isTop = seasonalData?.destinations_ranked?.[0]?.destination_id === dest.id;

            return (
              <div
                key={dest.id}
                onClick={() => navigate(`/plan?destination=${dest.id}`)}
                className={`bg-white rounded-2xl p-5 border transition-all hover:shadow-xl hover:-translate-y-1 cursor-pointer flex flex-col justify-between ${
                  isTop ? 'border-teal-500 ring-2 ring-teal-500/20' : 'border-slate-200'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 uppercase">
                      {dest.state}
                    </span>
                    {isTop && (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-teal-100 text-teal-800 uppercase tracking-wider">
                        Top Pick for {seasonalData?.travel_month_name}
                      </span>
                    )}
                  </div>

                  <h3 className="text-lg font-bold text-slate-900 mb-1">{dest.name}</h3>
                  <p className="text-xs text-slate-500 line-clamp-2 mb-4">{dest.description}</p>
                </div>

                {comp && (
                  <div className="space-y-2 pt-3 border-t border-slate-100 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Suitability:</span>
                      <span className="font-bold text-teal-700">
                        {Math.round(comp.suitability_score * 100)}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Climate:</span>
                      <span className="font-semibold text-slate-700 capitalize">
                        {comp.climate_type}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Crowd:</span>
                      <span className="font-semibold text-slate-700">{comp.crowd_demand}</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* Algorithmic Pipeline Architecture Overview */}
      <section className="bg-slate-50 border border-slate-200 rounded-3xl p-8 md:p-12 space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <div className="inline-flex items-center gap-1.5 text-xs font-bold text-teal-700 uppercase tracking-wider">
            <Layers className="w-4 h-4" />
            <span>Academic System Architecture</span>
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-slate-900">
            Deterministic Optimization Pipeline
          </h2>
          <p className="text-slate-500 text-xs md:text-sm">
            Strict separation of concerns ensures all routes, prices, and timings are mathematically verified.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 font-bold flex items-center justify-center text-sm">
              01
            </div>
            <h3 className="font-bold text-slate-900 text-base">Phase 4: MCDM Scoring</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Multi-Attribute Utility Theory combining interest cosine similarity, 12-month climate, popularity, rating, and budget.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-700 font-bold flex items-center justify-center text-sm">
              02
            </div>
            <h3 className="font-bold text-slate-900 text-base">Phase 5: Spatial Clustering</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Adaptive K-Means with Equirectangular projection partitioning attractions into coherent geographic sightseeing zones.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-700 font-bold flex items-center justify-center text-sm">
              03
            </div>
            <h3 className="font-bold text-slate-900 text-base">Phase 6: OR-Tools Routing</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Open TSP solver with Held-Karp fallback, road detour factors, daily pace limits, and MCDM-priority pruning.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-700 font-bold flex items-center justify-center text-sm">
              04
            </div>
            <h3 className="font-bold text-slate-900 text-base">Phase 7: AI & Replanning</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Gemini NLU & NLG explanation layer with contextual constraint merging and structured replanning audit diffs.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
