import React, { useState, useEffect } from 'react';
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
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [trips, setTrips] = useState<TripDetail[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

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

  const handleDeleteTrip = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this trip?')) return;

    try {
      await tripService.deleteTrip(id);
      setTrips((prev) => prev.filter((t) => t.id !== id));
    } catch (err) {
      alert('Failed to delete trip.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
        <p className="text-sm font-semibold text-slate-500">Loading your travel dashboard...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-8 space-y-10">
      {/* Welcome Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-6 md:p-8 bg-gradient-to-r from-teal-700 to-teal-900 text-white rounded-3xl shadow-lg">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold">Welcome back, {user?.full_name}!</h1>
          <p className="text-xs md:text-sm text-teal-200 mt-1">
            Manage your optimized itineraries, view spatial maps, or replan with AI.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/plan"
            className="px-5 py-2.5 bg-white text-teal-800 font-bold rounded-xl text-xs flex items-center gap-2 shadow hover:bg-teal-50 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>New Trip</span>
          </Link>
          <Link
            to="/chat"
            className="px-5 py-2.5 bg-teal-600 text-white font-bold rounded-xl text-xs flex items-center gap-2 shadow hover:bg-teal-500 transition-all border border-teal-400/40"
          >
            <MessageSquare className="w-4 h-4" />
            <span>AI Chat</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-2xl flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Saved Trips Grid */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Compass className="w-5 h-5 text-teal-600" />
            <span>Saved Itineraries ({trips.length})</span>
          </h2>
        </div>

        {trips.length === 0 ? (
          <div className="bg-white rounded-3xl p-10 text-center border border-slate-200 space-y-3">
            <Compass className="w-10 h-10 text-slate-300 mx-auto" />
            <h3 className="font-bold text-slate-700 text-base">No trips planned yet</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Use our Multi-Criteria & OR-Tools planner to create your first optimized itinerary.
            </p>
            <Link
              to="/plan"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-teal-600 text-white text-xs font-bold rounded-xl shadow-md hover:bg-teal-700 transition-all mt-2"
            >
              <span>Create Itinerary</span>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {trips.map((t) => (
              <div
                key={t.id}
                onClick={() => navigate(`/itinerary/${t.id}`)}
                className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:shadow-md hover:border-teal-300 transition-all cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 bg-teal-50 text-teal-700 rounded-full">
                      {t.destination_id}
                    </span>
                    <button
                      onClick={(e) => handleDeleteTrip(t.id, e)}
                      className="text-slate-300 hover:text-rose-600 p-1 transition-colors"
                      title="Delete Trip"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <h3 className="text-base font-bold text-slate-900 mb-1">{t.title}</h3>
                </div>

                <div className="space-y-1.5 pt-4 border-t border-slate-100 text-xs text-slate-500 mt-4">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>{t.start_date}</span>
                    </span>
                    <span className="font-semibold text-slate-700">₹{t.total_budget.toLocaleString()}</span>
                  </div>

                  <div className="flex items-center justify-between text-teal-700 font-bold pt-1">
                    <span>View Itinerary & Map</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Active AI Chat Sessions */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-teal-600" />
          <span>Active AI Chat Sessions ({sessions.length})</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sessions.map((s) => (
            <div
              key={s.id}
              onClick={() => navigate('/chat')}
              className="bg-white p-4 rounded-2xl border border-slate-200 flex items-center justify-between hover:border-teal-300 hover:bg-slate-50/50 transition-all cursor-pointer"
            >
              <div>
                <h4 className="text-sm font-bold text-slate-900">{s.title}</h4>
                <p className="text-[11px] text-slate-400">
                  {s.created_at ? new Date(s.created_at).toLocaleDateString() : 'Active session'}
                </p>
              </div>
              <span className="text-xs font-bold text-teal-600">Resume &rarr;</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
