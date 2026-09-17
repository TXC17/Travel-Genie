import React from 'react';
import { ReplanningDiff } from '../../types';
import { RefreshCw, ArrowRight, MinusCircle, PlusCircle, Shuffle, TrendingDown } from 'lucide-react';

interface ReplanningDiffViewProps {
  diff: ReplanningDiff;
}

export const ReplanningDiffView: React.FC<ReplanningDiffViewProps> = ({ diff }) => {
  if (!diff || !diff.is_replanned) return null;

  return (
    <div className="bg-slate-900 text-white rounded-xl p-4 my-3 border border-teal-500/30 text-xs">
      <div className="flex items-center gap-2 text-teal-400 font-bold mb-3">
        <RefreshCw className="w-4 h-4 animate-spin-slow" />
        <span className="uppercase tracking-wider">Smart Replanning Audit Diff</span>
      </div>

      {/* Changed Constraints */}
      {diff.changed_constraints.length > 0 && (
        <div className="space-y-1.5 mb-3 bg-white/5 p-2.5 rounded-lg">
          <span className="text-slate-400 font-semibold block text-[11px]">Constraint Adjustments:</span>
          {diff.changed_constraints.map((c, i) => (
            <div key={`diff-c-${i}`} className="flex items-center gap-2 text-slate-200">
              <span className="capitalize font-medium text-teal-300">{c.field.replace('_', ' ')}:</span>
              <span className="text-rose-400 line-through">{String(c.old_value)}</span>
              <ArrowRight className="w-3 h-3 text-slate-400" />
              <span className="text-emerald-400 font-bold">{String(c.new_value)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Removed Attractions */}
      {diff.removed_attractions.length > 0 && (
        <div className="space-y-1 mb-2.5">
          <span className="text-rose-400 font-semibold flex items-center gap-1">
            <MinusCircle className="w-3.5 h-3.5" /> Removed Stops ({diff.removed_attractions.length}):
          </span>
          {diff.removed_attractions.map((r, i) => (
            <p key={`rem-${i}`} className="text-slate-300 pl-4 text-[11px]">
              &bull; <strong className="text-white">{r.name}</strong> - {r.reason}
            </p>
          ))}
        </div>
      )}

      {/* Moved Attractions */}
      {diff.moved_attractions.length > 0 && (
        <div className="space-y-1 mb-2.5">
          <span className="text-amber-400 font-semibold flex items-center gap-1">
            <Shuffle className="w-3.5 h-3.5" /> Re-Clustered Stops:
          </span>
          {diff.moved_attractions.map((m, i) => (
            <p key={`mov-${i}`} className="text-slate-300 pl-4 text-[11px]">
              &bull; <strong className="text-white">{m.name}</strong> (Day {m.from_day} &rarr; Day {m.to_day})
            </p>
          ))}
        </div>
      )}

      {/* Metric Delta Summary */}
      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-white/10 text-center font-mono">
        <div className="bg-white/5 p-1.5 rounded">
          <span className="text-[10px] text-slate-400 block">&Delta; Distance</span>
          <span className={diff.distance_change_km <= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400'}>
            {diff.distance_change_km > 0 ? `+${diff.distance_change_km}` : diff.distance_change_km} km
          </span>
        </div>
        <div className="bg-white/5 p-1.5 rounded">
          <span className="text-[10px] text-slate-400 block">&Delta; Time</span>
          <span className={diff.travel_time_change_hours <= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400'}>
            {diff.travel_time_change_hours > 0 ? `+${diff.travel_time_change_hours}` : diff.travel_time_change_hours}h
          </span>
        </div>
        <div className="bg-white/5 p-1.5 rounded">
          <span className="text-[10px] text-slate-400 block">&Delta; Budget</span>
          <span className={diff.budget_change <= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400'}>
            {diff.budget_change > 0 ? `+₹${diff.budget_change}` : `₹${diff.budget_change}`}
          </span>
        </div>
      </div>
    </div>
  );
};
