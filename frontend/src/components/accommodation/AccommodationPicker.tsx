import React, { useState, useEffect } from 'react';
import { accommodationService } from '../../services/accommodationService';
import {
  AccommodationRecommendationResponse,
  AccommodationRecommendationItem,
} from '../../types';
import { AccommodationCard } from './AccommodationCard';
import {
  Hotel,
  Sparkles,
  ShieldCheck,
  DollarSign,
  Users,
  Calendar,
  Loader2,
  AlertCircle,
  Filter,
  CheckCircle2,
  X,
  MapPin,
} from 'lucide-react';

interface AccommodationPickerProps {
  destinationId: string;
  partySize?: number;
  totalBudget?: number;
  startDate?: string;
  durationDays?: number;
  intercityTransportCost?: number;
  itinerary?: any;
  selectedAccommodation?: AccommodationRecommendationItem | null;
  onSelectAccommodation: (item: AccommodationRecommendationItem | null) => void;
}

export const AccommodationPicker: React.FC<AccommodationPickerProps> = ({
  destinationId,
  partySize,
  totalBudget,
  startDate,
  durationDays,
  intercityTransportCost,
  itinerary,
  selectedAccommodation,
  onSelectAccommodation,
}) => {
  const [data, setData] = useState<AccommodationRecommendationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('All');

  // Compute check-out date
  const computeCheckOutDate = (start: string, days: number): string => {
    try {
      const d = new Date(start);
      if (isNaN(d.getTime())) {
        return start;
      }
      d.setDate(d.getDate() + Math.max(days, 1));
      return d.toISOString().split('T')[0];
    } catch {
      return start;
    }
  };

  const checkInDate = startDate;
  const checkOutDate = (startDate && durationDays) ? computeCheckOutDate(startDate, durationDays) : undefined;
  const hasRequiredConstraints = Boolean(
    destinationId && checkInDate && checkOutDate && partySize && partySize > 0
  );

  // Auto-reset selected accommodation if destination has changed
  useEffect(() => {
    if (selectedAccommodation && selectedAccommodation.accommodation.destination_id !== destinationId) {
      onSelectAccommodation(null);
    }
  }, [destinationId, selectedAccommodation, onSelectAccommodation]);

  useEffect(() => {
    let isCancelled = false;

    if (!hasRequiredConstraints) {
      setData(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    accommodationService.getRecommendations({
      destination_id: destinationId,
      check_in_date: checkInDate!,
      check_out_date: checkOutDate!,
      party_size: partySize!,
      total_budget: totalBudget,
      intercity_transport_cost: intercityTransportCost,
      category: selectedCategory !== 'all' ? selectedCategory : undefined,
      preferred_type: selectedType !== 'All' ? selectedType.toLowerCase() : undefined,
      trip_id: itinerary?.trip_id,
      itinerary_days: itinerary?.days,
    }).then((res) => {
      if (!isCancelled) {
        setData(res);
        setLoading(false);
      }
    }).catch((err: any) => {
      if (!isCancelled) {
        console.error('Failed to load accommodation recommendations', err);
        const msg = err.response?.data?.detail || 'Unable to fetch accommodation recommendations.';
        setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
        setData(null);
        setLoading(false);
      }
    });

    return () => {
      isCancelled = true;
    };
  }, [
    destinationId,
    partySize,
    totalBudget,
    checkInDate,
    checkOutDate,
    selectedCategory,
    selectedType,
    intercityTransportCost,
    hasRequiredConstraints,
    itinerary,
  ]);

  const handleSelect = (item: AccommodationRecommendationItem) => {
    if (selectedAccommodation?.accommodation.id === item.accommodation.id) {
      // Toggle unselect
      onSelectAccommodation(null);
    } else {
      onSelectAccommodation(item);
    }
  };

  return (
    <div className="liquid-glass rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-neutral-800 shadow-sm space-y-6">
      {/* Component Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-neutral-800 pb-4">
        <div>
          <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1 flex-wrap">
            <div className="flex items-center gap-1.5">
              <Hotel className="w-4 h-4" />
              <span>Phase 2 Budget-Based Accommodations</span>
            </div>
            {data?.is_itinerary_aware && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-blue-100 dark:bg-blue-950/70 text-blue-900 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                <MapPin className="w-3 h-3 text-blue-600 dark:text-blue-400" />
                <span>Itinerary-Aware Proximity ({data.total_itinerary_days_evaluated} Days Evaluated)</span>
              </span>
            )}
          </div>
          <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <span>Curated Lodging & Room Capacity Optimizer</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-neutral-400 mt-0.5">
            {data?.is_itinerary_aware
              ? 'Ranked by multi-day itinerary location centrality to reduce estimated daily transit across all planned activities.'
              : 'Transparent room capacity, stay duration, and budget impact analysis with verified regional benchmarks.'}
          </p>
        </div>

        {/* Selected Lodging Summary Chip */}
        {selectedAccommodation && (
          <div className="flex items-center gap-3 p-2.5 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-2xl shrink-0">
            <div className="space-y-0.5">
              <div className="text-[11px] font-black text-emerald-900 dark:text-emerald-300 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>Selected: {selectedAccommodation.accommodation.name}</span>
              </div>
              <div className="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 font-mono">
                ₹{selectedAccommodation.total_cost.toLocaleString()} total ({selectedAccommodation.rooms_needed} room{selectedAccommodation.rooms_needed > 1 ? 's' : ''})
              </div>
            </div>
            <button
              type="button"
              onClick={() => onSelectAccommodation(null)}
              className="p-1 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 rounded-lg cursor-pointer"
              title="Remove selection"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Missing Required Constraints Notice */}
      {!hasRequiredConstraints && (
        <div className="py-10 px-4 text-center space-y-3 bg-slate-50/50 dark:bg-neutral-900/40 rounded-2xl border border-slate-200/80 dark:border-neutral-800">
          <div className="inline-flex p-3 bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 rounded-2xl border border-amber-200 dark:border-amber-900/60">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-800 dark:text-neutral-200">
            Trip Constraints Required for Lodging
          </h3>
          <p className="text-xs text-slate-500 dark:text-neutral-400 max-w-md mx-auto">
            Accurate accommodation recommendations and room capacity planning require confirmed trip dates and party size.
          </p>
        </div>
      )}

      {/* Filter Toolbar */}
      {hasRequiredConstraints && (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
            {/* Category Filter */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[11px] font-bold text-slate-500 dark:text-neutral-400 uppercase tracking-wider mr-1">
                Category:
              </span>
              {[
                { id: 'all', label: 'All Stays' },
                { id: 'ultra_luxury', label: 'Ultra-Luxury' },
                { id: 'ultra_budget', label: 'Ultra-Budget' },
                { id: 'moderate', label: 'Moderate / Mid-Range' },
              ].map((cat) => (
                <button
                  key={`cat-${cat.id}`}
                  type="button"
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`liquid-btn px-3 py-1.5 rounded-xl font-bold transition-all cursor-pointer ${
                    selectedCategory === cat.id
                      ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black font-extrabold shadow-sm'
                      : 'bg-slate-100 dark:bg-neutral-850 hover:bg-slate-200 dark:hover:bg-neutral-800 text-slate-700 dark:text-neutral-300 border border-slate-200 dark:border-neutral-800'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            {/* Type Filter */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[11px] font-bold text-slate-500 dark:text-neutral-400 uppercase tracking-wider mr-1">
                Type:
              </span>
              {['All', 'Resort', 'Hotel', 'Homestay', 'Hostel', 'Guesthouse'].map((t) => (
                <button
                  key={`type-${t}`}
                  type="button"
                  onClick={() => setSelectedType(t)}
                  className={`liquid-btn px-3 py-1.5 rounded-xl font-bold transition-all cursor-pointer ${
                    selectedType === t
                      ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black font-extrabold shadow-sm'
                      : 'bg-slate-100 dark:bg-neutral-850 hover:bg-slate-200 dark:hover:bg-neutral-800 text-slate-700 dark:text-neutral-300 border border-slate-200 dark:border-neutral-800'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Dataset Depth / Regional Availability Disclosure */}
          {data?.category_data_status && (
            <div className="p-3 bg-blue-50/70 dark:bg-blue-950/30 border border-blue-200/80 dark:border-blue-900/50 rounded-2xl flex items-start gap-2 text-xs text-blue-900 dark:text-blue-300">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-blue-600 dark:text-blue-400" />
              <div>
                <span className="font-bold">Data Provenance & Category Scope: </span>
                <span>{data.category_data_status}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Budget Breakdown Indicator */}
      {hasRequiredConstraints && data?.budget_context && (
        <div className="p-3.5 bg-slate-50 dark:bg-neutral-900/60 rounded-2xl border border-slate-200 dark:border-neutral-800 space-y-2.5 text-xs">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <span className="text-[10px] font-bold text-slate-400 dark:text-neutral-500 uppercase">
                Total Budget
              </span>
              <div className="text-sm font-black text-slate-900 dark:text-white font-mono mt-0.5">
                {totalBudget !== undefined ? `₹${totalBudget.toLocaleString()}` : 'Not Specified'}
              </div>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 dark:text-neutral-500 uppercase">
                Target Lodging ({data.budget_context.budget_tier})
              </span>
              <div className="text-sm font-black text-emerald-700 dark:text-emerald-400 font-mono mt-0.5">
                {data.budget_context.allocated_accommodation_budget !== null && data.budget_context.allocated_accommodation_budget !== undefined
                  ? `₹${data.budget_context.allocated_accommodation_budget.toLocaleString()}`
                  : 'Flexible'}
              </div>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 dark:text-neutral-500 uppercase">
                Required Rooms
              </span>
              <div className="text-sm font-black text-slate-800 dark:text-neutral-200 mt-0.5">
                {data.budget_context.rooms_needed} Room(s) ({partySize} guest{partySize && partySize > 1 ? 's' : ''})
              </div>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 dark:text-neutral-500 uppercase">
                Stay Duration
              </span>
              <div className="text-sm font-black text-slate-800 dark:text-neutral-200 mt-0.5">
                {data.nights} Night{data.nights > 1 ? 's' : ''} ({checkInDate} to {checkOutDate})
              </div>
            </div>
          </div>

          {/* Explicit Accounting Notice */}
          <div className="pt-2 border-t border-slate-200/60 dark:border-neutral-800/60 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500 dark:text-neutral-400">
            <div>
              <span className="font-semibold text-slate-700 dark:text-neutral-300">Accounted in remaining balance: </span>
              <span>Lodging{data.budget_context.intercity_transport_cost ? ` + Intercity Transit (₹${Math.round(data.budget_context.intercity_transport_cost).toLocaleString()})` : ''}</span>
            </div>
            <div className="text-amber-700 dark:text-amber-400 font-medium">
              ⚠️ Local transit, admissions & meals are excluded from this preliminary estimate.
            </div>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 rounded-2xl flex items-center gap-3 text-rose-700 dark:text-rose-300 text-xs">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="py-12 flex flex-col items-center justify-center gap-2">
          <Loader2 className="w-6 h-6 animate-spin text-emerald-600 dark:text-emerald-400" />
          <span className="text-xs font-semibold text-slate-500 dark:text-neutral-400">
            Calculating optimal accommodation options & capacity...
          </span>
        </div>
      )}

      {/* Recommendations Cards Grid */}
      {hasRequiredConstraints && !loading && data && data.recommendations.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.recommendations.map((item) => (
            <AccommodationCard
              key={item.accommodation.id}
              item={item}
              isSelected={selectedAccommodation?.accommodation.id === item.accommodation.id}
              onSelect={handleSelect}
              totalBudget={totalBudget}
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {hasRequiredConstraints && !loading && data && data.recommendations.length === 0 && (
        <div className="py-8 text-center text-xs text-slate-500 dark:text-neutral-400 space-y-2">
          <p>
            No accommodations found matching the{' '}
            <strong className="text-slate-700 dark:text-neutral-200">
              {selectedCategory === 'ultra_luxury'
                ? 'Ultra-Luxury'
                : selectedCategory === 'ultra_budget'
                ? 'Ultra-Budget'
                : selectedCategory === 'moderate'
                ? 'Moderate / Mid-Range'
                : 'selected'}
            </strong>{' '}
            category.
          </p>
          {data.category_data_status && (
            <p className="text-blue-700 dark:text-blue-300 max-w-md mx-auto font-medium">
              {data.category_data_status}
            </p>
          )}
          <button
            type="button"
            onClick={() => {
              setSelectedCategory('all');
              setSelectedType('All');
            }}
            className="text-emerald-600 dark:text-emerald-400 font-bold hover:underline cursor-pointer"
          >
            Reset Filters
          </button>
        </div>
      )}
    </div>
  );
};
