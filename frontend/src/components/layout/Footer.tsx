import React from 'react';
import { Sparkles, GraduationCap, Cpu, Layers } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-400 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand & Project Info */}
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center space-x-2 text-white font-bold text-lg">
              <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white">
                <Sparkles className="w-4 h-4" />
              </div>
              <span>Travel Genie</span>
            </div>
            <p className="text-sm text-slate-400 max-w-md">
              An AI-Driven System for Optimized Travel Itinerary Generation. Final-Year Academic Major Project for Artificial Intelligence & Data Science.
            </p>
            <div className="flex items-center gap-2 text-xs text-brand-400 font-mono">
              <GraduationCap className="w-4 h-4" />
              <span>Bachelor of Engineering — AI & Data Science</span>
            </div>
          </div>

          {/* Academic Algorithms */}
          <div className="space-y-3">
            <h4 className="text-white text-sm font-semibold uppercase tracking-wider flex items-center gap-1.5">
              <Cpu className="w-4 h-4 text-brand-400" />
              Algorithms
            </h4>
            <ul className="space-y-2 text-xs">
              <li className="hover:text-white transition-colors">MCDM Recommender Scoring</li>
              <li className="hover:text-white transition-colors">Geographic K-Means Spatial Clustering</li>
              <li className="hover:text-white transition-colors">Google OR-Tools TSP Optimization</li>
              <li className="hover:text-white transition-colors">Heuristic Temporal & Budget Pruner</li>
            </ul>
          </div>

          {/* Curated Scope */}
          <div className="space-y-3">
            <h4 className="text-white text-sm font-semibold uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-brand-400" />
              Curated Scope
            </h4>
            <ul className="space-y-2 text-xs">
              <li>Dandeli (Eco-Adventure)</li>
              <li>Coorg (Nature & Coffee)</li>
              <li>Hampi (UNESCO Heritage)</li>
              <li>Goa (Coastal & Heritage)</li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500">
          <p>© 2026 Travel Genie Academic Project. Deterministic Algorithms & Neuro-Symbolic AI.</p>
          <p className="mt-2 sm:mt-0 font-mono">Leaflet & OpenStreetMap Powered</p>
        </div>
      </div>
    </footer>
  );
};
