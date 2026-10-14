import React from 'react';
import { OptimizedDaySchedule } from '../../types';
import {
  Clock,
  MapPin,
  DollarSign,
  Car,
  Navigation,
  CheckCircle2,
  AlertTriangle,
  ArrowDown,
  Hotel,
} from 'lucide-react';

interface DayScheduleCardProps {
  day: OptimizedDaySchedule;
}

export const DayScheduleCard: React.FC<DayScheduleCardProps> = ({ day }) => {
  return (
    <div className="liquid-glass rounded-3xl p-6 shadow-sm border border-slate-200 dark:border-neutral-800">
      {/* Day Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-slate-100 dark:border-neutral-800">
        <div className="flex items-center gap-3">
          <span className="flex items-center justify-center w-10 h-10 rounded-xl bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black font-extrabold text-base shadow-md shadow-emerald-600/20">
            {day.day_number}
          </span>
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Day {day.day_number} Sightseeing
            </h3>
            <p className="text-xs text-slate-500 dark:text-neutral-400 flex items-center gap-2">
              <span>{day.day_start_time} - {day.day_end_time}</span>
              <span>&bull;</span>
              <span className="capitalize text-emerald-700 dark:text-emerald-400 font-medium">{day.recommended_transport} Transport</span>
            </p>
          </div>
        </div>

        {/* Badges */}
        <div className="flex flex-wrap items-center gap-2">
          {day.start_location_type === 'accommodation' && day.start_location_name && (
            <span className="liquid-btn px-3 py-1 bg-amber-50 dark:bg-amber-950/60 border border-amber-200 dark:border-amber-800/80 text-amber-700 dark:text-amber-300 text-xs font-semibold rounded-full flex items-center gap-1.5">
              <Hotel className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
              <span>Base: {day.start_location_name}</span>
            </span>
          )}
          <span className="liquid-btn px-3 py-1 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800/80 text-emerald-700 dark:text-emerald-300 text-xs font-semibold rounded-full flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            {day.feasibility_status === 'FEASIBLE' ? '100% Feasible' : 'Feasible (Pruned)'}
          </span>
          <span className="liquid-btn px-3 py-1 bg-slate-100 dark:bg-neutral-900 text-slate-700 dark:text-neutral-300 text-xs font-semibold rounded-full border border-transparent dark:border-neutral-800">
            {day.attraction_count} Stops
          </span>
          <span
            className="liquid-btn px-3 py-1 bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800/80 text-amber-700 dark:text-amber-300 text-xs font-semibold rounded-full"
            title={`Estimated day sightseeing & local transit cost (includes attraction admission fees of ₹${day.day_estimated_admission_cost} and local transit of ₹${day.day_estimated_transit_cost})`}
          >
            Day Sightseeing & Transit: ₹{day.day_total_estimated_cost}
          </span>
        </div>
      </div>

      {/* Metrics Summary Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-4 text-center border-b border-slate-100 dark:border-neutral-800 text-xs">
        <div
          className="liquid-btn bg-slate-50 dark:bg-neutral-900/70 p-2.5 rounded-xl border border-slate-100 dark:border-neutral-800"
          title="Estimated road distance: calculated from straight-line geographic distance using a 1.30 detour factor. Actual road distances and travel times may differ."
        >
          <span className="text-slate-400 dark:text-neutral-500 block mb-0.5">Est. Distance</span>
          <span className="font-bold text-slate-800 dark:text-neutral-100">{day.total_travel_distance_km} km</span>
        </div>
        <div className="liquid-btn bg-slate-50 dark:bg-neutral-900/70 p-2.5 rounded-xl border border-slate-100 dark:border-neutral-800">
          <span className="text-slate-400 dark:text-neutral-500 block mb-0.5">Travel Time</span>
          <span className="font-bold text-slate-800 dark:text-neutral-100">{day.total_travel_duration_hours} hrs</span>
        </div>
        <div className="liquid-btn bg-slate-50 dark:bg-neutral-900/70 p-2.5 rounded-xl border border-slate-100 dark:border-neutral-800">
          <span className="text-slate-400 dark:text-neutral-500 block mb-0.5">Sightseeing</span>
          <span className="font-bold text-slate-800 dark:text-neutral-100">{day.total_sightseeing_duration_hours} hrs</span>
        </div>
        <div className="liquid-btn bg-slate-50 dark:bg-neutral-900/70 p-2.5 rounded-xl border border-slate-100 dark:border-neutral-800">
          <span className="text-slate-400 dark:text-neutral-500 block mb-0.5">Optimization</span>
          <span className="font-bold text-emerald-600 dark:text-emerald-400">
            -{day.optimization_metrics.distance_reduction_pct}% km
          </span>
        </div>
      </div>

      {/* Timeline Waypoints */}
      <div className="mt-6 space-y-4">
        {/* Accommodation Departure Banner */}
        {day.accommodation_origin_leg && (
          <div className="p-3.5 rounded-2xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200/80 dark:border-amber-800/50 flex items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2.5">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-300 font-bold shrink-0">
                🏨
              </span>
              <div>
                <span className="font-bold text-slate-900 dark:text-white">
                  Depart from {day.accommodation_origin_leg.from_attraction_name}
                </span>
                <span className="block text-slate-500 dark:text-neutral-400 text-[11px]">
                  Daily Tour Origin &bull; {day.day_start_time}
                </span>
              </div>
            </div>
            <div className="text-right shrink-0">
              <span className="font-semibold text-slate-700 dark:text-neutral-300">
                {day.accommodation_origin_leg.distance_km} km ({Math.round(day.accommodation_origin_leg.travel_time_hours * 60)} min)
              </span>
              <span className="block text-[11px] text-amber-700 dark:text-amber-400 font-medium">
                ₹{day.accommodation_origin_leg.estimated_transit_cost}
              </span>
            </div>
          </div>
        )}

        {day.items.map((item, idx) => {
          // If accommodation leg exists, legs[0] is origin leg, so legs between item 0 and item 1 is legs[1]
          const leg = day.accommodation_origin_leg
            ? day.legs.find(
                (l) =>
                  l.leg_type === 'attraction_to_attraction' &&
                  idx > 0 &&
                  l.from_attraction_id === day.items[idx - 1].attraction.id &&
                  l.to_attraction_id === item.attraction.id
              )
            : idx > 0
            ? day.legs[idx - 1]
            : null;

          return (
            <React.Fragment key={`item-${item.attraction.id}-${item.visit_order}`}>
              {/* Transit Connector */}
              {leg && (
                <div className="ml-5 pl-6 border-l-2 border-dashed border-emerald-200 dark:border-emerald-800/80 py-2 my-1">
                  <div className="liquid-btn flex items-center gap-2 text-xs text-slate-500 dark:text-neutral-400 bg-slate-50 dark:bg-neutral-900/90 border border-slate-100 dark:border-neutral-800 p-2 rounded-lg inline-flex">
                    <Car className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                    <span className="font-medium">
                      {leg.distance_km} km ({Math.round(leg.travel_time_hours * 60)} min) via {leg.transport_mode}
                    </span>
                    <span>&bull;</span>
                    <span className="text-slate-700 dark:text-neutral-200 font-semibold">₹{leg.estimated_transit_cost}</span>
                  </div>
                </div>
              )}

              {/* Waypoint Card */}
              <div className="liquid-card flex items-start gap-4 p-4 rounded-2xl border border-slate-200 dark:border-neutral-800">
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 font-extrabold text-sm shrink-0 mt-0.5 border border-emerald-200 dark:border-emerald-800/60">
                  {item.visit_order}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white truncate">
                      {item.attraction.name}
                    </h4>
                    <span className="text-xs px-2.5 py-0.5 bg-slate-100 dark:bg-neutral-900 text-slate-600 dark:text-neutral-300 rounded-full capitalize border border-transparent dark:border-neutral-800">
                      {item.attraction.category}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-slate-500 dark:text-neutral-400 mt-2">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                      <strong className="text-slate-700 dark:text-neutral-200">
                        {item.arrival_time} - {item.departure_time}
                      </strong>{' '}
                      ({item.visit_duration_hours}h)
                    </span>

                    <span
                      className="flex items-center gap-1"
                      title={
                        item.admission_fee_status === 'unknown'
                          ? 'Admission fee unverified / not officially published'
                          : item.item_admission_fee && item.item_admission_fee > 0
                          ? 'Included in estimated sightseeing cost'
                          : 'Free admission; included in estimated sightseeing cost'
                      }
                    >
                      <DollarSign className="w-3.5 h-3.5 text-slate-400 dark:text-neutral-500" />
                      {item.admission_fee_status === 'unknown' || item.item_admission_fee === null || item.item_admission_fee === undefined ? (
                        <span className="text-amber-600 dark:text-amber-400 font-medium">Fee Unverified</span>
                      ) : item.item_admission_fee > 0 ? (
                        <span>
                          Entry: ₹{item.item_admission_fee}/person
                          {item.item_group_admission_fee && item.item_group_admission_fee > item.item_admission_fee ? (
                            <span className="text-slate-400 dark:text-neutral-500 ml-1">
                              (₹{item.item_group_admission_fee} group)
                            </span>
                          ) : null}
                          {item.is_fee_verified && (
                            <span className="ml-1 text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold" title="Verified Fee">✓</span>
                          )}
                          <span className="ml-1 text-[10px] text-slate-400 dark:text-neutral-500">(in sightseeing cost)</span>
                        </span>
                      ) : (
                        <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                          Entry: Free
                          {item.is_fee_verified && (
                            <span className="ml-1 text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold" title="Verified Free Entry">✓</span>
                          )}
                        </span>
                      )}
                    </span>

                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                      Crowd: {item.crowd_level}
                    </span>
                  </div>

                  {item.visit_notes && (
                    <p className="text-xs text-slate-500 dark:text-neutral-400 italic mt-2 bg-slate-50 dark:bg-neutral-900/80 p-2 rounded-lg border border-transparent dark:border-neutral-800/80">
                      {item.visit_notes}
                    </p>
                  )}
                </div>
              </div>
            </React.Fragment>
          );
        })}

        {/* Accommodation Return Banner */}
        {day.accommodation_return_leg && (
          <div className="p-3.5 rounded-2xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200/80 dark:border-amber-800/50 flex items-center justify-between gap-3 text-xs mt-3">
            <div className="flex items-center gap-2.5">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-300 font-bold shrink-0">
                🏨
              </span>
              <div>
                <span className="font-bold text-slate-900 dark:text-white">
                  Return to {day.accommodation_return_leg.to_attraction_name}
                </span>
                <span className="block text-slate-500 dark:text-neutral-400 text-[11px]">
                  Daily Tour Return &bull; {day.day_end_time}
                </span>
              </div>
            </div>
            <div className="text-right shrink-0">
              <span className="font-semibold text-slate-700 dark:text-neutral-300">
                {day.accommodation_return_leg.distance_km} km ({Math.round(day.accommodation_return_leg.travel_time_hours * 60)} min)
              </span>
              <span className="block text-[11px] text-amber-700 dark:text-amber-400 font-medium">
                ₹{day.accommodation_return_leg.estimated_transit_cost}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
