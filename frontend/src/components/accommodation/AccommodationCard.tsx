import React, { useState } from 'react';
import { AccommodationRecommendationItem } from '../../types';
import {
  Hotel,
  Home,
  Tent,
  Star,
  CheckCircle2,
  ShieldCheck,
  AlertTriangle,
  Info,
  DollarSign,
  Users,
  Calendar,
  ExternalLink,
  Phone,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface AccommodationCardProps {
  item: AccommodationRecommendationItem;
  isSelected: boolean;
  onSelect: (item: AccommodationRecommendationItem) => void;
  totalBudget?: number;
}

const TYPE_ICONS: Record<string, React.ReactNode> = {
  hotel: <Hotel className="w-3.5 h-3.5" />,
  resort: <Sparkles className="w-3.5 h-3.5" />,
  homestay: <Home className="w-3.5 h-3.5" />,
  hostel: <Users className="w-3.5 h-3.5" />,
  guesthouse: <Tent className="w-3.5 h-3.5" />,
};

export const AccommodationCard: React.FC<AccommodationCardProps> = ({
  item,
  isSelected,
  onSelect,
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const { accommodation, nights, rooms_needed, total_cost, is_within_budget, match_score } = item;

  const typeIcon = TYPE_ICONS[accommodation.accommodation_type.toLowerCase()] || <Hotel className="w-3.5 h-3.5" />;

  return (
    <div
      className={`liquid-card rounded-2xl border-2 transition-all p-4 sm:p-5 flex flex-col justify-between relative ${
        isSelected
          ? 'border-emerald-600 dark:border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/30 shadow-md ring-2 ring-emerald-500/20'
          : 'border-slate-200 dark:border-neutral-800 bg-white dark:bg-neutral-900/80 hover:border-emerald-300 dark:hover:border-emerald-500/60'
      }`}
    >
      <div className="space-y-3.5">
        {/* Top Header: Image / Type / Badges */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-wrap">
            {/* Type badge */}
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-slate-100 dark:bg-neutral-800 text-slate-700 dark:text-neutral-300 border border-slate-200 dark:border-neutral-700">
              {typeIcon}
              <span>{accommodation.accommodation_type}</span>
            </span>

            {/* Rating */}
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-extrabold bg-amber-50 dark:bg-amber-950/60 text-amber-900 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
              <Star className="w-3 h-3 fill-amber-400 text-amber-500" />
              <span>{accommodation.rating.toFixed(1)}</span>
            </span>

            {/* Provenance Badge */}
            {item.provenance_badge === 'VERIFIED' ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-extrabold bg-emerald-100 dark:bg-emerald-950/70 text-emerald-900 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>Verified Benchmark</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-extrabold bg-amber-100 dark:bg-amber-950/70 text-amber-900 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                <Info className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
                <span>Estimated</span>
              </span>
            )}

            {/* Match Score Badge */}
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-extrabold bg-emerald-700 dark:bg-emerald-500 text-white dark:text-black shadow-xs">
              <Sparkles className="w-3 h-3" />
              <span>{Math.round(match_score * 100)}% Match</span>
            </span>
          </div>

          {/* Pricing Highlight */}
          <div className="text-left sm:text-right shrink-0">
            <div className="text-base sm:text-lg font-black text-slate-900 dark:text-white">
              ₹{total_cost.toLocaleString()}
            </div>
            <div className="text-[11px] font-semibold text-slate-500 dark:text-neutral-400">
              ₹{accommodation.price_per_night.toLocaleString()} / night &bull; {rooms_needed} room{rooms_needed > 1 ? 's' : ''}
            </div>
          </div>
        </div>

        {/* Accommodation Name & Description */}
        <div>
          <h3 className="text-base sm:text-lg font-black text-slate-900 dark:text-white tracking-tight">
            {accommodation.name}
          </h3>
          <p className="text-xs text-slate-600 dark:text-neutral-300 font-medium line-clamp-2 mt-1">
            {accommodation.description}
          </p>
        </div>

        {/* Stay & Room Capacity Metrics Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-xs">
          <div className="p-2 rounded-xl bg-slate-50 dark:bg-neutral-850 border border-slate-100 dark:border-neutral-800 flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 dark:text-neutral-500 uppercase flex items-center gap-1">
              <Calendar className="w-3 h-3" /> Duration
            </span>
            <span className="font-extrabold text-slate-800 dark:text-neutral-200 mt-0.5">
              {nights} Night{nights > 1 ? 's' : ''}
            </span>
          </div>

          <div className="p-2 rounded-xl bg-slate-50 dark:bg-neutral-850 border border-slate-100 dark:border-neutral-800 flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 dark:text-neutral-500 uppercase flex items-center gap-1">
              <Users className="w-3 h-3" /> Capacity
            </span>
            <span className="font-extrabold text-slate-800 dark:text-neutral-200 mt-0.5">
              {rooms_needed} Room{rooms_needed > 1 ? 's' : ''} ({accommodation.room_capacity}/rm)
            </span>
          </div>

          <div className="p-2 rounded-xl bg-slate-50 dark:bg-neutral-850 border border-slate-100 dark:border-neutral-800 flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 dark:text-neutral-500 uppercase flex items-center gap-1">
              <DollarSign className="w-3 h-3" /> Budget Fit
            </span>
            <span
              className={`font-extrabold mt-0.5 ${
                is_within_budget
                  ? 'text-emerald-700 dark:text-emerald-400'
                  : 'text-amber-700 dark:text-amber-400'
              }`}
            >
              {is_within_budget ? 'Within Budget' : 'Exceeds Target'}
            </span>
          </div>

          <div className="p-2 rounded-xl bg-slate-50 dark:bg-neutral-850 border border-slate-100 dark:border-neutral-800 flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 dark:text-neutral-500 uppercase flex items-center gap-1">
              💰 Remaining
            </span>
            <span
              className={`font-extrabold mt-0.5 font-mono ${
                item.remaining_budget !== undefined
                  ? item.remaining_budget >= 0
                    ? 'text-emerald-700 dark:text-emerald-400'
                    : 'text-rose-600 dark:text-rose-400'
                  : 'text-slate-800 dark:text-neutral-200'
              }`}
            >
              {item.remaining_budget !== undefined
                ? item.remaining_budget >= 0
                  ? `₹${Math.round(item.remaining_budget).toLocaleString()} left`
                  : `-₹${Math.round(Math.abs(item.remaining_budget)).toLocaleString()} over`
                : 'N/A'}
            </span>
          </div>
        </div>

        {/* Amenities Chips */}
        {accommodation.amenities && accommodation.amenities.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {accommodation.amenities.slice(0, 5).map((amenity, i) => (
              <span
                key={`am-${i}`}
                className="px-2 py-0.5 bg-slate-100 dark:bg-neutral-800 text-slate-600 dark:text-neutral-300 rounded-lg text-[11px] font-semibold border border-slate-200 dark:border-neutral-700"
              >
                {amenity}
              </span>
            ))}
            {accommodation.amenities.length > 5 && (
              <span className="px-2 py-0.5 bg-slate-50 dark:bg-neutral-900 text-slate-400 dark:text-neutral-500 rounded-lg text-[10px] font-bold">
                +{accommodation.amenities.length - 5} more
              </span>
            )}
          </div>
        )}

        {/* Expandable Match Explanations & Provenance Notes */}
        {showDetails && (
          <div className="pt-3 border-t border-slate-200 dark:border-neutral-800 space-y-2 text-xs">
            <div className="text-[11px] font-bold text-slate-500 dark:text-neutral-400 uppercase tracking-wider">
              Deterministic Recommendation Reasons:
            </div>
            <ul className="space-y-1">
              {item.match_reasons.map((reason, idx) => (
                <li
                  key={`r-${idx}`}
                  className="flex items-start gap-1.5 text-slate-700 dark:text-neutral-300 font-medium"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                  <span>{reason}</span>
                </li>
              ))}
            </ul>

            {/* Direct Links and Booking Contact */}
            <div className="pt-2 flex flex-wrap items-center gap-3 text-[11px]">
              {accommodation.booking_url && (
                <a
                  href={accommodation.booking_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-emerald-700 dark:text-emerald-400 hover:underline font-bold"
                >
                  <ExternalLink className="w-3 h-3" />
                  <span>Official Booking Portal</span>
                </a>
              )}
              {accommodation.contact_phone && (
                <span className="inline-flex items-center gap-1 text-slate-500 dark:text-neutral-400 font-semibold">
                  <Phone className="w-3 h-3" />
                  <span>{accommodation.contact_phone}</span>
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Card Action Footer */}
      <div className="pt-4 border-t border-slate-100 dark:border-neutral-800 mt-3 flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={() => setShowDetails(!showDetails)}
          className="text-xs font-bold text-slate-500 dark:text-neutral-400 hover:text-emerald-700 dark:hover:text-emerald-400 flex items-center gap-1 cursor-pointer transition-colors"
        >
          <span>{showDetails ? 'Hide Details' : 'View Reasons & Sources'}</span>
          {showDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        <button
          type="button"
          onClick={() => onSelect(item)}
          className={`liquid-btn px-4 py-2 rounded-xl text-xs font-extrabold flex items-center gap-1.5 transition-all cursor-pointer ${
            isSelected
              ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black shadow-md'
              : 'bg-slate-100 dark:bg-neutral-800 hover:bg-emerald-50 dark:hover:bg-neutral-700 text-slate-700 dark:text-neutral-200 border border-slate-200 dark:border-neutral-700'
          }`}
        >
          {isSelected ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Selected</span>
            </>
          ) : (
            <span>Select Lodging</span>
          )}
        </button>
      </div>
    </div>
  );
};
