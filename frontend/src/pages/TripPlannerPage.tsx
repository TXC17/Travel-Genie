import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { destinationService } from '../services/destinationService';
import { recommendationService } from '../services/recommendationService';
import { tripService } from '../services/tripService';
import { Destination, ScoredAttraction } from '../types';
import {
  Compass,
  Calendar,
  Users,
  DollarSign,
  Gauge,
  Car,
  Sparkles,
  Loader2,
  ChevronRight,
  ChevronLeft,
  CheckCircle2,
  AlertCircle,
  MapPin,
  Clock,
  Tag,
  Star,
} from 'lucide-react';

const DESTINATION_META: Record<string, { emoji: string; highlight: string; badgeColor: string }> = {
  hampi: { emoji: '🏛️', highlight: 'UNESCO Heritage & Ancient Ruins', badgeColor: 'bg-amber-100 text-amber-800' },
  coorg: { emoji: '☕', highlight: 'Lush Coffee Hills & Waterfalls', badgeColor: 'bg-emerald-100 text-emerald-800' },
  dandeli: { emoji: '🌲', highlight: 'River Rafting & Wildlife Safari', badgeColor: 'bg-emerald-100 text-emerald-800' },
  goa: { emoji: '🏖️', highlight: 'Golden Beaches & Portuguese Heritage', badgeColor: 'bg-amber-100 text-amber-800' },
};

const INTEREST_META: Record<string, { label: string; emoji: string }> = {
  heritage: { label: 'Heritage & History', emoji: '🏛️' },
  nature: { label: 'Nature & Scenery', emoji: '🌿' },
  adventure: { label: 'Adventure & Trekking', emoji: '🧗' },
  religious: { label: 'Temples & Spiritual', emoji: '🛕' },
  beach: { label: 'Beaches & Coastal', emoji: '🏖️' },
};

const TRANSPORT_META = [
  { id: 'auto', label: 'Auto Rickshaw', emoji: '🛺', cost: '₹15/km (Base ₹30)', desc: 'Best for local intra-city transit' },
  { id: 'car', label: 'Taxi / Cab', emoji: '🚕', cost: '₹22/km (Base ₹100)', desc: 'Comfortable air-conditioned ride' },
  { id: 'rental', label: 'Self-Drive Rental', emoji: '🚗', cost: '₹12/km (Base ₹400)', desc: 'Flexible self-paced driving' },
  { id: 'walking', label: 'Walking / Foot', emoji: '🚶‍♂️', cost: '₹0/km', desc: 'Short-range eco exploration' },
  { id: 'public', label: 'Public Transit', emoji: '🚌', cost: '₹4/km', desc: 'Budget-friendly bus network' },
];

const MONTHS = [
  { m: 1, name: 'January ❄️' },
  { m: 2, name: 'February 🌤️' },
  { m: 3, name: 'March ☀️' },
  { m: 4, name: 'April ☀️' },
  { m: 5, name: 'May ☀️' },
  { m: 6, name: 'June 🌧️' },
  { m: 7, name: 'July 🌧️' },
  { m: 8, name: 'August 🌧️' },
  { m: 9, name: 'September 🌤️' },
  { m: 10, name: 'October 🍂' },
  { m: 11, name: 'November 🌤️' },
  { m: 12, name: 'December ❄️' },
];

export const TripPlannerPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isAuthenticated } = useAuth();

  const [step, setStep] = useState<number>(1);
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [selectedDestination, setSelectedDestination] = useState<string>(
    searchParams.get('destination') || 'hampi'
  );
  const [durationDays, setDurationDays] = useState<number>(3);
  const [partySize, setPartySize] = useState<number>(2);
  const [budget, setBudget] = useState<number>(15000);
  const [travelMonth, setTravelMonth] = useState<number>(11);
  const [startDate, setStartDate] = useState<string>('2026-11-01');
  const [selectedInterests, setSelectedInterests] = useState<string[]>(['heritage']);
  const [pace, setPace] = useState<string>('Moderate');
  const [transport, setTransport] = useState<string>('auto');

  // Preview Recommendations State
  const [recommendations, setRecommendations] = useState<ScoredAttraction[]>([]);

  useEffect(() => {
    loadDestinations();
  }, []);

  const loadDestinations = async () => {
    try {
      setLoading(true);
      const dests = await destinationService.getDestinations();
      setDestinations(dests);
    } catch (err) {
      console.error('Failed to load destinations', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInterestToggle = (tag: string) => {
    setSelectedInterests((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const handleFetchRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await recommendationService.getRecommendations({
        destination_id: selectedDestination,
        travel_month: travelMonth,
        interests: selectedInterests.length > 0 ? selectedInterests : ['heritage'],
        total_budget: budget,
        number_of_days: durationDays,
        party_size: partySize,
      });
      setRecommendations(res);
      setStep(3);
    } catch (err: any) {
      setError('Failed to fetch recommendations. Please check inputs.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateItinerary = async () => {
    try {
      setGenerating(true);
      setError(null);
      const response = await tripService.generateItinerary({
        destination_id: selectedDestination,
        duration_days: durationDays,
        total_budget: budget,
        party_size: partySize,
        interests: selectedInterests.length > 0 ? selectedInterests : ['heritage'],
        pace,
        preferred_transport: transport,
        travel_month: travelMonth,
        start_date: startDate,
      });

      navigate(`/itinerary/${response.trip_id}`, { state: { generatedData: response } });
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to generate itinerary. Please try again.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setGenerating(false);
    }
  };

  const goToStep = async (targetStep: number) => {
    if (loading) return;
    if (targetStep === 1) {
      setStep(1);
    } else if (targetStep === 2) {
      setStep(2);
    } else if (targetStep === 3) {
      if (recommendations.length > 0) {
        setStep(3);
      } else {
        await handleFetchRecommendations();
      }
    }
  };

  return (
    <div className="min-h-[calc(100vh-64px)] max-w-5xl mx-auto px-4 py-6 sm:px-6 sm:py-8 flex flex-col justify-between">
      <div className="space-y-6 flex-1">
        {/* Wizard Progress Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 rounded-full text-xs font-bold border border-emerald-200/60 dark:border-emerald-800">
            <Sparkles className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>Deterministic AI Optimizer</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            🗺️ Plan Your Optimal Itinerary
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-neutral-400 max-w-xl mx-auto">
            Configure destination, budget, and travel preferences to generate a mathematically optimized route with Google OR-Tools.
          </p>

          {/* Stepper Indicator */}
          <div className="flex items-center justify-center gap-2 sm:gap-4 pt-3">
            {/* Step 1 */}
            <button
              type="button"
              onClick={() => goToStep(1)}
              className={`liquid-btn flex items-center gap-2 px-4 py-2 rounded-full text-xs font-extrabold cursor-pointer select-none ${
                step === 1
                  ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black shadow-md shadow-emerald-600/25 dark:shadow-emerald-500/30 ring-2 ring-emerald-500/30 dark:ring-emerald-400/50'
                  : 'bg-slate-100 dark:bg-neutral-900 hover:bg-emerald-50 dark:hover:bg-neutral-850 text-slate-700 dark:text-neutral-300 hover:text-emerald-800 dark:hover:text-emerald-300 border border-slate-200 dark:border-neutral-800'
              }`}
              title="Go to 1. Destination"
            >
              <span>1. 📍 Destination</span>
              {step > 1 && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />}
            </button>

            <span className="w-6 sm:w-10 h-0.5 bg-slate-200 dark:bg-neutral-800" />

            {/* Step 2 */}
            <button
              type="button"
              onClick={() => goToStep(2)}
              className={`liquid-btn flex items-center gap-2 px-4 py-2 rounded-full text-xs font-extrabold cursor-pointer select-none ${
                step === 2
                  ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black shadow-md shadow-emerald-600/25 dark:shadow-emerald-500/30 ring-2 ring-emerald-500/30 dark:ring-emerald-400/50'
                  : 'bg-slate-100 dark:bg-neutral-900 hover:bg-emerald-50 dark:hover:bg-neutral-850 text-slate-700 dark:text-neutral-300 hover:text-emerald-800 dark:hover:text-emerald-300 border border-slate-200 dark:border-neutral-800'
              }`}
              title="Go to 2. Constraints"
            >
              <span>2. ⚙️ Constraints</span>
              {step > 2 && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />}
            </button>

            <span className="w-6 sm:w-10 h-0.5 bg-slate-200 dark:bg-neutral-800" />

            {/* Step 3 */}
            <button
              type="button"
              onClick={() => goToStep(3)}
              disabled={loading}
              className={`liquid-btn flex items-center gap-2 px-4 py-2 rounded-full text-xs font-extrabold cursor-pointer select-none ${
                step === 3
                  ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black shadow-md shadow-emerald-600/25 dark:shadow-emerald-500/30 ring-2 ring-emerald-500/30 dark:ring-emerald-400/50'
                  : 'bg-slate-100 dark:bg-neutral-900 hover:bg-emerald-50 dark:hover:bg-neutral-850 text-slate-700 dark:text-neutral-300 hover:text-emerald-800 dark:hover:text-emerald-300 border border-slate-200 dark:border-neutral-800'
              }`}
              title="Go to 3. AI Optimization"
            >
              {loading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-600 dark:text-emerald-400" />
              ) : null}
              <span>3. ✨ AI Optimization</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 rounded-2xl flex items-center gap-3 text-rose-700 dark:text-rose-300 text-sm shadow-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span className="font-semibold">{error}</span>
          </div>
        )}

        {/* STEP 1: Destination Selection */}
        {step === 1 && (
          <div className="liquid-glass rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-neutral-800 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-neutral-800 pb-4">
              <div>
                <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  <span>Choose Your Target Destination</span>
                </h2>
                <p className="text-xs text-slate-500 dark:text-neutral-400 mt-0.5">
                  Select one of our curated geographical scopes with complete geospatial attraction datasets.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {destinations.map((dest) => {
                const meta = DESTINATION_META[dest.id.toLowerCase()] || {
                  emoji: '📍',
                  highlight: dest.description,
                  badgeColor: 'bg-emerald-100 text-emerald-800',
                };
                const isSelected = selectedDestination === dest.id;

                return (
                  <div
                    key={dest.id}
                    onClick={() => setSelectedDestination(dest.id)}
                    className={`liquid-card p-5 rounded-2xl border-2 cursor-pointer relative ${
                      isSelected
                        ? 'border-emerald-600 dark:border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/30 shadow-md ring-2 ring-emerald-500/20 dark:ring-emerald-500/20'
                        : 'border-slate-200 dark:border-neutral-800 bg-white dark:bg-neutral-900/80 hover:border-emerald-300 dark:hover:border-emerald-500/60'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2.5">
                        <span className="text-2xl">{meta.emoji}</span>
                        <div>
                          <h3 className="font-bold text-slate-900 dark:text-white text-base">{dest.name}</h3>
                          <span className="text-[11px] font-semibold text-slate-400 dark:text-neutral-500">
                            {dest.state}
                          </span>
                        </div>
                      </div>
                      {isSelected ? (
                        <span className="flex items-center gap-1 text-[11px] font-extrabold px-2.5 py-0.5 bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black rounded-full shadow-sm">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Selected</span>
                        </span>
                      ) : (
                        <span className="text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 bg-slate-100 dark:bg-neutral-800 text-slate-600 dark:text-neutral-300 rounded-full">
                          {dest.id}
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-slate-600 dark:text-neutral-300 font-medium mb-3 mt-1">
                      {dest.description}
                    </p>

                    <div className="pt-2 border-t border-slate-100 dark:border-neutral-800 flex items-center justify-between text-xs">
                      <span className="font-semibold text-emerald-700 dark:text-emerald-400 flex items-center gap-1">
                        🌤️ Best: {dest.best_season}
                      </span>
                      <span className="text-[11px] font-bold text-slate-400 dark:text-neutral-500">
                        {meta.highlight}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex justify-end pt-4 border-t border-slate-100 dark:border-neutral-800">
              <button
                type="button"
                onClick={() => goToStep(2)}
                className="liquid-btn px-6 py-3 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-black font-extrabold rounded-xl flex items-center gap-2 text-sm shadow-md shadow-emerald-600/20 dark:shadow-emerald-500/20 cursor-pointer"
              >
                <span>Next: Constraints & Preferences</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: Constraints & Preferences */}
        {step === 2 && (
          <div className="liquid-glass rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-neutral-800 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-neutral-800 pb-4">
              <div>
                <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
                  <Gauge className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  <span>Trip Constraints & Travel Preferences</span>
                </h2>
                <p className="text-xs text-slate-500 dark:text-neutral-400 mt-0.5">
                  Customize duration, budget limits, travel pace, and transit vehicle for optimal routing.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Duration */}
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-neutral-300 uppercase tracking-wider mb-2">
                  📅 Trip Duration (Days)
                </label>
                <div className="flex items-center gap-2 sm:gap-3">
                  {[1, 2, 3, 4, 5, 7].map((d) => (
                    <button
                      key={`dur-${d}`}
                      type="button"
                      onClick={() => setDurationDays(d)}
                      className={`liquid-btn flex-1 py-2.5 rounded-xl font-bold text-xs sm:text-sm cursor-pointer ${
                        durationDays === d
                          ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black font-extrabold shadow-md shadow-emerald-600/20 dark:shadow-emerald-500/20 scale-105'
                          : 'bg-slate-100 dark:bg-neutral-900 text-slate-700 dark:text-neutral-300 hover:bg-slate-200 dark:hover:bg-neutral-800'
                      }`}
                    >
                      {d} {d === 1 ? 'Day' : 'Days'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Party Size */}
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-neutral-300 uppercase tracking-wider mb-2">
                  👥 Party Size (Travelers)
                </label>
                <div className="flex items-center gap-3">
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={partySize}
                    onChange={(e) => setPartySize(Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-full px-4 py-2.5 bg-slate-50 dark:bg-neutral-900 border border-slate-200 dark:border-neutral-800 rounded-xl text-sm font-bold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-500"
                  />
                  <span className="text-xs font-semibold text-slate-500 dark:text-neutral-400 shrink-0">
                    {partySize === 1 ? 'Solo Traveler' : `${partySize} Travelers`}
                  </span>
                </div>
              </div>

              {/* Total Budget */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-bold text-slate-700 dark:text-neutral-300 uppercase tracking-wider">
                    💰 Total Budget
                  </label>
                  <span className="text-sm font-extrabold text-emerald-700 dark:text-emerald-400">
                    ₹{budget.toLocaleString()}
                  </span>
                </div>
                <input
                  type="range"
                  min={2000}
                  max={60000}
                  step={1000}
                  value={budget}
                  onChange={(e) => setBudget(parseInt(e.target.value))}
                  className="w-full accent-emerald-600 dark:accent-emerald-400 cursor-pointer h-2 bg-slate-200 dark:bg-neutral-800 rounded-lg"
                />
                <div className="flex justify-between text-[11px] text-slate-400 dark:text-neutral-500 font-semibold mt-1">
                  <span>₹2,000 (Budget)</span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                    ~₹{Math.round(budget / partySize / durationDays).toLocaleString()}/person/day
                  </span>
                  <span>₹60,000 (Luxury)</span>
                </div>
              </div>

              {/* Travel Pace */}
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-neutral-300 uppercase tracking-wider mb-2">
                  🏃 Sightseeing Pace
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'Relaxed', label: 'Relaxed', emoji: '😌', desc: '2-3 spots/day' },
                    { id: 'Moderate', label: 'Moderate', emoji: '🚶', desc: '4-5 spots/day' },
                    { id: 'Intense', label: 'Intense', emoji: '⚡', desc: '6+ spots/day' },
                  ].map((p) => (
                    <button
                      key={`pace-${p.id}`}
                      type="button"
                      onClick={() => setPace(p.id)}
                      className={`liquid-card-interactive liquid-btn py-2 px-2.5 rounded-xl font-bold text-xs cursor-pointer flex flex-col items-center gap-0.5 border ${
                        pace === p.id
                          ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black font-extrabold shadow-md shadow-emerald-600/20 dark:shadow-emerald-500/20 border-emerald-600 dark:border-emerald-500'
                          : 'bg-slate-100 dark:bg-neutral-900 text-slate-700 dark:text-neutral-300 hover:bg-slate-200 dark:hover:bg-neutral-800 border-slate-200 dark:border-neutral-800'
                      }`}
                    >
                      <span>{p.emoji} {p.label}</span>
                      <span className={`text-[10px] ${pace === p.id ? 'text-emerald-100 dark:text-emerald-950' : 'text-slate-400 dark:text-neutral-500'}`}>
                        {p.desc}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Preferred Transport */}
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-neutral-300 uppercase tracking-wider mb-2">
                  🛺 Preferred Transit Vehicle
                </label>
                <select
                  value={transport}
                  onChange={(e) => setTransport(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-50 dark:bg-neutral-900 border border-slate-200 dark:border-neutral-800 rounded-xl text-sm font-bold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-500 cursor-pointer"
                >
                  {TRANSPORT_META.map((t) => (
                    <option key={t.id} value={t.id} className="dark:bg-neutral-900 dark:text-white">
                      {t.emoji} {t.label} — {t.cost}
                    </option>
                  ))}
                </select>
              </div>

              {/* Travel Month & Start Date */}
              <div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-neutral-300 uppercase tracking-wider mb-2">
                      🗓️ Travel Month
                    </label>
                    <select
                      value={travelMonth}
                      onChange={(e) => setTravelMonth(parseInt(e.target.value))}
                      className="w-full px-3 py-2.5 bg-slate-50 dark:bg-neutral-900 border border-slate-200 dark:border-neutral-800 rounded-xl text-xs font-bold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-500 cursor-pointer"
                    >
                      {MONTHS.map((item) => (
                        <option key={item.m} value={item.m} className="dark:bg-neutral-900 dark:text-white">
                          {item.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-neutral-300 uppercase tracking-wider mb-2">
                      📅 Start Date
                    </label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-50 dark:bg-neutral-900 border border-slate-200 dark:border-neutral-800 rounded-xl text-xs font-bold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-500"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Interest Tags */}
            <div className="pt-2">
              <label className="block text-xs font-bold text-slate-700 dark:text-neutral-300 uppercase tracking-wider mb-2">
                🎯 Interests & Themes (Select all that apply)
              </label>
              <div className="flex flex-wrap gap-2.5">
                {Object.entries(INTEREST_META).map(([key, item]) => {
                  const isSelected = selectedInterests.includes(key);
                  return (
                    <button
                      key={`tag-${key}`}
                      type="button"
                      onClick={() => handleInterestToggle(key)}
                      className={`liquid-card-interactive liquid-btn px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 cursor-pointer border ${
                        isSelected
                          ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black font-extrabold shadow-sm ring-2 ring-emerald-500/20 dark:ring-emerald-500/20 border-emerald-600 dark:border-emerald-500'
                          : 'bg-slate-100 dark:bg-neutral-900 text-slate-700 dark:text-neutral-300 hover:bg-slate-200 dark:hover:bg-neutral-800 border-slate-200 dark:border-neutral-800'
                      }`}
                    >
                      <span>{item.emoji}</span>
                      <span>{item.label}</span>
                      {isSelected && <CheckCircle2 className="w-3.5 h-3.5 ml-1" />}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex justify-between pt-6 border-t border-slate-100 dark:border-neutral-800">
              <button
                type="button"
                onClick={() => goToStep(1)}
                className="liquid-btn px-5 py-2.5 bg-slate-100 dark:bg-neutral-900 hover:bg-slate-200 dark:hover:bg-neutral-800 text-slate-700 dark:text-neutral-300 font-bold rounded-xl flex items-center gap-1.5 text-xs sm:text-sm cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Back to Destinations</span>
              </button>

              <button
                type="button"
                onClick={handleFetchRecommendations}
                disabled={loading}
                className="liquid-btn px-6 py-3 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-black font-extrabold rounded-xl flex items-center gap-2 text-xs sm:text-sm shadow-md shadow-emerald-600/20 dark:shadow-emerald-500/20 cursor-pointer disabled:opacity-60"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                <span>Preview MCDM Recommendations</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: Preview MCDM Recommendations & Generate */}
        {step === 3 && (
          <div className="liquid-glass rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-neutral-800 shadow-sm space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 dark:border-neutral-800 pb-4">
              <div>
                <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1">
                  <Sparkles className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <span>Phase 4 Multi-Criteria Recommendation Engine</span>
                </div>
                <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 dark:text-white">
                  Top Scored Attractions ({recommendations.length} Selected)
                </h2>
                <p className="text-xs text-slate-500 dark:text-neutral-400 mt-0.5">
                  Ranked by personalized interest alignment, seasonal suitability, and popularity score.
                </p>
              </div>

              <button
                type="button"
                onClick={handleGenerateItinerary}
                disabled={generating}
                className="liquid-btn px-6 py-3.5 bg-gradient-to-r from-emerald-600 to-amber-500 dark:from-emerald-500 dark:to-amber-500 hover:from-emerald-700 hover:to-amber-600 dark:hover:from-emerald-400 dark:hover:to-amber-400 text-white dark:text-black font-black rounded-xl shadow-lg shadow-emerald-600/25 dark:shadow-emerald-500/25 flex items-center gap-2 text-sm cursor-pointer disabled:opacity-60"
              >
                {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                <span>Generate Optimal Itinerary 🚀</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[460px] overflow-y-auto pr-1">
              {recommendations.map((rec) => (
                <div
                  key={rec.attraction.id}
                  className="liquid-card p-4 rounded-2xl border border-slate-200 dark:border-neutral-800 space-y-2.5"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-[11px] font-black px-2.5 py-0.5 bg-emerald-700 dark:bg-emerald-500 text-white dark:text-black rounded-full shadow-xs">
                          Rank #{rec.rank}
                        </span>
                        <span className="text-[11px] font-black px-2.5 py-0.5 bg-amber-100 dark:bg-amber-950/70 text-amber-900 dark:text-amber-300 rounded-full border border-amber-200 dark:border-amber-800/80 shadow-xs">
                          ✨ Score: {Math.round(rec.composite_score * 100)}% ({rec.composite_score.toFixed(2)})
                        </span>
                        <span className="text-[11px] font-extrabold uppercase tracking-wider px-2.5 py-0.5 bg-emerald-100 dark:bg-emerald-950/70 text-emerald-900 dark:text-emerald-300 rounded-full border border-emerald-200 dark:border-emerald-800">
                          {rec.attraction.category}
                        </span>
                      </div>
                      <h4 className="font-extrabold text-slate-900 dark:text-white text-base mt-1.5">
                        {rec.attraction.name}
                      </h4>
                    </div>
                    <span className="text-xs font-black text-slate-900 dark:text-white shrink-0 bg-white dark:bg-neutral-900 px-2.5 py-1 rounded-xl border-2 border-slate-200 dark:border-neutral-800 shadow-xs">
                      {rec.attraction.entry_fee > 0 ? `₹${rec.attraction.entry_fee}` : 'Free Entry 🎉'}
                    </span>
                  </div>

                  <p className="text-xs text-slate-700 dark:text-neutral-300 font-medium line-clamp-2">{rec.breakdown.reason}</p>

                  {/* High-Contrast Score Breakdown Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2.5 border-t border-slate-200 dark:border-neutral-800">
                    {/* Interest */}
                    <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200/90 dark:border-amber-800/60 p-2 rounded-xl flex flex-col items-center justify-center text-center shadow-xs">
                      <span className="text-[11px] font-black text-amber-900 dark:text-amber-300 tracking-wide flex items-center gap-1">
                        <span>🎯</span>
                        <span>Interest</span>
                      </span>
                      <span className="text-sm font-black text-amber-950 dark:text-amber-200 font-mono mt-0.5">
                        {Math.round(rec.breakdown.interest_score * 100)}%
                      </span>
                      <span className="text-[10px] font-bold text-amber-800/90 dark:text-amber-400/90 font-mono">
                        ({rec.breakdown.interest_score.toFixed(2)})
                      </span>
                    </div>

                    {/* Season */}
                    <div className="bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/90 dark:border-emerald-800/60 p-2 rounded-xl flex flex-col items-center justify-center text-center shadow-xs">
                      <span className="text-[11px] font-black text-emerald-900 dark:text-emerald-300 tracking-wide flex items-center gap-1">
                        <span>🌤️</span>
                        <span>Season</span>
                      </span>
                      <span className="text-sm font-black text-emerald-950 dark:text-emerald-200 font-mono mt-0.5">
                        {Math.round(rec.breakdown.season_score * 100)}%
                      </span>
                      <span className="text-[10px] font-bold text-emerald-800/90 dark:text-emerald-400/90 font-mono">
                        ({rec.breakdown.season_score.toFixed(2)})
                      </span>
                    </div>

                    {/* Popularity */}
                    <div className="bg-purple-50 dark:bg-purple-950/40 border border-purple-200/90 dark:border-purple-800/60 p-2 rounded-xl flex flex-col items-center justify-center text-center shadow-xs">
                      <span className="text-[11px] font-black text-purple-900 dark:text-purple-300 tracking-wide flex items-center gap-1">
                        <span>🔥</span>
                        <span>Popular</span>
                      </span>
                      <span className="text-sm font-black text-purple-950 dark:text-purple-200 font-mono mt-0.5">
                        {Math.round(rec.breakdown.popularity_score * 100)}%
                      </span>
                      <span className="text-[10px] font-bold text-purple-800/90 dark:text-purple-400/90 font-mono">
                        ({rec.breakdown.popularity_score.toFixed(2)})
                      </span>
                    </div>

                    {/* Rating */}
                    <div className="bg-emerald-50 dark:bg-yellow-950/40 border border-emerald-200/90 dark:border-yellow-800/60 p-2 rounded-xl flex flex-col items-center justify-center text-center shadow-xs">
                      <span className="text-[11px] font-black text-emerald-900 dark:text-yellow-300 tracking-wide flex items-center gap-1">
                        <span>⭐</span>
                        <span>Rating</span>
                      </span>
                      <span className="text-sm font-black text-emerald-950 dark:text-yellow-200 font-mono mt-0.5">
                        {Math.round(rec.breakdown.rating_score * 100)}%
                      </span>
                      <span className="text-[10px] font-bold text-emerald-800/90 dark:text-yellow-400/90 font-mono">
                        ({rec.breakdown.rating_score.toFixed(2)})
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-between pt-4 border-t border-slate-100 dark:border-neutral-800">
              <button
                type="button"
                onClick={() => goToStep(2)}
                className="liquid-btn px-5 py-2.5 bg-slate-100 dark:bg-neutral-900 hover:bg-slate-200 dark:hover:bg-neutral-800 text-slate-700 dark:text-neutral-300 font-bold rounded-xl flex items-center gap-1.5 text-xs sm:text-sm cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Back to Constraints</span>
              </button>

              <button
                type="button"
                onClick={handleGenerateItinerary}
                disabled={generating}
                className="liquid-btn px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-black font-extrabold rounded-xl flex items-center gap-2 text-xs sm:text-sm shadow-md cursor-pointer disabled:opacity-60"
              >
                {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                <span>Generate Route</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
