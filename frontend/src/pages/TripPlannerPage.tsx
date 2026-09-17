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
  Heart,
  Gauge,
  Car,
  Sparkles,
  Loader2,
  ChevronRight,
  ChevronLeft,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';

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

  return (
    <div className="max-w-4xl mx-auto py-8 space-y-8">
      {/* Wizard Progress Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-extrabold text-slate-900">Plan Your Optimal Itinerary</h1>
        <p className="text-sm text-slate-500">
          Configure trip constraints for deterministic Multi-Criteria & OR-Tools Optimization
        </p>

        <div className="flex items-center justify-center gap-3 pt-4">
          <span
            className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
              step >= 1 ? 'bg-teal-600 text-white' : 'bg-slate-200 text-slate-600'
            }`}
          >
            1
          </span>
          <span className="w-12 h-0.5 bg-slate-200" />
          <span
            className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
              step >= 2 ? 'bg-teal-600 text-white' : 'bg-slate-200 text-slate-600'
            }`}
          >
            2
          </span>
          <span className="w-12 h-0.5 bg-slate-200" />
          <span
            className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
              step >= 3 ? 'bg-teal-600 text-white' : 'bg-slate-200 text-slate-600'
            }`}
          >
            3
          </span>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-center gap-3 text-rose-700 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* STEP 1: Destination Selection */}
      {step === 1 && (
        <div className="bg-white rounded-3xl p-6 md:p-8 border border-slate-200 shadow-sm space-y-6">
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Compass className="w-5 h-5 text-teal-600" />
            <span>Select Destination</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {destinations.map((dest) => (
              <div
                key={dest.id}
                onClick={() => setSelectedDestination(dest.id)}
                className={`p-5 rounded-2xl border-2 cursor-pointer transition-all ${
                  selectedDestination === dest.id
                    ? 'border-teal-600 bg-teal-50/40 shadow-md'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold text-slate-900 text-lg">{dest.name}</h3>
                  <span className="text-xs uppercase px-2 py-0.5 bg-slate-100 rounded-full text-slate-600">
                    {dest.state}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mb-3">{dest.description}</p>
                <span className="text-xs font-semibold text-teal-700 block">
                  Best Season: {dest.best_season}
                </span>
              </div>
            ))}
          </div>

          <div className="flex justify-end pt-4">
            <button
              onClick={() => setStep(2)}
              className="px-6 py-3 bg-teal-600 hover:bg-teal-700 text-white font-bold rounded-xl flex items-center gap-2 text-sm shadow-md cursor-pointer"
            >
              <span>Next: Constraints & Preferences</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: Constraints & Preferences */}
      {step === 2 && (
        <div className="bg-white rounded-3xl p-6 md:p-8 border border-slate-200 shadow-sm space-y-6">
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Gauge className="w-5 h-5 text-teal-600" />
            <span>Trip Constraints & Pace</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Duration */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Trip Duration (Days)
              </label>
              <div className="flex items-center gap-3">
                {[1, 2, 3, 4, 5, 7].map((d) => (
                  <button
                    key={`dur-${d}`}
                    type="button"
                    onClick={() => setDurationDays(d)}
                    className={`w-10 h-10 rounded-xl font-bold text-sm transition-all cursor-pointer ${
                      durationDays === d
                        ? 'bg-teal-600 text-white shadow-md'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>

            {/* Party Size */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Party Size (Travelers)
              </label>
              <input
                type="number"
                min={1}
                max={20}
                value={partySize}
                onChange={(e) => setPartySize(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            {/* Total Budget */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Total Budget (INR): ₹{budget.toLocaleString()}
              </label>
              <input
                type="range"
                min={2000}
                max={60000}
                step={1000}
                value={budget}
                onChange={(e) => setBudget(parseInt(e.target.value))}
                className="w-full accent-teal-600 cursor-pointer"
              />
            </div>

            {/* Travel Pace */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Sightseeing Pace
              </label>
              <div className="grid grid-cols-3 gap-2">
                {['Relaxed', 'Moderate', 'Intense'].map((p) => (
                  <button
                    key={`pace-${p}`}
                    type="button"
                    onClick={() => setPace(p)}
                    className={`py-2 px-3 rounded-xl font-semibold text-xs transition-all cursor-pointer ${
                      pace === p
                        ? 'bg-teal-600 text-white shadow'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>

            {/* Preferred Transport */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Preferred Transport
              </label>
              <select
                value={transport}
                onChange={(e) => setTransport(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="auto">Auto Rickshaw (₹15/km, Base ₹30)</option>
                <option value="car">Taxi / Cab (₹22/km, Base ₹100)</option>
                <option value="rental">Self-Drive Rental (₹12/km, Base ₹400)</option>
                <option value="walking">Walking / On Foot (₹0/km)</option>
                <option value="public">Public Bus / Transit (₹4/km)</option>
              </select>
            </div>

            {/* Travel Month */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Travel Month
              </label>
              <select
                value={travelMonth}
                onChange={(e) => setTravelMonth(parseInt(e.target.value))}
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                {[
                  { m: 1, name: 'January' },
                  { m: 2, name: 'February' },
                  { m: 3, name: 'March' },
                  { m: 4, name: 'April' },
                  { m: 5, name: 'May' },
                  { m: 6, name: 'June' },
                  { m: 7, name: 'July' },
                  { m: 8, name: 'August' },
                  { m: 9, name: 'September' },
                  { m: 10, name: 'October' },
                  { m: 11, name: 'November' },
                  { m: 12, name: 'December' },
                ].map((item) => (
                  <option key={item.m} value={item.m}>
                    {item.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Interest Tags */}
          <div className="pt-2">
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Interests & Themes
            </label>
            <div className="flex flex-wrap gap-2">
              {['heritage', 'nature', 'adventure', 'religious', 'beach'].map((tag) => (
                <button
                  key={`tag-${tag}`}
                  type="button"
                  onClick={() => handleInterestToggle(tag)}
                  className={`px-4 py-2 rounded-xl text-xs font-bold capitalize transition-all cursor-pointer ${
                    selectedInterests.includes(tag)
                      ? 'bg-teal-600 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-between pt-6 border-t border-slate-100">
            <button
              onClick={() => setStep(1)}
              className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl flex items-center gap-1.5 text-sm cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Back</span>
            </button>

            <button
              onClick={handleFetchRecommendations}
              disabled={loading}
              className="px-6 py-3 bg-teal-600 hover:bg-teal-700 text-white font-bold rounded-xl flex items-center gap-2 text-sm shadow-md cursor-pointer disabled:opacity-60"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              <span>Preview MCDM Recommendations</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Preview MCDM Recommendations & Generate */}
      {step === 3 && (
        <div className="bg-white rounded-3xl p-6 md:p-8 border border-slate-200 shadow-sm space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 text-teal-600 text-xs font-bold uppercase tracking-wider mb-1">
                <Sparkles className="w-4 h-4" />
                <span>Phase 4 MCDM Engine</span>
              </div>
              <h2 className="text-xl font-bold text-slate-900">
                Top Scored Attractions ({recommendations.length})
              </h2>
            </div>

            <button
              onClick={handleGenerateItinerary}
              disabled={generating}
              className="px-6 py-3.5 bg-teal-600 hover:bg-teal-700 text-white font-bold rounded-xl shadow-lg shadow-teal-600/20 flex items-center gap-2 text-sm cursor-pointer disabled:opacity-60"
            >
              {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              <span>Generate Optimal Itinerary</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[480px] overflow-y-auto pr-1">
            {recommendations.map((rec) => (
              <div
                key={rec.attraction.id}
                className="p-4 rounded-2xl border border-slate-200 bg-slate-50/50 space-y-2"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-bold px-2 py-0.5 bg-teal-100 text-teal-800 rounded-full uppercase">
                      Rank #{rec.rank} &bull; Score {rec.composite_score}
                    </span>
                    <h4 className="font-bold text-slate-900 text-sm mt-1">
                      {rec.attraction.name}
                    </h4>
                  </div>
                  <span className="text-xs font-bold text-slate-700">
                    {rec.attraction.entry_fee > 0 ? `₹${rec.attraction.entry_fee}` : 'Free'}
                  </span>
                </div>

                <p className="text-xs text-slate-500 line-clamp-2">{rec.breakdown.reason}</p>

                {/* Score breakdown metrics */}
                <div className="grid grid-cols-4 gap-1 pt-2 border-t border-slate-200/60 text-[10px] text-center font-mono">
                  <div className="bg-white p-1 rounded">
                    <span className="text-slate-400 block">Interest</span>
                    <span className="font-bold text-slate-700">{rec.breakdown.interest_score}</span>
                  </div>
                  <div className="bg-white p-1 rounded">
                    <span className="text-slate-400 block">Season</span>
                    <span className="font-bold text-slate-700">{rec.breakdown.season_score}</span>
                  </div>
                  <div className="bg-white p-1 rounded">
                    <span className="text-slate-400 block">Popularity</span>
                    <span className="font-bold text-slate-700">{rec.breakdown.popularity_score}</span>
                  </div>
                  <div className="bg-white p-1 rounded">
                    <span className="text-slate-400 block">Rating</span>
                    <span className="font-bold text-slate-700">{rec.breakdown.rating_score}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(2)}
              className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl flex items-center gap-1.5 text-sm cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
