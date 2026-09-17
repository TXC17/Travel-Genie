import React, { useState } from 'react';
import { DeferredAttraction } from '../../types';
import { AlertTriangle, ChevronDown, ChevronUp, ShieldAlert } from 'lucide-react';

interface DeferredAttractionsCardProps {
  deferredAttractions: DeferredAttraction[];
}

export const DeferredAttractionsCard: React.FC<DeferredAttractionsCardProps> = ({
  deferredAttractions,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!deferredAttractions || deferredAttractions.length === 0) return null;

  return (
    <div className="bg-amber-50/70 border border-amber-200 rounded-2xl p-5 mb-6">
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between cursor-pointer"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-amber-900">
              {deferredAttractions.length} Stops Deferred (Schedule Feasibility Protection)
            </h4>
            <p className="text-xs text-amber-700">
              The optimizer automatically deferred lower-priority stops to prevent pace overload or closing-hour violations.
            </p>
          </div>
        </div>

        <button className="text-amber-800 hover:text-amber-950 p-1">
          {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      {isOpen && (
        <div className="mt-4 pt-4 border-t border-amber-200/60 space-y-2.5">
          {deferredAttractions.map((item) => (
            <div
              key={`deferred-${item.attraction_id}`}
              className="bg-white/80 p-3 rounded-xl border border-amber-100 flex items-start gap-3 text-xs"
            >
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900">{item.attraction_name}</span>
                  <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded font-semibold text-[10px] uppercase">
                    {item.violating_constraint.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-slate-600 mt-1">{item.reason}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
