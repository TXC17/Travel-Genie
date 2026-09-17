import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export const ThemeToggle: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { theme, toggleTheme, isDark } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      className={`liquid-btn group relative flex items-center gap-2 p-1.5 rounded-full border transition-all cursor-pointer select-none ${
        isDark
          ? 'bg-black border-emerald-500/50 text-emerald-400 hover:border-emerald-400 shadow-lg shadow-emerald-950/40'
          : 'bg-amber-50/90 border-amber-300 text-amber-900 hover:border-amber-400 shadow-sm'
      } ${className}`}
    >
      {/* Sliding Track Pill */}
      <div className="flex items-center gap-1.5 px-1">
        {/* Sun Icon */}
        <div
          className={`flex items-center justify-center w-6 h-6 rounded-full transition-all duration-300 ${
            !isDark
              ? 'bg-gradient-to-tr from-amber-500 to-yellow-400 text-slate-950 shadow-md scale-110 rotate-0'
              : 'text-neutral-500 hover:text-amber-400 scale-90'
          }`}
        >
          <Sun className="w-3.5 h-3.5" />
        </div>

        {/* Moon Icon */}
        <div
          className={`flex items-center justify-center w-6 h-6 rounded-full transition-all duration-300 ${
            isDark
              ? 'bg-gradient-to-tr from-emerald-500 to-amber-400 text-black shadow-md shadow-emerald-500/30 scale-110 rotate-0'
              : 'text-slate-400 hover:text-emerald-600 scale-90'
          }`}
        >
          <Moon className="w-3.5 h-3.5 font-bold" />
        </div>
      </div>

      {/* Mode Tag Label */}
      <span
        className={`text-[11px] font-extrabold uppercase tracking-wider pr-2 hidden sm:inline-block transition-colors ${
          isDark ? 'text-emerald-400 group-hover:text-emerald-300' : 'text-amber-900 group-hover:text-amber-950'
        }`}
      >
        {isDark ? 'Dark' : 'Light'}
      </span>
    </button>
  );
};
