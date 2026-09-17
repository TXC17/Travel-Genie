import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { tripService, TripDetail } from '../services/tripService';
import { chatService } from '../services/chatService';
import { ChatSession } from '../types';
import {
  Compass,
  MapPin,
  Calendar,
  DollarSign,
  Trash2,
  ExternalLink,
  MessageSquare,
  Plus,
  Loader2,
  AlertCircle,
  Pencil,
  Check,
  X,
  Sparkles,
  Users,
  Clock,
  ArrowRight,
} from 'lucide-react';

const DESTINATION_META: Record<string, { emoji: string; name: string; state: string; badgeColor: string }> = {
  hampi: { emoji: '🏛️', name: 'Hampi', state: 'Karnataka', badgeColor: 'bg-amber-100 text-amber-800' },
  coorg: { emoji: '☕', name: 'Coorg', state: 'Karnataka', badgeColor: 'bg-emerald-100 text-emerald-800' },
  dandeli: { emoji: '🌲', name: 'Dandeli', state: 'Karnataka', badgeColor: 'bg-emerald-100 text-emerald-800' },
  goa: { emoji: '🏖️', name: 'Goa', state: 'Goa', badgeColor: 'bg-amber-100 text-amber-800' },
};

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [trips, setTrips] = useState<TripDetail[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Trip Renaming State
  const [editingTripId, setEditingTripId] = useState<string | null>(null);
  const [editingTripTitle, setEditingTripTitle] = useState<string>('');
  const [isSavingTripRename, setIsSavingTripRename] = useState<boolean>(false);
  const editTripInputRef = useRef<HTMLInputElement>(null);

  // Chat Session Renaming State
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingSessionTitle, setEditingSessionTitle] = useState<string>('');
  const editSessionInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (editingTripId && editTripInputRef.current) {
      editTripInputRef.current.focus();
      editTripInputRef.current.select();
    }
  }, [editingTripId]);

  useEffect(() => {
    if (editingSessionId && editSessionInputRef.current) {
      editSessionInputRef.current.focus();
      editSessionInputRef.current.select();
    }
  }, [editingSessionId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [tripsList, sessionsList] = await Promise.all([
        tripService.getUserTrips(),
        chatService.getSessions(),
      ]);
      setTrips(tripsList);
      setSessions(sessionsList);
    } catch (err) {
      console.error('Failed to load dashboard data', err);
      setError('Could not load saved trips.');
    } finally {
      setLoading(false);
    }
  };

  // TRIP ACTIONS
  const handleStartTripRename = (trip: TripDetail, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingTripId(trip.id);
    setEditingTripTitle(trip.title);
  };

  const handleCancelTripRename = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setEditingTripId(null);
    setEditingTripTitle('');
  };

  const handleSaveTripRename = async (tripId: string, e?: React.MouseEvent | React.FormEvent) => {
    if (e) e.stopPropagation();
    if (!editingTripTitle.trim()) {
      handleCancelTripRename();
      return;
    }

    try {
      setIsSavingTripRename(true);
      await tripService.updateTrip(tripId, { title: editingTripTitle.trim() });
      setTrips((prev) =>
        prev.map((t) => (t.id === tripId ? { ...t, title: editingTripTitle.trim() } : t))
      );
      setEditingTripId(null);
      setEditingTripTitle('');
    } catch (err) {
      console.error('Failed to update trip title', err);
      alert('Failed to save trip title. Please try again.');
    } finally {
      setIsSavingTripRename(false);
    }
  };

  const handleDeleteTrip = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this trip itinerary?')) return;

    try {
      await tripService.deleteTrip(id);
      setTrips((prev) => prev.filter((t) => t.id !== id));
    } catch (err) {
      alert('Failed to delete trip.');
    }
  };

  // SESSION ACTIONS
  const handleStartSessionRename = (session: ChatSession, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditingSessionTitle(session.title);
  };

  const handleCancelSessionRename = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setEditingSessionId(null);
    setEditingSessionTitle('');
  };

  const handleSaveSessionRename = async (sessionId: string, e?: React.MouseEvent | React.FormEvent) => {
    if (e) e.stopPropagation();
    if (!editingSessionTitle.trim()) {
      handleCancelSessionRename();
      return;
    }

    try {
      const updated = await chatService.renameSession(sessionId, editingSessionTitle.trim());
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? { ...s, title: updated.title } : s))
      );
      setEditingSessionId(null);
      setEditingSessionTitle('');
    } catch (err) {
      console.error('Failed to rename session', err);
    }
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Delete this AI chat session?')) return;

    try {
      await chatService.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    } catch (err) {
      console.error('Failed to delete session', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
        <p className="text-sm font-bold text-slate-500">Loading your travel dashboard...</p>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-64px)] max-w-6xl mx-auto px-4 py-6 sm:px-6 sm:py-8 flex flex-col justify-between space-y-8">
      <div className="space-y-8 flex-1">
        {/* Welcome Banner */}
        <div className="liquid-glass relative overflow-hidden p-6 sm:p-8 rounded-3xl shadow-md bg-gradient-to-br from-emerald-200/95 via-teal-100/90 to-amber-100/85 dark:from-neutral-950 dark:via-neutral-950 dark:to-neutral-950 border-2 border-emerald-400/90 dark:border-neutral-800">
          <div className="flex flex-wrap items-center justify-between gap-6 relative z-10">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-700/15 dark:bg-emerald-950/60 text-emerald-950 dark:text-emerald-300 rounded-full text-xs font-bold border border-emerald-500/40 dark:border-emerald-800/60">
                <Sparkles className="w-3.5 h-3.5 text-emerald-800 dark:text-emerald-400" />
                <span>AI Travel Genie Control Center</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white">
                Welcome back, {user?.full_name || 'Traveler'}! 👋
              </h1>
              <p className="text-xs sm:text-sm text-slate-800 dark:text-neutral-300 max-w-xl font-medium">
                Manage your saved multi-day itineraries, explore spatial route maps, or plan and replan with conversational AI.
              </p>

              {/* Quick stats pills */}
              <div className="flex items-center gap-3 pt-2">
                <div className="liquid-btn px-3.5 py-1.5 bg-slate-100 dark:bg-neutral-900/90 rounded-xl text-xs font-bold border border-slate-300 dark:border-neutral-800 flex items-center gap-1.5 text-slate-800 dark:text-white shadow-xs">
                  <span>🗺️</span>
                  <span>{trips.length} Saved {trips.length === 1 ? 'Trip' : 'Trips'}</span>
                </div>
                <div className="liquid-btn px-3.5 py-1.5 bg-slate-100 dark:bg-neutral-900/90 rounded-xl text-xs font-bold border border-slate-300 dark:border-neutral-800 flex items-center gap-1.5 text-slate-800 dark:text-white shadow-xs">
                  <span>💬</span>
                  <span>{sessions.length} AI {sessions.length === 1 ? 'Session' : 'Sessions'}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Link
                to="/plan"
                className="liquid-btn px-5 py-3 bg-emerald-700 hover:bg-emerald-800 dark:bg-emerald-400 dark:hover:bg-emerald-300 text-white dark:text-black font-extrabold rounded-xl text-xs sm:text-sm flex items-center gap-2 shadow-md cursor-pointer"
              >
                <Plus className="w-4 h-4 text-white dark:text-black" />
                <span>+ Plan New Trip</span>
              </Link>
              <Link
                to="/chat"
                className="liquid-btn px-5 py-3 bg-white hover:bg-slate-50 dark:bg-neutral-900 dark:hover:bg-neutral-850 text-slate-900 dark:text-white font-bold rounded-xl text-xs sm:text-sm flex items-center gap-2 shadow-sm border-2 border-emerald-400/80 dark:border-neutral-800 cursor-pointer"
              >
                <MessageSquare className="w-4 h-4 text-emerald-700 dark:text-emerald-400" />
                <span>💬 AI Assistant</span>
              </Link>
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 rounded-2xl flex items-center gap-3 text-sm shadow-sm font-semibold">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Saved Trips Grid */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
              <Compass className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              <span>🗺️ Saved Itineraries ({trips.length})</span>
            </h2>
            <Link
              to="/plan"
              className="text-xs font-bold text-emerald-700 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 flex items-center gap-1"
            >
              <span>Create New</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {trips.length === 0 ? (
            <div className="liquid-glass rounded-3xl p-10 text-center border border-slate-200 dark:border-neutral-800 shadow-sm space-y-3">
              <Compass className="w-12 h-12 text-slate-300 dark:text-neutral-600 mx-auto" />
              <h3 className="font-extrabold text-slate-800 dark:text-white text-base">No saved itineraries yet</h3>
              <p className="text-xs text-slate-500 dark:text-neutral-400 max-w-sm mx-auto">
                Use our Multi-Criteria & OR-Tools optimizer to generate and save your first personalized trip.
              </p>
              <Link
                to="/plan"
                className="liquid-btn inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black text-xs font-extrabold rounded-xl shadow-md hover:bg-emerald-700 dark:hover:bg-emerald-400 mt-2 cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>Plan Your First Trip</span>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {trips.map((t) => {
                const meta = DESTINATION_META[t.destination_id.toLowerCase()] || {
                  emoji: '📍',
                  name: t.destination_id.toUpperCase(),
                  state: 'Destination',
                  badgeColor: 'bg-emerald-100 text-emerald-800',
                };
                const isEditingThisTrip = editingTripId === t.id;

                return (
                  <div
                    key={t.id}
                    onClick={() => !isEditingThisTrip && navigate(`/itinerary/${t.id}`)}
                    className="liquid-card rounded-3xl p-5 border border-slate-200 dark:border-neutral-800 shadow-sm cursor-pointer flex flex-col justify-between group"
                  >
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className={`text-[11px] font-extrabold uppercase tracking-wider px-3 py-1 rounded-full flex items-center gap-1.5 ${meta.badgeColor}`}>
                          <span>{meta.emoji}</span>
                          <span>{meta.name}</span>
                        </span>

                        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                          {!isEditingThisTrip && (
                            <button
                              onClick={(e) => handleStartTripRename(t, e)}
                              className="text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-neutral-800 transition-colors"
                              title="Rename Trip"
                            >
                              <Pencil className="w-3.5 h-3.5" />
                            </button>
                          )}
                          <button
                            onClick={(e) => handleDeleteTrip(t.id, e)}
                            className="text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 p-1.5 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/50 transition-colors"
                            title="Delete Trip"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>

                      {/* Title or Inline Edit */}
                      {isEditingThisTrip ? (
                        <div
                          className="flex items-center gap-1.5 py-1"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <input
                            ref={editTripInputRef}
                            type="text"
                            value={editingTripTitle}
                            onChange={(e) => setEditingTripTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveTripRename(t.id);
                              if (e.key === 'Escape') handleCancelTripRename();
                            }}
                            className="flex-1 px-3 py-1.5 text-sm font-bold text-slate-900 dark:text-white border-2 border-emerald-500 dark:border-emerald-500 rounded-xl focus:outline-none bg-white dark:bg-black"
                          />
                          <button
                            onClick={(e) => handleSaveTripRename(t.id, e)}
                            disabled={isSavingTripRename}
                            className="p-1.5 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-black rounded-lg transition-colors cursor-pointer font-bold"
                            title="Save"
                          >
                            {isSavingTripRename ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <Check className="w-3.5 h-3.5" />
                            )}
                          </button>
                          <button
                            onClick={handleCancelTripRename}
                            className="p-1.5 bg-slate-200 dark:bg-neutral-800 hover:bg-slate-300 dark:hover:bg-neutral-700 text-slate-700 dark:text-neutral-200 rounded-lg transition-colors cursor-pointer"
                            title="Cancel"
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ) : (
                        <h3 className="text-base font-extrabold text-slate-900 dark:text-white line-clamp-1 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                          {t.title}
                        </h3>
                      )}
                    </div>

                    <div className="space-y-2 pt-4 border-t border-slate-100 dark:border-neutral-800 text-xs text-slate-600 dark:text-neutral-300 mt-4">
                      <div className="flex items-center justify-between font-semibold">
                        <span className="flex items-center gap-1 text-slate-500 dark:text-neutral-400">
                          <Calendar className="w-3.5 h-3.5 text-slate-400 dark:text-neutral-500" />
                          <span>{t.start_date}</span>
                        </span>
                        <span className="font-extrabold text-slate-900 dark:text-white">
                          ₹{t.total_budget.toLocaleString()}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-slate-400 dark:text-neutral-500">
                        <span className="flex items-center gap-1">
                          <Users className="w-3.5 h-3.5" />
                          <span>{t.party_size} {t.party_size === 1 ? 'Traveler' : 'Travelers'}</span>
                        </span>
                        <span className="font-bold text-emerald-700 dark:text-emerald-400 flex items-center gap-0.5 group-hover:translate-x-0.5 transition-transform">
                          <span>View Route & Map</span>
                          <ExternalLink className="w-3 h-3" />
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* Active AI Chat Sessions */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              <span>💬 AI Planning Sessions ({sessions.length})</span>
            </h2>
            <Link
              to="/chat"
              className="text-xs font-bold text-emerald-700 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 flex items-center gap-1"
            >
              <span>Open Chat</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {sessions.length === 0 ? (
            <div className="liquid-glass rounded-3xl p-6 text-center border border-slate-200 dark:border-neutral-800 text-xs text-slate-400 dark:text-neutral-500">
              No active AI chat sessions. Click on <strong>AI Assistant</strong> to begin planning.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {sessions.map((s) => {
                const isEditingThisSession = editingSessionId === s.id;

                return (
                  <div
                    key={s.id}
                    onClick={() => !isEditingThisSession && navigate('/chat')}
                    className="liquid-card p-4 rounded-2xl border border-slate-200 dark:border-neutral-800 flex flex-col justify-between cursor-pointer space-y-3 group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      {isEditingThisSession ? (
                        <div
                          className="flex items-center gap-1.5 w-full"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <input
                            ref={editSessionInputRef}
                            type="text"
                            value={editingSessionTitle}
                            onChange={(e) => setEditingSessionTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveSessionRename(s.id);
                              if (e.key === 'Escape') handleCancelSessionRename();
                            }}
                            className="flex-1 px-2.5 py-1 text-xs font-bold text-slate-900 dark:text-white border-2 border-emerald-500 dark:border-emerald-500 rounded-lg focus:outline-none bg-white dark:bg-black"
                          />
                          <button
                            onClick={(e) => handleSaveSessionRename(s.id, e)}
                            className="p-1 bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black rounded cursor-pointer font-bold"
                          >
                            <Check className="w-3 h-3" />
                          </button>
                          <button
                            onClick={handleCancelSessionRename}
                            className="p-1 bg-slate-200 dark:bg-neutral-800 text-slate-700 dark:text-neutral-200 rounded cursor-pointer"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className="text-base">💬</span>
                          <div>
                            <h4 className="text-xs font-bold text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors line-clamp-1">
                              {s.title}
                            </h4>
                            <p className="text-[10px] text-slate-400 dark:text-neutral-500 flex items-center gap-1 mt-0.5">
                              <Clock className="w-3 h-3" />
                              <span>{s.created_at ? new Date(s.created_at).toLocaleDateString() : 'Active'}</span>
                            </p>
                          </div>
                        </div>
                      )}

                      {!isEditingThisSession && (
                        <div className="flex items-center gap-0.5" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={(e) => handleStartSessionRename(s, e)}
                            className="text-slate-300 dark:text-neutral-600 hover:text-emerald-600 dark:hover:text-emerald-400 p-1 rounded transition-colors"
                            title="Rename"
                          >
                            <Pencil className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={(e) => handleDeleteSession(s.id, e)}
                            className="text-slate-300 dark:text-neutral-600 hover:text-rose-600 dark:hover:text-rose-400 p-1 rounded transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="flex justify-end pt-2 border-t border-slate-100 dark:border-neutral-800 text-[11px] font-bold text-emerald-700 dark:text-emerald-400">
                      <span>Resume Chat &rarr;</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
