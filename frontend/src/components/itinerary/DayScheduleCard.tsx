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
} from 'lucide-react';

interface DayScheduleCardProps {
  day: OptimizedDaySchedule;
}

export const DayScheduleCard: React.FC<DayScheduleCardProps> = ({ day }) => {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
      {/* Day Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <span className="flex items-center justify-center w-10 h-10 rounded-xl bg-teal-600 text-white font-bold text-base shadow-md shadow-teal-600/20">
            {day.day_number}
          </span>
          <div>
            <h3 className="text-lg font-bold text-slate-900">
              Day {day.day_number} Sightseeing
            </h3>
            <p className="text-xs text-slate-500 flex items-center gap-2">
              <span>{day.day_start_time} - {day.day_end_time}</span>
              <span>&bull;</span>
              <span className="capitalize">{day.recommended_transport} Transport</span>
            </p>
          </div>
        </div>

        {/* Badges */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="px-3 py-1 bg-teal-50 border border-teal-200 text-teal-700 text-xs font-semibold rounded-full flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            {day.feasibility_status === 'FEASIBLE' ? '100% Feasible' : 'Feasible (Pruned)'}
          </span>
          <span className="px-3 py-1 bg-slate-100 text-slate-700 text-xs font-semibold rounded-full">
            {day.attraction_count} Stops
          </span>
          <span className="px-3 py-1 bg-amber-50 border border-amber-200 text-amber-700 text-xs font-semibold rounded-full">
            Est. Cost: ₹{day.day_total_estimated_cost}
          </span>
        </div>
      </div>

      {/* Metrics Summary Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-4 text-center border-b border-slate-100 text-xs">
        <div className="bg-slate-50 p-2.5 rounded-xl">
          <span className="text-slate-400 block mb-0.5">Total Distance</span>
          <span className="font-bold text-slate-800">{day.total_travel_distance_km} km</span>
        </div>
        <div className="bg-slate-50 p-2.5 rounded-xl">
          <span className="text-slate-400 block mb-0.5">Travel Time</span>
          <span className="font-bold text-slate-800">{day.total_travel_duration_hours} hrs</span>
        </div>
        <div className="bg-slate-50 p-2.5 rounded-xl">
          <span className="text-slate-400 block mb-0.5">Sightseeing</span>
          <span className="font-bold text-slate-800">{day.total_sightseeing_duration_hours} hrs</span>
        </div>
        <div className="bg-slate-50 p-2.5 rounded-xl">
          <span className="text-slate-400 block mb-0.5">Optimization</span>
          <span className="font-bold text-teal-600">
            -{day.optimization_metrics.distance_reduction_pct}% km
          </span>
        </div>
      </div>

      {/* Timeline Waypoints */}
      <div className="mt-6 space-y-4">
        {day.items.map((item, idx) => {
          const leg = idx > 0 ? day.legs[idx - 1] : null;

          return (
            <React.Fragment key={`item-${item.attraction.id}-${item.visit_order}`}>
              {/* Transit Connector */}
              {leg && (
                <div className="ml-5 pl-6 border-l-2 border-dashed border-teal-200 py-2 my-1">
                  <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 p-2 rounded-lg inline-flex">
                    <Car className="w-3.5 h-3.5 text-teal-600" />
                    <span className="font-medium">
                      {leg.distance_km} km ({Math.round(leg.travel_time_hours * 60)} min) via {leg.transport_mode}
                    </span>
                    <span>&bull;</span>
                    <span className="text-slate-700 font-semibold">₹{leg.estimated_transit_cost}</span>
                  </div>
                </div>
              )}

              {/* Waypoint Card */}
              <div className="flex items-start gap-4 p-4 rounded-xl border border-slate-100 hover:border-teal-200 hover:bg-teal-50/20 transition-all">
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-teal-100 text-teal-700 font-bold text-sm shrink-0 mt-0.5">
                  {item.visit_order}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
                    <h4 className="text-sm font-bold text-slate-900 truncate">
                      {item.attraction.name}
                    </h4>
                    <span className="text-xs px-2.5 py-0.5 bg-slate-100 text-slate-600 rounded-full capitalize">
                      {item.attraction.category}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-slate-500 mt-2">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-teal-600" />
                      <strong className="text-slate-700">
                        {item.arrival_time} - {item.departure_time}
                      </strong>{' '}
                      ({item.visit_duration_hours}h)
                    </span>

                    <span className="flex items-center gap-1">
                      <DollarSign className="w-3.5 h-3.5 text-slate-400" />
                      {item.item_admission_fee > 0 ? (
                        <span>Entry: ₹{item.item_admission_fee}</span>
                      ) : (
                        <span className="text-teal-600 font-medium">Free Entry</span>
                      )}
                    </span>

                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                      Crowd: {item.crowd_level}
                    </span>
                  </div>

                  {item.visit_notes && (
                    <p className="text-xs text-slate-500 italic mt-2 bg-slate-50 p-2 rounded-lg">
                      {item.visit_notes}
                    </p>
                  )}
                </div>
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
