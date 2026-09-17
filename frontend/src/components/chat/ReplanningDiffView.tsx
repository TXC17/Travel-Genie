import React from 'react';
import { ReplanningDiff } from '../../types';
import { RefreshCw, ArrowRight, MinusCircle, PlusCircle, Shuffle, TrendingDown } from 'lucide-react';

interface ReplanningDiffViewProps {
  diff: ReplanningDiff;
}

export const ReplanningDiffView: React.FC<ReplanningDiffViewProps> = ({ diff }) => {
  if (!diff || !diff.is_replanned) return null;

  return (
    <div className="bg-slate-50 dark:bg-black text-slate-800 dark:text-white rounded-2xl p-4 my-3 border border-emerald-200 dark:border-emerald-500/40 shadow-sm text-xs">
      <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400 font-bold mb-3">
        <RefreshCw className="w-4 h-4 animate-spin-slow" />
        <span className="uppercase tracking-wider">Smart Replanning Audit Diff</span>
      </div>

      {/* Changed Constraints */}
      {diff.changed_constraints.length > 0 && (
        <div className="space-y-1.5 mb-3 bg-white dark:bg-neutral-900/80 p-2.5 rounded-xl border border-slate-200/80 dark:border-neutral-800">
          <span className="text-slate-500 dark:text-neutral-400 font-semibold block text-[11px]">Constraint Adjustments:</span>
          {diff.changed_constraints.map((c, i) => (
            <div key={`diff-c-${i}`} className="flex items-center gap-2 text-slate-700 dark:text-neutral-200">
              <span className="capitalize font-medium text-emerald-800 dark:text-emerald-300">{c.field.replace('_', ' ')}:</span>
              <span className="text-rose-600 dark:text-rose-400 line-through">{String(c.old_value)}</span>
              <ArrowRight className="w-3 h-3 text-slate-400 dark:text-neutral-500" />
              <span className="text-emerald-700 dark:text-emerald-400 font-bold">{String(c.new_value)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Removed Attractions */}
      {diff.removed_attractions.length > 0 && (
        <div className="space-y-1 mb-2.5">
          <span className="text-rose-600 dark:text-rose-400 font-semibold flex items-center gap-1">
            <MinusCircle className="w-3.5 h-3.5" /> Removed Stops ({diff.removed_attractions.length}):
          </span>
          {diff.removed_attractions.map((r, i) => (
            <p key={`rem-${i}`} className="text-slate-600 dark:text-neutral-300 pl-4 text-[11px]">
              &bull; <strong className="text-slate-900 dark:text-white">{r.name}</strong> - {r.reason}
            </p>
          ))}
        </div>
      )}

      {/* Moved Attractions */}
      {diff.moved_attractions.length > 0 && (
        <div className="space-y-1 mb-2.5">
          <span className="text-amber-600 dark:text-amber-400 font-semibold flex items-center gap-1">
            <Shuffle className="w-3.5 h-3.5" /> Re-Clustered Stops:
          </span>
          {diff.moved_attractions.map((m, i) => (
            <p key={`mov-${i}`} className="text-slate-600 dark:text-neutral-300 pl-4 text-[11px]">
              &bull; <strong className="text-slate-900 dark:text-white">{m.name}</strong> (Day {m.from_day} &rarr; Day {m.to_day})
            </p>
          ))}
        </div>
      )}

      {/* Metric Delta Summary */}
      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-200 dark:border-neutral-800 text-center font-mono">
        <div className="bg-white dark:bg-neutral-900/80 p-2 rounded-xl border border-slate-200/80 dark:border-neutral-800">
          <span className="text-[10px] text-slate-500 dark:text-neutral-400 block">&Delta; Distance</span>
          <span className={diff.distance_change_km <= 0 ? 'text-emerald-700 dark:text-emerald-400 font-bold' : 'text-rose-600 dark:text-rose-400'}>
            {diff.distance_change_km > 0 ? `+${diff.distance_change_km}` : diff.distance_change_km} km
          </span>
        </div>
        <div className="bg-white dark:bg-neutral-900/80 p-2 rounded-xl border border-slate-200/80 dark:border-neutral-800">
          <span className="text-[10px] text-slate-500 dark:text-neutral-400 block">&Delta; Time</span>
          <span className={diff.travel_time_change_hours <= 0 ? 'text-emerald-700 dark:text-emerald-400 font-bold' : 'text-rose-600 dark:text-rose-400'}>
            {diff.travel_time_change_hours > 0 ? `+${diff.travel_time_change_hours}` : diff.travel_time_change_hours}h
          </span>
        </div>
        <div className="bg-white dark:bg-neutral-900/80 p-2 rounded-xl border border-slate-200/80 dark:border-neutral-800">
          <span className="text-[10px] text-slate-500 dark:text-neutral-400 block">&Delta; Budget</span>
          <span className={diff.budget_change <= 0 ? 'text-emerald-700 dark:text-emerald-400 font-bold' : 'text-rose-600 dark:text-rose-400'}>
            {diff.budget_change > 0 ? `+₹${diff.budget_change}` : `₹${diff.budget_change}`}
          </span>
        </div>
      </div>
    </div>
  );
};
