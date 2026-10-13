import React, { useState, useEffect } from 'react';
import { transportService } from '../../services/transportService';
import { IntercityRecommendationResponse, IntercityOption } from '../../types';
import {
  Compass,
  Car,
  Bike,
  Bus,
  Train,
  Plane,
  Ship,
  Clock,
  DollarSign,
  Users,
  ShieldCheck,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Search,
  CheckCircle2,
  XCircle,
  Sparkles,
} from 'lucide-react';

interface IntercityTransportCardProps {
  destinationId: string;
  partySize?: number;
  budget?: number;
  initialOrigin?: string;
}

const COMMON_ORIGINS = [
  'Bengaluru',
  'Mumbai',
  'Pune',
  'Hyderabad',
  'Mysuru',
  'Mangaluru',
  'Hubballi',
  'Belagavi',
];

const MODE_ICONS: Record<string, React.ReactNode> = {
  car: <Car className="w-5 h-5" />,
  bike: <Bike className="w-5 h-5" />,
  bus: <Bus className="w-5 h-5" />,
  train: <Train className="w-5 h-5" />,
  flight: <Plane className="w-5 h-5" />,
  boat: <Ship className="w-5 h-5" />,
};

export const IntercityTransportCard: React.FC<IntercityTransportCardProps> = ({
  destinationId,
  partySize = 2,
  budget,
  initialOrigin = 'Bengaluru',
}) => {
  const [origin, setOrigin] = useState<string>(initialOrigin);
  const [customOrigin, setCustomOrigin] = useState<string>('');
  const [data, setData] = useState<IntercityRecommendationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedMode, setExpandedMode] = useState<string | null>(null);

  useEffect(() => {
    if (origin && destinationId) {
      fetchRecommendations(origin);
    }
  }, [origin, destinationId, partySize, budget]);

  const fetchRecommendations = async (targetOrigin: string) => {
    if (!targetOrigin.trim()) return;
    try {
      setLoading(true);
      setError(null);
      const res = await transportService.getIntercityRecommendations({
        origin: targetOrigin.trim(),
        destination: destinationId,
        party_size: partySize,
        budget: budget,
      });
      setData(res);
      // Auto-expand best-ranked option
      if (res.options && res.options.length > 0) {
        setExpandedMode(res.options[0].transport_mode);
      }
    } catch (err: any) {
      console.error('Failed to load intercity recommendations', err);
      const msg = err.response?.data?.detail || 'Unable to load intercity transit recommendations.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCustomOriginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customOrigin.trim()) {
      setOrigin(customOrigin.trim());
    }
  };

  const toggleExpand = (mode: string) => {
    setExpandedMode((prev) => (prev === mode ? null : mode));
  };

  return (
    <div className="liquid-glass rounded-3xl p-5 sm:p-6 border border-slate-200 dark:border-neutral-800 shadow-sm space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 dark:border-neutral-800 pb-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 rounded-full text-[11px] font-extrabold uppercase tracking-wider border border-emerald-200 dark:border-emerald-800/60 mb-1">
            <Compass className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>Intercity Transit Assistant</span>
          </div>
          <h3 className="text-lg font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <span>Travel Modes to {destinationId.toUpperCase()}</span>
          </h3>
          <p className="text-xs text-slate-500 dark:text-neutral-400">
            Compare intercity transit (Car, Bike, Bus, Train, Flight, Boat) from your departure city for {partySize} traveler{partySize > 1 ? 's' : ''}.
          </p>
        </div>

        <button
          onClick={() => fetchRecommendations(origin)}
          disabled={loading}
          className="liquid-btn px-3 py-1.5 bg-slate-100 dark:bg-neutral-800 hover:bg-slate-200 dark:hover:bg-neutral-700 text-slate-700 dark:text-neutral-200 text-xs font-bold rounded-xl flex items-center gap-1.5 cursor-pointer transition-colors"
          title="Refresh recommendations"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Recalculate</span>
        </button>
      </div>

      {/* Origin Selector */}
      <div className="space-y-2">
        <label className="block text-[11px] font-bold text-slate-600 dark:text-neutral-400 uppercase tracking-wider">
          📍 Select or Enter Starting City
        </label>
        <div className="flex flex-wrap items-center gap-2">
          {COMMON_ORIGINS.map((city) => (
            <button
              key={city}
              type="button"
              onClick={() => {
                setOrigin(city);
                setCustomOrigin('');
              }}
              className={`px-3 py-1 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                origin.toLowerCase() === city.toLowerCase()
                  ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black shadow-xs font-extrabold'
                  : 'bg-white dark:bg-neutral-900 border border-slate-200 dark:border-neutral-800 text-slate-700 dark:text-neutral-300 hover:bg-slate-100 dark:hover:bg-neutral-800'
              }`}
            >
              {city}
            </button>
          ))}
        </div>

        {/* Custom Input */}
        <form onSubmit={handleCustomOriginSubmit} className="flex items-center gap-2 pt-1">
          <div className="relative flex-1 max-w-sm">
            <input
              type="text"
              placeholder="Or type another origin (e.g. Solapur, Chennai)..."
              value={customOrigin}
              onChange={(e) => setCustomOrigin(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs font-semibold bg-white dark:bg-neutral-900 border border-slate-200 dark:border-neutral-800 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
          </div>
          <button
            type="submit"
            disabled={!customOrigin.trim()}
            className="px-3.5 py-1.5 bg-slate-800 dark:bg-neutral-700 hover:bg-slate-900 dark:hover:bg-neutral-600 disabled:opacity-50 text-white text-xs font-bold rounded-xl cursor-pointer transition-colors"
          >
            Compare
          </button>
        </form>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="py-8 text-center space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin text-emerald-600 mx-auto" />
          <p className="text-xs font-bold text-slate-500 dark:text-neutral-400">
            Calculating distance, estimated duration & group cost from {origin}...
          </p>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 rounded-2xl flex items-center justify-between gap-3 text-xs text-rose-700 dark:text-rose-300 font-semibold">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => fetchRecommendations(origin)}
            className="px-2.5 py-1 bg-rose-200 dark:bg-rose-900 rounded-lg text-[11px] font-bold text-rose-900 dark:text-rose-100 hover:bg-rose-300"
          >
            Retry
          </button>
        </div>
      )}

      {/* Options List */}
      {!loading && data && (
        <div className="space-y-3">
          {/* Top highlight bar */}
          <div className="flex flex-wrap items-center justify-between text-xs font-semibold px-2 text-slate-600 dark:text-neutral-400">
            <span className="flex items-center gap-1.5">
              <span>Departure: <strong>{data.origin}</strong></span>
              <span>&rarr;</span>
              <span>Destination: <strong>{data.destination}</strong></span>
            </span>
            <div className="flex items-center gap-3 text-[11px]">
              {data.cheapest_mode && (
                <span className="text-emerald-700 dark:text-emerald-400 font-bold">
                  💰 Cheapest: <span className="uppercase">{data.cheapest_mode}</span>
                </span>
              )}
              {data.fastest_mode && (
                <span className="text-sky-700 dark:text-sky-400 font-bold">
                  ⚡ Fastest: <span className="uppercase">{data.fastest_mode}</span>
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {data.options.map((opt: IntercityOption) => {
              const isExpanded = expandedMode === opt.transport_mode;
              const isAvailable = opt.is_available;

              return (
                <div
                  key={opt.transport_mode}
                  className={`rounded-2xl border transition-all ${
                    !isAvailable
                      ? 'bg-slate-50/60 dark:bg-neutral-900/40 border-slate-200 dark:border-neutral-800/80 opacity-70'
                      : opt.rank === 1
                      ? 'bg-emerald-50/40 dark:bg-emerald-950/20 border-emerald-300 dark:border-emerald-800/80 shadow-xs'
                      : 'bg-white dark:bg-neutral-900 border-slate-200 dark:border-neutral-800'
                  }`}
                >
                  {/* Option Card Header */}
                  <div
                    onClick={() => toggleExpand(opt.transport_mode)}
                    className="p-4 flex flex-wrap items-center justify-between gap-3 cursor-pointer select-none"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold ${
                          !isAvailable
                            ? 'bg-slate-200 dark:bg-neutral-800 text-slate-400'
                            : opt.rank === 1
                            ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black shadow-xs'
                            : 'bg-slate-100 dark:bg-neutral-800 text-slate-700 dark:text-neutral-300'
                        }`}
                      >
                        {MODE_ICONS[opt.transport_mode] || <Car className="w-5 h-5" />}
                      </div>

                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-extrabold text-slate-900 dark:text-white">
                            {opt.mode_name}
                          </h4>
                          {opt.rank === 1 && isAvailable && (
                            <span className="px-2 py-0.5 bg-emerald-600 dark:bg-emerald-400 text-white dark:text-black text-[10px] font-extrabold rounded-full flex items-center gap-1">
                              <Sparkles className="w-2.5 h-2.5" />
                              <span>Top Ranked</span>
                            </span>
                          )}
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                              opt.verification_status === 'VERIFIED'
                                ? 'bg-sky-100 dark:bg-sky-950/70 text-sky-800 dark:text-sky-300'
                                : opt.verification_status === 'ESTIMATED'
                                ? 'bg-amber-100 dark:bg-amber-950/70 text-amber-800 dark:text-amber-300'
                                : 'bg-slate-100 dark:bg-neutral-800 text-slate-500'
                            }`}
                          >
                            {opt.verification_status}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 dark:text-neutral-400 line-clamp-1 mt-0.5">
                          {isAvailable ? opt.recommendation_reason : opt.unavailability_reason}
                        </p>
                      </div>
                    </div>

                    {/* Right side metrics */}
                    <div className="flex items-center gap-4 text-right">
                      {isAvailable ? (
                        <>
                          <div className="hidden sm:block">
                            <span className="text-[10px] font-bold text-slate-400 uppercase block">Duration</span>
                            <span className="text-xs font-extrabold text-slate-800 dark:text-neutral-200 flex items-center justify-end gap-1">
                              <Clock className="w-3 h-3 text-slate-400" />
                              <span>{opt.estimated_duration_hours} hrs</span>
                            </span>
                          </div>

                          <div>
                            <span className="text-[10px] font-bold text-slate-400 uppercase block">
                              Total ({partySize}p)
                            </span>
                            <span className="text-sm font-extrabold text-slate-900 dark:text-white">
                              ₹{opt.estimated_total_cost?.toLocaleString()}
                            </span>
                            <span className="text-[10px] text-slate-400 block">
                              (₹{opt.estimated_cost_per_person?.toLocaleString()}/person)
                            </span>
                          </div>
                        </>
                      ) : (
                        <span className="text-xs font-bold text-rose-600 dark:text-rose-400 flex items-center gap-1">
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Not Feasible</span>
                        </span>
                      )}

                      <div className="text-slate-400 hover:text-slate-600 dark:hover:text-neutral-200">
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </div>
                    </div>
                  </div>

                  {/* Expanded Accordion Details */}
                  {isExpanded && (
                    <div className="px-4 pb-4 pt-2 border-t border-slate-100 dark:border-neutral-800/80 text-xs space-y-3">
                      {isAvailable ? (
                        <>
                          {/* Metrics row */}
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-neutral-800/60 border border-slate-100 dark:border-neutral-800">
                              <span className="text-[10px] font-bold text-slate-400 uppercase block">Distance</span>
                              <span className="font-extrabold text-slate-900 dark:text-white">
                                {opt.distance_km} km
                              </span>
                              <span className="text-[10px] text-slate-500 block capitalize">
                                {opt.distance_type.replace(/_/g, ' ')}
                              </span>
                            </div>

                            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-neutral-800/60 border border-slate-100 dark:border-neutral-800">
                              <span className="text-[10px] font-bold text-slate-400 uppercase block">Travel Time</span>
                              <span className="font-extrabold text-slate-900 dark:text-white">
                                {opt.estimated_duration_hours} Hours
                              </span>
                              <span className="text-[10px] text-slate-500 block">Estimated journey</span>
                            </div>

                            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-neutral-800/60 border border-slate-100 dark:border-neutral-800">
                              <span className="text-[10px] font-bold text-slate-400 uppercase block">Group Suitability</span>
                              <span className="font-extrabold text-slate-900 dark:text-white">
                                {opt.group_suitability_label}
                              </span>
                              <span className="text-[10px] text-slate-500 block truncate" title={opt.group_suitability_notes}>
                                {opt.group_suitability_notes}
                              </span>
                            </div>

                            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-neutral-800/60 border border-slate-100 dark:border-neutral-800">
                              <span className="text-[10px] font-bold text-slate-400 uppercase block">Budget Status</span>
                              <span
                                className={`font-extrabold ${
                                  opt.budget_compatibility === 'WITHIN_BUDGET'
                                    ? 'text-emerald-600 dark:text-emerald-400'
                                    : opt.budget_compatibility === 'OVER_BUDGET'
                                    ? 'text-rose-600 dark:text-rose-400'
                                    : 'text-slate-700 dark:text-neutral-300'
                                }`}
                              >
                                {opt.budget_compatibility === 'WITHIN_BUDGET'
                                  ? 'Within Budget'
                                  : opt.budget_compatibility === 'OVER_BUDGET'
                                  ? 'Exceeds Budget'
                                  : 'Not Specified'}
                              </span>
                              <span className="text-[10px] text-slate-500 block">
                                Rate: ₹{opt.cost_per_km}/km
                              </span>
                            </div>
                          </div>

                          {/* Advantages & Limitations */}
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                            {opt.advantages.length > 0 && (
                              <div className="space-y-1">
                                <span className="text-[11px] font-bold text-emerald-800 dark:text-emerald-400 flex items-center gap-1">
                                  <CheckCircle2 className="w-3 h-3" />
                                  <span>Advantages</span>
                                </span>
                                <ul className="space-y-0.5 text-[11px] text-slate-600 dark:text-neutral-300">
                                  {opt.advantages.map((adv, i) => (
                                    <li key={i} className="flex items-start gap-1.5">
                                      <span className="text-emerald-500 font-bold">&bull;</span>
                                      <span>{adv}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {opt.limitations.length > 0 && (
                              <div className="space-y-1">
                                <span className="text-[11px] font-bold text-amber-800 dark:text-amber-400 flex items-center gap-1">
                                  <AlertTriangle className="w-3 h-3" />
                                  <span>Considerations</span>
                                </span>
                                <ul className="space-y-0.5 text-[11px] text-slate-600 dark:text-neutral-300">
                                  {opt.limitations.map((lim, i) => (
                                    <li key={i} className="flex items-start gap-1.5">
                                      <span className="text-amber-500 font-bold">&bull;</span>
                                      <span>{lim}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>

                          {/* Provenance Footer */}
                          <div className="pt-2 text-[10px] text-slate-400 dark:text-neutral-500 flex flex-wrap items-center justify-between border-t border-slate-100 dark:border-neutral-800">
                            <span>
                              Data Source:{' '}
                              <strong>{opt.data_provenance?.source || 'Curated Regional Benchmark'}</strong>
                            </span>
                            {opt.data_provenance?.nearest_railhead && (
                              <span>Railhead: {opt.data_provenance.nearest_railhead}</span>
                            )}
                            {opt.data_provenance?.nearest_airport && (
                              <span>Airport: {opt.data_provenance.nearest_airport}</span>
                            )}
                          </div>
                        </>
                      ) : (
                        <div className="p-3 bg-slate-100 dark:bg-neutral-800 rounded-xl space-y-1">
                          <span className="text-[11px] font-bold text-slate-700 dark:text-neutral-300 flex items-center gap-1">
                            <Info className="w-3.5 h-3.5 text-slate-400" />
                            <span>Why is this option unavailable?</span>
                          </span>
                          <p className="text-xs text-slate-600 dark:text-neutral-400">
                            {opt.unavailability_reason}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <p className="text-[10px] text-slate-400 dark:text-neutral-500 text-center pt-1 italic">
            * Intercity transit costs and durations are estimates based on regional benchmarks. In-app bookings are not made; check official carriers for live reservations.
          </p>
        </div>
      )}
    </div>
  );
};
