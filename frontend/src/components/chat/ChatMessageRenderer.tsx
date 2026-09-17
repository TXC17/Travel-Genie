import React from 'react';
import {
  MapPin,
  Calendar,
  Clock,
  Car,
  Ticket,
  AlertTriangle,
  Sparkles,
  TrendingDown,
  DollarSign,
  CheckCircle2,
  Compass,
} from 'lucide-react';

interface ChatMessageRendererProps {
  content: string;
  isUser: boolean;
  onSuggestionClick?: (text: string) => void;
}

export const ChatMessageRenderer: React.FC<ChatMessageRendererProps> = ({
  content,
  isUser,
  onSuggestionClick,
}) => {
  if (isUser) {
    return <div className="font-medium">{content}</div>;
  }

  // Check if this is an itinerary explanation message
  const isItinerary =
    content.includes('DAY 1') ||
    content.includes('Day 1') ||
    content.includes('OPTIMIZED ITINERARY') ||
    content.includes('Planned Activities') ||
    content.includes('Sightseeing Visits');

  if (!isItinerary) {
    // Regular conversational response
    return (
      <div className="space-y-3">
        <div className="leading-relaxed whitespace-pre-line text-slate-800 dark:text-neutral-200">
          {renderFormattedText(content)}
        </div>

        {/* Quick action chips if it's a greeting or destination question */}
        {(content.includes('Hampi, Coorg, Dandeli, or Goa') || content.includes('Welcome to Travel Genie')) &&
          onSuggestionClick && (
            <div className="pt-2 flex flex-wrap gap-2">
              {[
                '🌴 Plan 3 days in Goa',
                '🏛️ 3-day Hampi trip with auto',
                '☕ 2 days in Coorg with nature',
                '🛶 2 days in Dandeli adventure',
              ].map((chip, idx) => (
                <button
                  key={idx}
                  onClick={() => onSuggestionClick(chip.replace(/^[^\w]+/, ''))}
                  className="px-3 py-1.5 bg-emerald-50 dark:bg-emerald-950/60 hover:bg-emerald-100 dark:hover:bg-emerald-900/80 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/80 rounded-full text-xs font-semibold transition-all hover:scale-105 cursor-pointer flex items-center gap-1.5 shadow-sm"
                >
                  <Compass className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                  <span>{chip}</span>
                </button>
              ))}
            </div>
          )}
      </div>
    );
  }

  // Parse structured itinerary message into visual sections
  const sections = parseItineraryContent(content);

  return (
    <div className="space-y-4 text-slate-800 dark:text-neutral-200">
      {/* Replanning Banner if present */}
      {sections.replanning && (
        <div className="p-3.5 bg-amber-50/80 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 rounded-2xl text-xs space-y-1.5 shadow-sm">
          <div className="flex items-center gap-2 font-bold text-amber-900 dark:text-amber-300">
            <Sparkles className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            <span>Smart Replanning Updates</span>
          </div>
          <div className="text-amber-800 dark:text-amber-200 whitespace-pre-line pl-6 leading-relaxed">
            {renderFormattedText(sections.replanning)}
          </div>
        </div>
      )}

      {/* Header Summary Card */}
      {sections.header && (
        <div className="p-4 bg-gradient-to-br from-emerald-800 via-emerald-950 to-slate-900 dark:from-neutral-900 dark:via-neutral-950 dark:to-black text-white rounded-2xl shadow-md space-y-3 border border-emerald-700/40 dark:border-neutral-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-xl border border-emerald-500/30">
              <MapPin className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h3 className="font-extrabold text-sm md:text-base tracking-wide text-white">
                {sections.title || 'Optimized Trip Itinerary'}
              </h3>
              <p className="text-[11px] text-emerald-300 font-medium">
                Deterministic Multi-Day Route Optimization (OR-Tools)
              </p>
            </div>
          </div>

          {/* Quick Metrics Pills */}
          {sections.stats.length > 0 && (
            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-emerald-700/40 dark:border-neutral-800">
              {sections.stats.map((stat, idx) => (
                <div
                  key={idx}
                  className="bg-emerald-900/60 dark:bg-neutral-900/90 border border-emerald-500/30 dark:border-neutral-800 p-2.5 rounded-xl text-xs flex items-center gap-2"
                >
                  <span className="text-emerald-400 text-sm">{stat.icon}</span>
                  <span className="font-semibold text-emerald-50 dark:text-neutral-200 text-[11px] leading-tight">
                    {stat.text}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Per Day Cards */}
      <div className="space-y-3">
        {sections.days.map((day, idx) => (
          <div
            key={idx}
            className="bg-white dark:bg-neutral-950 border border-slate-200 dark:border-neutral-800 rounded-2xl p-4 shadow-sm space-y-3 hover:border-emerald-300 dark:hover:border-emerald-500/60 transition-all"
          >
            {/* Day Header */}
            <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-slate-100 dark:border-neutral-800">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black font-extrabold text-xs rounded-lg shadow-sm">
                  Day {day.dayNumber}
                </span>
                {day.timeWindow && (
                  <span className="flex items-center gap-1 text-slate-600 dark:text-neutral-300 font-bold text-xs bg-slate-100 dark:bg-neutral-900 px-2.5 py-1 rounded-lg border border-transparent dark:border-neutral-800">
                    <Clock className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                    <span>{day.timeWindow}</span>
                  </span>
                )}
              </div>

              {day.transport && (
                <span className="flex items-center gap-1 text-[11px] font-semibold text-slate-500 dark:text-neutral-400 bg-slate-50 dark:bg-neutral-900 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-neutral-800">
                  <Car className="w-3.5 h-3.5 text-slate-400 dark:text-neutral-500" />
                  <span>{day.transport}</span>
                </span>
              )}
            </div>

            {/* Travel metrics if present */}
            {day.travelSummary && (
              <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-600 dark:text-neutral-300 bg-emerald-50/60 dark:bg-neutral-900/80 p-2 rounded-xl border border-emerald-100/80 dark:border-emerald-900/40">
                <span className="font-bold text-emerald-900 dark:text-emerald-300">🛣️ Travel: {day.travelSummary}</span>
                {day.savings && (
                  <span className="flex items-center gap-1 text-emerald-700 dark:text-emerald-400 font-bold ml-auto">
                    <TrendingDown className="w-3.5 h-3.5" />
                    <span>Saved {day.savings}</span>
                  </span>
                )}
              </div>
            )}

            {/* Activities Timeline */}
            <div className="space-y-2 pt-1">
              {day.activities.map((act, actIdx) => (
                <div
                  key={actIdx}
                  className="flex items-start gap-2.5 p-2 rounded-xl hover:bg-slate-50 dark:hover:bg-neutral-900/60 transition-colors"
                >
                  <span className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60 font-extrabold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                    {act.order}
                  </span>

                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center justify-between gap-1.5">
                      <h5 className="font-bold text-slate-900 dark:text-white text-xs md:text-sm">
                        {act.name}
                      </h5>
                      {act.fee && (
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 shrink-0 ${
                            act.fee.toLowerCase().includes('free')
                              ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                              : 'bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800'
                          }`}
                        >
                          <Ticket className="w-3 h-3" />
                          <span>{act.fee}</span>
                        </span>
                      )}
                    </div>

                    {act.time && (
                      <div className="flex items-center gap-1 text-[11px] text-slate-500 dark:text-neutral-400 mt-0.5 font-medium">
                        <Clock className="w-3 h-3 text-slate-400 dark:text-neutral-500" />
                        <span>{act.time}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Deferred Stops Alert Box */}
      {sections.deferred.length > 0 && (
        <div className="p-4 bg-amber-50/70 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 rounded-2xl space-y-2.5">
          <div className="flex items-center gap-2 text-amber-900 dark:text-amber-300 font-bold text-xs">
            <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
            <span>Deferred Stops (Daily Feasibility Protection)</span>
          </div>
          <div className="space-y-1.5 pl-6">
            {sections.deferred.map((item, idx) => (
              <div key={idx} className="text-xs text-amber-800 dark:text-amber-200 leading-relaxed">
                <span className="font-bold text-slate-900 dark:text-white">• {item.name}: </span>
                <span className="text-amber-900/90 dark:text-amber-300/90 italic">{item.reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Helper function to format bold text and bullet points in text
function renderFormattedText(text: string): React.ReactNode {
  const lines = text.split('\n');
  return lines.map((line, lineIdx) => {
    // Process markdown bold **text**
    const parts = line.split(/(\*\*[^*]+\*\*)/g);
    return (
      <div key={lineIdx} className={line.trim() === '' ? 'h-2' : 'py-0.5'}>
        {parts.map((part, partIdx) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return (
              <strong key={partIdx} className="font-bold text-slate-900 dark:text-white">
                {part.slice(2, -2)}
              </strong>
            );
          }
          return part;
        })}
      </div>
    );
  });
}

// Structure parser for itinerary messages
interface ParsedItinerary {
  replanning?: string;
  title?: string;
  header: boolean;
  stats: { icon: string; text: string }[];
  days: {
    dayNumber: number;
    timeWindow?: string;
    transport?: string;
    travelSummary?: string;
    savings?: string;
    activities: {
      order: number;
      name: string;
      time?: string;
      fee?: string;
    }[];
  }[];
  deferred: { name: string; reason: string }[];
}

function parseItineraryContent(raw: string): ParsedItinerary {
  const result: ParsedItinerary = {
    header: false,
    stats: [],
    days: [],
    deferred: [],
  };

  const lines = raw.split('\n').map((l) => l.trim()).filter(Boolean);

  let currentDay: (typeof result.days)[0] | null = null;
  let inDeferred = false;
  let inReplanning = false;
  const replanningLines: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Check for Replanning header
    if (line.includes('REPLANNING') || line.includes('Smart Replanning')) {
      inReplanning = true;
      continue;
    }
    if (inReplanning) {
      if (line.includes('OPTIMIZED ITINERARY') || line.includes('━━━') || line.includes('DAY 1')) {
        inReplanning = false;
        result.replanning = replanningLines.join('\n');
      } else {
        replanningLines.push(line);
        continue;
      }
    }

    // Check for Main Header Title
    if (line.includes('OPTIMIZED ITINERARY') || line.includes('Optimized Itinerary')) {
      result.header = true;
      result.title = line.replace(/[#*✨📍🌴━]/g, '').trim();
      continue;
    }

    // Check for Stat lines
    if (line.includes('Sightseeing Visits') || line.includes('sightseeing visits')) {
      result.header = true;
      result.stats.push({ icon: '🎯', text: line.replace(/[#*•]/g, '').trim() });
      continue;
    }
    if (line.includes('Transit') || line.includes('road transit') || line.includes('Road Travel')) {
      result.stats.push({ icon: '🚗', text: line.replace(/[#*•]/g, '').trim() });
      continue;
    }
    if (line.includes('distance reduction') || line.includes('Distance Reduction') || line.includes('Optimization')) {
      result.stats.push({ icon: '⚡', text: line.replace(/[#*•]/g, '').trim() });
      continue;
    }
    if (line.includes('Estimated Trip Cost') || line.includes('Total Estimated Trip Cost')) {
      result.stats.push({ icon: '💰', text: line.replace(/[#*•]/g, '').trim() });
      continue;
    }

    // Check for Day headers (e.g. DAY 1, Day 1, 🗓️ DAY 1)
    const dayMatch = line.match(/(?:🗓️|#+)?\s*(?:DAY|Day)\s*(\d+)(?:\s*[•(-]\s*(.+?)[)-]?)?$/i);
    if (dayMatch) {
      inDeferred = false;
      const num = parseInt(dayMatch[1], 10);
      const windowStr = dayMatch[2] ? dayMatch[2].replace(/[()*#]/g, '').trim() : '';
      currentDay = {
        dayNumber: num,
        timeWindow: windowStr,
        activities: [],
      };
      result.days.push(currentDay);
      continue;
    }

    // Check for Day transport / travel summary
    if (currentDay && (line.includes('Transit Mode') || line.includes('Transport') || line.includes('Day Travel'))) {
      const parts = line.split(/[|•]/);
      for (const p of parts) {
        if (p.includes('Transit') || p.includes('Transport')) {
          currentDay.transport = p.replace(/[#*🚕]/g, '').trim();
        } else if (p.includes('Travel') || p.includes('Day Travel')) {
          currentDay.travelSummary = p.replace(/[#*🛣️]/g, '').trim();
        } else if (p.includes('Saved') || p.includes('Savings')) {
          currentDay.savings = p.replace(/[#*📉]/g, '').trim();
        }
      }
      continue;
    }

    // Check for Deferred Stops section
    if (line.includes('DEFERRED STOPS') || line.includes('Deferred Stops')) {
      inDeferred = true;
      currentDay = null;
      continue;
    }

    if (inDeferred) {
      if (line.startsWith('•') || line.startsWith('-') || line.includes(':')) {
        const clean = line.replace(/^[•\-\s*⏳⚠️]+/, '');
        const splitIdx = clean.indexOf(':');
        if (splitIdx > 0) {
          result.deferred.push({
            name: clean.substring(0, splitIdx).replace(/[*]/g, '').trim(),
            reason: clean.substring(splitIdx + 1).replace(/[*]/g, '').trim(),
          });
        }
      }
      continue;
    }

    // Check for numbered activity (e.g. 1. Basilica of Bom Jesus [09:00 - 10:30] (Free Entry))
    if (currentDay) {
      const actMatch = line.match(/^\s*(\d+)[.)]\s*(?:[🏛️⛪🎨🏰🏖️🌊⛰️ temples]*\s*)?(.*?)(?:\s*[•⏱️\[(]\s*(\d{2}:\d{2}\s*-\s*\d{2}:\d{2})[\])]?)?(?:\s*[•🎟️(\[]\s*(Free Entry|Admission:[^\])]+|Fee:[^\])]+|₹\d+[^\])]*)[\])]?)?$/i);
      if (actMatch) {
        const order = parseInt(actMatch[1], 10);
        let name = actMatch[2] ? actMatch[2].replace(/[*\[\]()•]/g, '').trim() : 'Attraction';
        let time = actMatch[3] ? actMatch[3].trim() : undefined;
        let fee = actMatch[4] ? actMatch[4].trim() : undefined;

        // Fallback search for brackets in line if regex didn't capture time/fee
        if (!time) {
          const timeSub = line.match(/(\d{2}:\d{2}\s*-\s*\d{2}:\d{2})/);
          if (timeSub) time = timeSub[1];
        }
        if (!fee) {
          if (line.includes('Free Entry')) fee = 'Free Entry';
          else {
            const feeSub = line.match(/(₹\s*\d+|Admission:\s*₹?\d+|Fee:\s*₹?\d+)/i);
            if (feeSub) fee = feeSub[1];
          }
        }

        currentDay.activities.push({
          order,
          name,
          time,
          fee,
        });
      }
    }
  }

  return result;
}
