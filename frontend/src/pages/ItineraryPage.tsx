import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { tripService } from '../services/tripService';
import { MultiDayTripOptimizationResponse, GenerateItineraryResponse } from '../types';
import { MapComponent } from '../components/map/MapComponent';
import { DayScheduleCard } from '../components/itinerary/DayScheduleCard';
import { OptimizationMetricsCard } from '../components/itinerary/OptimizationMetricsCard';
import { DeferredAttractionsCard } from '../components/itinerary/DeferredAttractionsCard';
import { ChatWidget } from '../components/chat/ChatWidget';
import {
  MapPin,
  Calendar,
  Sparkles,
  ArrowLeft,
  Share2,
  Download,
  Loader2,
  AlertCircle,
} from 'lucide-react';

export const ItineraryPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  const [itineraryData, setItineraryData] = useState<MultiDayTripOptimizationResponse | null>(null);
  const [tripTitle, setTripTitle] = useState<string>('Optimized Travel Itinerary');
  const [selectedDay, setSelectedDay] = useState<number | null>(null); // null = all days
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if passed via router state
    const stateData = location.state?.generatedData as GenerateItineraryResponse | undefined;
    if (stateData && stateData.itinerary) {
      setItineraryData(stateData.itinerary);
      setTripTitle(stateData.title || `${stateData.destination_id.toUpperCase()} Itinerary`);
    } else if (id) {
      loadTripItinerary(id);
    }
  }, [id, location.state]);

  const loadTripItinerary = async (tripId: string) => {
    try {
      setLoading(true);
      setError(null);
      const trip = await tripService.getTrip(tripId);
      setTripTitle(trip.title);

      // Reconstruct or extract latest itinerary
      if (trip.itineraries && trip.itineraries.length > 0) {
        const latest = trip.itineraries[0];
        // Convert to MultiDayTripOptimizationResponse shape
        setItineraryData({
          destination_id: trip.destination_id,
          trip_id: trip.id,
          total_days: latest.days?.length || 1,
          total_scheduled_attractions: latest.days?.reduce((acc: number, d: any) => acc + (d.items?.length || 0), 0) || 0,
          total_deferred_attractions: 0,
          total_travel_distance_km: latest.total_travel_distance_km || 0,
          total_travel_duration_hours: latest.total_travel_duration_hours || 0,
          total_sightseeing_duration_hours: latest.total_sightseeing_duration_hours || 0,
          total_day_duration_hours: (latest.total_travel_duration_hours || 0) + (latest.total_sightseeing_duration_hours || 0),
          total_estimated_cost: latest.total_estimated_cost || 0,
          aggregate_distance_reduction_pct: latest.optimization_metrics?.distance_reduction_pct || 0,
          days: latest.days || [],
          deferred_attractions: [],
        });
      }
    } catch (err: any) {
      setError('Failed to load itinerary details.');
    } finally {
      setLoading(false);
    }
  };

  const handleItineraryUpdated = (updatedItinerary: MultiDayTripOptimizationResponse) => {
    setItineraryData(updatedItinerary);
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
        <p className="text-sm font-semibold text-slate-600">
          Loading optimized travel itinerary...
        </p>
      </div>
    );
  }

  if (error || !itineraryData) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-4">
        <div className="inline-flex p-3 bg-rose-50 text-rose-600 rounded-2xl">
          <AlertCircle className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900">Itinerary Not Found</h2>
        <p className="text-sm text-slate-500">{error || 'No itinerary data available.'}</p>
        <button
          onClick={() => navigate('/plan')}
          className="px-6 py-2.5 bg-teal-600 text-white rounded-xl font-bold text-sm"
        >
          Create New Plan
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 py-6">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <button
            onClick={() => navigate('/plan')}
            className="text-xs text-slate-500 hover:text-teal-600 flex items-center gap-1 mb-1 font-semibold"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Plan Another Trip</span>
          </button>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 capitalize">
            {tripTitle}
          </h1>
          <p className="text-xs text-slate-500 flex items-center gap-2">
            <span className="capitalize font-semibold text-teal-700">
              {itineraryData.destination_id}
            </span>
            <span>&bull;</span>
            <span>{itineraryData.total_days} Sightseeing Days</span>
            <span>&bull;</span>
            <span>{itineraryData.total_scheduled_attractions} Scheduled Stops</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => window.print()}
            className="px-4 py-2 bg-white border border-slate-200 text-slate-700 font-semibold rounded-xl text-xs flex items-center gap-1.5 hover:bg-slate-50 transition-all cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export / Print</span>
          </button>
        </div>
      </div>

      {/* Optimization Statistics Summary Card */}
      <OptimizationMetricsCard itinerary={itineraryData} />

      {/* Deferred Attractions Accordion (if any) */}
      <DeferredAttractionsCard deferredAttractions={itineraryData.deferred_attractions} />

      {/* Interactive Map & Day Schedules Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Day Schedules (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Day Selection Tabs */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            <button
              onClick={() => setSelectedDay(null)}
              className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer ${
                selectedDay === null
                  ? 'bg-slate-900 text-white shadow-md'
                  : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
              }`}
            >
              All Days ({itineraryData.days.length})
            </button>

            {itineraryData.days.map((day) => (
              <button
                key={`tab-${day.day_number}`}
                onClick={() => setSelectedDay(day.day_number)}
                className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer ${
                  selectedDay === day.day_number
                    ? 'bg-teal-600 text-white shadow-md'
                    : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
                }`}
              >
                Day {day.day_number}
              </button>
            ))}
          </div>

          {/* Render Schedule Cards */}
          <div className="space-y-6">
            {itineraryData.days
              .filter((d) => selectedDay === null || d.day_number === selectedDay)
              .map((day) => (
                <DayScheduleCard key={`day-card-${day.day_number}`} day={day} />
              ))}
          </div>
        </div>

        {/* Right Column: Sticky Interactive Leaflet Map (5 Cols) */}
        <div className="lg:col-span-5 lg:sticky lg:top-24 space-y-4">
          <div className="bg-white rounded-3xl p-4 border border-slate-200 shadow-sm space-y-3">
            <div className="flex items-center justify-between px-2">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-teal-600" />
                <span>Spatial Route Map</span>
              </span>
              <span className="text-xs text-slate-400">OpenStreetMap</span>
            </div>

            <div className="h-[480px]">
              <MapComponent
                days={itineraryData.days}
                selectedDayNumber={selectedDay || undefined}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Floating AI Chat Assistant with Real-Time Smart Replanning */}
      <ChatWidget onItineraryUpdated={handleItineraryUpdated} />
    </div>
  );
};
