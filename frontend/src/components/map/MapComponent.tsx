import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { OptimizedDaySchedule, Accommodation } from '../../types';
import { Clock, DollarSign, Users, Hotel, Layers } from 'lucide-react';

interface MapComponentProps {
  days: OptimizedDaySchedule[];
  selectedDayNumber?: number;
  center?: [number, number];
  zoom?: number;
  accommodation?: Accommodation | null;
  onSelectDay?: (dayNumber: number | null) => void;
}

const DAY_COLORS = [
  '#0d9488', // Day 1: Teal
  '#6366f1', // Day 2: Indigo
  '#f59e0b', // Day 3: Amber
  '#ec4899', // Day 4: Pink
  '#8b5cf6', // Day 5: Purple
  '#06b6d4', // Day 6: Cyan
  '#10b981', // Day 7: Emerald
];

// Helper component inside MapContainer to programmatically adjust viewport bounds without remounting
const MapViewportController: React.FC<{
  targetBounds: [number, number][] | null;
  focusPoint: [number, number] | null;
  defaultCenter: [number, number];
  defaultZoom: number;
}> = ({ targetBounds, focusPoint, defaultCenter, defaultZoom }) => {
  const map = useMap();

  useEffect(() => {
    if (focusPoint) {
      map.flyTo(focusPoint, Math.max(map.getZoom(), 15), {
        animate: true,
        duration: 0.8,
      });
    } else if (targetBounds && targetBounds.length > 0) {
      if (targetBounds.length === 1) {
        map.flyTo(targetBounds[0], Math.max(map.getZoom(), 14), {
          animate: true,
          duration: 0.8,
        });
      } else {
        const bounds = L.latLngBounds(targetBounds.map((p) => L.latLng(p[0], p[1])));
        map.fitBounds(bounds, {
          padding: [50, 50],
          maxZoom: 15,
          animate: true,
          duration: 0.8,
        });
      }
    } else {
      map.flyTo(defaultCenter, defaultZoom, {
        animate: true,
        duration: 0.8,
      });
    }
  }, [map, targetBounds, focusPoint, defaultCenter, defaultZoom]);

  return null;
};

export const MapComponent: React.FC<MapComponentProps> = ({
  days,
  selectedDayNumber: propSelectedDayNumber,
  center = [15.335, 76.46],
  zoom = 13,
  accommodation = null,
  onSelectDay,
}) => {
  // Internal selection state synchronized with prop if provided
  const [internalSelectedDay, setInternalSelectedDay] = useState<number | null>(
    propSelectedDayNumber ?? null
  );
  const [focusPoint, setFocusPoint] = useState<[number, number] | null>(null);
  const hotelMarkerRef = useRef<L.Marker | null>(null);

  useEffect(() => {
    if (propSelectedDayNumber !== undefined) {
      setInternalSelectedDay(propSelectedDayNumber);
      setFocusPoint(null);
    }
  }, [propSelectedDayNumber]);

  const activeDay = internalSelectedDay;

  const handleDayClick = (dayNumber: number) => {
    const nextDay = activeDay === dayNumber ? null : dayNumber;
    setInternalSelectedDay(nextDay);
    setFocusPoint(null);
    if (onSelectDay) {
      onSelectDay(nextDay);
    }
  };

  const handleShowAll = () => {
    setInternalSelectedDay(null);
    setFocusPoint(null);
    if (onSelectDay) {
      onSelectDay(null);
    }
  };

  const handleHotelClick = () => {
    if (accommodation?.latitude && accommodation?.longitude) {
      setFocusPoint([accommodation.latitude, accommodation.longitude]);
      if (hotelMarkerRef.current) {
        hotelMarkerRef.current.openPopup();
      }
    }
  };

  // Determine map center from items or accommodation if available
  const allItems = days.flatMap((d) => d.items);
  const defaultCenter: [number, number] =
    accommodation?.latitude && accommodation?.longitude
      ? [accommodation.latitude, accommodation.longitude]
      : allItems.length > 0
      ? [allItems[0].attraction.latitude, allItems[0].attraction.longitude]
      : center;

  const createCustomMarker = (dayIndex: number, visitOrder: number) => {
    const color = DAY_COLORS[dayIndex % DAY_COLORS.length];
    return L.divIcon({
      className: 'custom-map-pin',
      html: `
        <div style="
          background-color: ${color};
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 700;
          font-size: 13px;
          border: 2.5px solid white;
          box-shadow: 0 4px 10px rgba(0,0,0,0.3);
          transform: translate(-50%, -50%);
        ">
          ${visitOrder}
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });
  };

  const createAccommodationMarker = () => {
    return L.divIcon({
      className: 'custom-hotel-pin',
      html: `
        <div style="
          background-color: #f59e0b;
          width: 38px;
          height: 38px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 700;
          font-size: 18px;
          border: 3px solid white;
          box-shadow: 0 4px 12px rgba(245, 158, 11, 0.6);
          transform: translate(-50%, -50%);
        ">
          🏨
        </div>
      `,
      iconSize: [38, 38],
      iconAnchor: [19, 19],
    });
  };

  const daysToRender = activeDay
    ? days.filter((d) => d.day_number === activeDay)
    : days;

  // Compute active target bounds for the viewport controller
  const activeCoordinates: [number, number][] = [];
  if (accommodation?.latitude && accommodation?.longitude) {
    activeCoordinates.push([accommodation.latitude, accommodation.longitude]);
  }
  daysToRender.forEach((day) => {
    day.items.forEach((item) => {
      if (item.attraction.latitude && item.attraction.longitude) {
        activeCoordinates.push([item.attraction.latitude, item.attraction.longitude]);
      }
    });
  });

  return (
    <div className="w-full h-full min-h-[420px] rounded-2xl overflow-hidden shadow-inner border border-slate-200 dark:border-neutral-800 relative">
      <MapContainer
        center={defaultCenter}
        zoom={zoom}
        scrollWheelZoom={true}
        className="w-full h-full min-h-[420px]"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapViewportController
          targetBounds={activeCoordinates.length > 0 ? activeCoordinates : null}
          focusPoint={focusPoint}
          defaultCenter={defaultCenter}
          defaultZoom={zoom}
        />

        {/* Accommodation Marker (if selected) */}
        {accommodation && accommodation.latitude && accommodation.longitude && (
          <Marker
            ref={hotelMarkerRef}
            position={[accommodation.latitude, accommodation.longitude]}
            icon={createAccommodationMarker()}
          >
            <Popup className="custom-leaflet-popup">
              <div className="p-1 min-w-[200px]">
                <div className="flex items-center gap-1.5 mb-1 text-xs font-bold uppercase tracking-wider text-amber-600">
                  <Hotel className="w-3.5 h-3.5" />
                  <span>Selected Accommodation (Base)</span>
                </div>
                <h4 className="text-sm font-bold text-slate-900 mb-1">
                  {accommodation.name}
                </h4>
                <p className="text-xs text-slate-500 capitalize mb-2">
                  {accommodation.accommodation_type}
                </p>
                <div className="space-y-1 text-xs text-slate-600 border-t border-slate-100 pt-2">
                  <div className="flex items-center gap-1.5">
                    <DollarSign className="w-3.5 h-3.5 text-slate-400" />
                    <span>₹{accommodation.price_per_night} / night</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-amber-500 font-bold">★</span>
                    <span>{accommodation.rating} / 5.0</span>
                  </div>
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {daysToRender.map((day) => {
          const color = DAY_COLORS[(day.day_number - 1) % DAY_COLORS.length];
          const positions: [number, number][] = [];

          // Prepend hotel coordinates if day route originates from accommodation
          if (
            accommodation &&
            day.start_location_type === 'accommodation' &&
            accommodation.latitude &&
            accommodation.longitude
          ) {
            positions.push([accommodation.latitude, accommodation.longitude]);
          }

          // Add attraction positions
          day.items.forEach((item) => {
            positions.push([item.attraction.latitude, item.attraction.longitude]);
          });

          // Append hotel coordinates if day route returns to accommodation
          if (
            accommodation &&
            day.end_location_type === 'accommodation' &&
            accommodation.latitude &&
            accommodation.longitude
          ) {
            positions.push([accommodation.latitude, accommodation.longitude]);
          }

          return (
            <React.Fragment key={`day-map-${day.day_number}`}>
              {/* Route Polyline */}
              {positions.length > 1 && (
                <Polyline
                  positions={positions}
                  pathOptions={{
                    color,
                    weight: activeDay === day.day_number ? 5 : 3.5,
                    opacity: activeDay && activeDay !== day.day_number ? 0.3 : 0.85,
                    dashArray: '8, 8',
                    lineJoin: 'round',
                  }}
                />
              )}

              {/* Attraction Markers */}
              {day.items.map((item) => (
                <Marker
                  key={`marker-${item.attraction.id}`}
                  position={[item.attraction.latitude, item.attraction.longitude]}
                  icon={createCustomMarker(day.day_number - 1, item.visit_order)}
                >
                  <Popup className="custom-leaflet-popup">
                    <div className="p-1 min-w-[200px]">
                      <div className="flex items-center gap-1.5 mb-1 text-xs font-bold uppercase tracking-wider text-emerald-700">
                        <span
                          className="w-2.5 h-2.5 rounded-full inline-block"
                          style={{ backgroundColor: color }}
                        />
                        Day {day.day_number} &bull; Stop #{item.visit_order}
                      </div>

                      <h4 className="text-sm font-bold text-slate-900 mb-1">
                        {item.attraction.name}
                      </h4>
                      <p className="text-xs text-slate-500 capitalize mb-2">
                        {item.attraction.category}
                      </p>

                      <div className="space-y-1 text-xs text-slate-600 border-t border-slate-100 pt-2">
                        <div className="flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5 text-slate-400" />
                          <span>
                            {item.arrival_time} - {item.departure_time} ({item.visit_duration_hours}h)
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <DollarSign className="w-3.5 h-3.5 text-slate-400" />
                          <span>
                            {item.item_admission_fee && item.item_admission_fee > 0
                              ? `Entry: ₹${item.item_admission_fee}`
                              : item.admission_fee_status === 'unknown' || item.item_admission_fee === null
                              ? 'Fee Unverified'
                              : 'Free Admission'}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Users className="w-3.5 h-3.5 text-slate-400" />
                          <span>Crowd: {item.crowd_level}</span>
                        </div>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </React.Fragment>
          );
        })}
      </MapContainer>

      {/* Interactive Map Legend & Filter Bar */}
      <div
        className="absolute bottom-4 left-4 right-4 sm:right-auto z-[400] bg-white/95 dark:bg-black/95 backdrop-blur-md rounded-2xl p-2.5 sm:p-3 shadow-xl border border-slate-200 dark:border-neutral-800 text-xs flex flex-wrap items-center gap-2 max-w-full"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-1 text-slate-500 dark:text-neutral-400 font-bold pr-1 border-r border-slate-200 dark:border-neutral-800">
          <Layers className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          <span className="hidden sm:inline">Filter:</span>
        </div>

        {/* Show All Control */}
        <button
          type="button"
          onClick={handleShowAll}
          aria-label="Show all itinerary days on map"
          className={`liquid-btn px-2.5 py-1 rounded-xl font-bold transition-all text-xs flex items-center gap-1.5 cursor-pointer ${
            activeDay === null
              ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black shadow-sm ring-2 ring-emerald-500/25'
              : 'bg-slate-100 dark:bg-neutral-900 text-slate-700 dark:text-neutral-300 hover:bg-slate-200 dark:hover:bg-neutral-800 border border-transparent dark:border-neutral-800'
          }`}
        >
          <span>All Days</span>
        </button>

        {/* Clickable Days */}
        {days.map((day) => {
          const color = DAY_COLORS[(day.day_number - 1) % DAY_COLORS.length];
          const isSelected = activeDay === day.day_number;

          return (
            <button
              key={`legend-btn-${day.day_number}`}
              type="button"
              onClick={() => handleDayClick(day.day_number)}
              aria-label={`Filter map to Day ${day.day_number}`}
              className={`liquid-btn px-2.5 py-1 rounded-xl font-semibold transition-all text-xs flex items-center gap-1.5 cursor-pointer ${
                isSelected
                  ? 'bg-slate-900 dark:bg-white text-white dark:text-black shadow-md ring-2 ring-slate-900/30 dark:ring-white/40'
                  : 'bg-slate-100 dark:bg-neutral-900 text-slate-700 dark:text-neutral-300 hover:bg-slate-200 dark:hover:bg-neutral-800 border border-transparent dark:border-neutral-800'
              }`}
            >
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: color }}
              />
              <span>Day {day.day_number}</span>
            </button>
          );
        })}

        {/* Clickable Hotel Base */}
        {accommodation && (
          <button
            type="button"
            onClick={handleHotelClick}
            aria-label={`Focus map on accommodation: ${accommodation.name}`}
            className="liquid-btn px-2.5 py-1 rounded-xl font-semibold transition-all text-xs flex items-center gap-1.5 bg-amber-50 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 hover:bg-amber-100 dark:hover:bg-amber-900/80 border border-amber-200/80 dark:border-amber-800/80 cursor-pointer shadow-xs ml-auto sm:ml-0"
            title={`Focus on hotel: ${accommodation.name}`}
          >
            <span className="w-3.5 h-3.5 rounded-full bg-amber-500 flex items-center justify-center text-[9px] text-white">
              🏨
            </span>
            <span>Hotel Base</span>
          </button>
        )}
      </div>
    </div>
  );
};
