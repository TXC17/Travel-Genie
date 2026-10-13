import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { tripService } from '../services/tripService';
import {
  MultiDayTripOptimizationResponse,
  GenerateItineraryResponse,
  AccommodationRecommendationItem,
} from '../types';
import { MapComponent } from '../components/map/MapComponent';
import { DayScheduleCard } from '../components/itinerary/DayScheduleCard';
import { OptimizationMetricsCard } from '../components/itinerary/OptimizationMetricsCard';
import { DeferredAttractionsCard } from '../components/itinerary/DeferredAttractionsCard';
import { IntercityTransportCard } from '../components/transport/IntercityTransportCard';
import { AccommodationPicker } from '../components/accommodation/AccommodationPicker';
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
  const [selectedAccommodation, setSelectedAccommodation] = useState<AccommodationRecommendationItem | null>(
    (location.state?.selectedAccommodation as AccommodationRecommendationItem) || null
  );
  const [tripBudget, setTripBudget] = useState<number | undefined>(
    (location.state?.generatedData as GenerateItineraryResponse | undefined)?.constraints?.total_budget
  );
  const [partySize, setPartySize] = useState<number | undefined>(
    (location.state?.generatedData as GenerateItineraryResponse | undefined)?.constraints?.party_size
  );
  const [startDate, setStartDate] = useState<string | undefined>(
    (location.state?.generatedData as GenerateItineraryResponse | undefined)?.constraints?.start_date
  );
  const [durationDays, setDurationDays] = useState<number | undefined>(
    (location.state?.generatedData as GenerateItineraryResponse | undefined)?.constraints?.duration_days
  );

  useEffect(() => {
    // Check if passed via router state
    const stateData = location.state?.generatedData as GenerateItineraryResponse | undefined;
    if (stateData && stateData.itinerary) {
      setItineraryData(stateData.itinerary);
      setTripTitle(stateData.title || `${stateData.destination_id.toUpperCase()} Itinerary`);
      if (stateData.constraints) {
        if (stateData.constraints.total_budget !== undefined) {
          setTripBudget(stateData.constraints.total_budget);
        }
        if (stateData.constraints.party_size !== undefined) {
          setPartySize(stateData.constraints.party_size);
        }
        if (stateData.constraints.start_date) {
          setStartDate(stateData.constraints.start_date);
        }
        if (stateData.constraints.duration_days !== undefined) {
          setDurationDays(stateData.constraints.duration_days);
        }
      }
      // If constraints are missing party_size or total_budget, fetch from trip if ID is available
      if (
        (stateData.constraints?.total_budget === undefined || stateData.constraints?.party_size === undefined) &&
        (id || stateData.trip_id)
      ) {
        tripService.getTrip(id || stateData.trip_id).then((trip) => {
          if (trip.total_budget !== undefined) setTripBudget(trip.total_budget);
          if (trip.party_size !== undefined) setPartySize(trip.party_size);
          if (trip.start_date) setStartDate(trip.start_date);
          if (trip.number_of_days !== undefined) setDurationDays(trip.number_of_days);
        }).catch(() => {});
      }
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
      if (trip.total_budget !== undefined) {
        setTripBudget(trip.total_budget);
      }
      if (trip.party_size !== undefined) {
        setPartySize(trip.party_size);
      }
      if (trip.start_date) {
        setStartDate(trip.start_date);
      }
      if (trip.number_of_days !== undefined) {
        setDurationDays(trip.number_of_days);
      }

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

      if (trip.selected_accommodation && !selectedAccommodation) {
        const nights = trip.number_of_days ? Math.max(1, trip.number_of_days - 1) : 2;
        const capacity = trip.selected_accommodation.room_capacity || 2;
        const rooms = Math.ceil(trip.party_size / Math.max(1, capacity));
        const cost = trip.selected_accommodation.price_per_night * nights * rooms;
        setSelectedAccommodation({
          accommodation: trip.selected_accommodation,
          nights,
          rooms_needed: rooms,
          price_per_night: trip.selected_accommodation.price_per_night,
          total_cost: cost,
          budget_fit_score: 1.0,
          is_within_budget: cost <= trip.total_budget,
          match_score: 1.0,
          match_reasons: ['Persisted trip accommodation preference'],
          provenance_badge: trip.selected_accommodation.is_verified ? 'VERIFIED' : 'ESTIMATED',
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
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600 dark:text-emerald-400" />
        <p className="text-sm font-semibold text-slate-600 dark:text-neutral-400">
          Loading optimized travel itinerary...
        </p>
      </div>
    );
  }

  if (error || !itineraryData) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-4">
        <div className="inline-flex p-3 bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 rounded-2xl border border-rose-200 dark:border-rose-900/60">
          <AlertCircle className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Itinerary Not Found</h2>
        <p className="text-sm text-slate-500 dark:text-neutral-400">{error || 'No itinerary data available.'}</p>
        <button
          onClick={() => navigate('/plan')}
          className="liquid-btn px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-black font-extrabold rounded-xl text-sm cursor-pointer shadow-md"
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
            className="text-xs text-slate-500 dark:text-neutral-400 hover:text-emerald-600 dark:hover:text-emerald-400 flex items-center gap-1 mb-1 font-semibold transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Plan Another Trip</span>
          </button>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white capitalize">
            {tripTitle}
          </h1>
          <p className="text-xs text-slate-500 dark:text-neutral-400 flex items-center gap-2">
            <span className="capitalize font-semibold text-emerald-700 dark:text-emerald-400">
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
            className="liquid-btn px-4 py-2 bg-white dark:bg-neutral-900 border border-slate-200 dark:border-neutral-800 text-slate-700 dark:text-neutral-200 font-semibold rounded-xl text-xs flex items-center gap-1.5 hover:bg-slate-50 dark:hover:bg-neutral-800 hover:border-emerald-300 dark:hover:border-emerald-500/50 transition-all cursor-pointer shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-emerald-500 dark:text-emerald-400" />
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
              className={`liquid-btn px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap cursor-pointer transition-all ${
                selectedDay === null
                  ? 'bg-emerald-700 dark:bg-emerald-500 text-white dark:text-black dark:font-extrabold shadow-md'
                  : 'bg-white dark:bg-neutral-900 border border-slate-200 dark:border-neutral-800 text-slate-700 dark:text-neutral-300 hover:bg-slate-100 dark:hover:bg-neutral-800'
              }`}
            >
              All Days ({itineraryData.days.length})
            </button>

            {itineraryData.days.map((day) => (
              <button
                key={`tab-${day.day_number}`}
                onClick={() => setSelectedDay(day.day_number)}
                className={`liquid-btn px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap cursor-pointer transition-all ${
                  selectedDay === day.day_number
                    ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black dark:font-extrabold shadow-md'
                    : 'bg-white dark:bg-neutral-900 border border-slate-200 dark:border-neutral-800 text-slate-700 dark:text-neutral-300 hover:bg-slate-100 dark:hover:bg-neutral-800'
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
          <div className="liquid-glass rounded-3xl p-4 border border-slate-200 dark:border-neutral-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between px-2">
              <span className="text-xs font-bold text-slate-700 dark:text-neutral-300 uppercase tracking-wider flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <span>Spatial Route Map</span>
              </span>
              <span className="text-xs text-slate-400 dark:text-neutral-500 font-mono">OpenStreetMap</span>
            </div>

            <div className="h-[480px]">
              <MapComponent
                days={itineraryData.days}
                selectedDayNumber={selectedDay || undefined}
                accommodation={selectedAccommodation?.accommodation || null}
                onSelectDay={setSelectedDay}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Intercity Transit Options Assistant */}
      <IntercityTransportCard
        destinationId={itineraryData.destination_id}
        partySize={partySize}
        budget={tripBudget}
      />

      {/* Curated Lodging & Accommodations Assistant */}
      <AccommodationPicker
        destinationId={itineraryData.destination_id}
        partySize={partySize}
        totalBudget={tripBudget}
        startDate={startDate}
        durationDays={durationDays ?? itineraryData.total_days}
        itinerary={itineraryData}
        selectedAccommodation={selectedAccommodation}
        onSelectAccommodation={setSelectedAccommodation}
      />

      {/* Floating AI Chat Assistant with Real-Time Smart Replanning */}
      <ChatWidget onItineraryUpdated={handleItineraryUpdated} />
    </div>
  );
};
