import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { OptimizedDaySchedule } from '../../types';
import { Clock, MapPin, DollarSign, Users } from 'lucide-react';

interface MapComponentProps {
  days: OptimizedDaySchedule[];
  selectedDayNumber?: number;
  center?: [number, number];
  zoom?: number;
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

export const MapComponent: React.FC<MapComponentProps> = ({
  days,
  selectedDayNumber,
  center = [15.335, 76.46],
  zoom = 13,
}) => {
  // Determine map center from items if available
  const allItems = days.flatMap((d) => d.items);
  const defaultCenter: [number, number] =
    allItems.length > 0
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

  const daysToRender = selectedDayNumber
    ? days.filter((d) => d.day_number === selectedDayNumber)
    : days;

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

        {daysToRender.map((day, dayIdx) => {
          const color = DAY_COLORS[(day.day_number - 1) % DAY_COLORS.length];
          const positions: [number, number][] = day.items.map((item) => [
            item.attraction.latitude,
            item.attraction.longitude,
          ]);

          return (
            <React.Fragment key={`day-map-${day.day_number}`}>
              {/* Route Polyline */}
              {positions.length > 1 && (
                <Polyline
                  positions={positions}
                  pathOptions={{
                    color,
                    weight: 4,
                    opacity: 0.8,
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
                            {item.item_admission_fee > 0
                              ? `Entry: ₹${item.item_admission_fee}`
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

      {/* Map Legend */}
      <div className="absolute bottom-4 left-4 z-[400] bg-white/95 dark:bg-black/95 backdrop-blur-md rounded-xl p-3 shadow-lg border border-slate-200 dark:border-neutral-800 text-xs flex flex-wrap gap-3">
        <span className="font-bold text-slate-700 dark:text-neutral-300 self-center">Day Legend:</span>
        {days.map((day) => {
          const color = DAY_COLORS[(day.day_number - 1) % DAY_COLORS.length];
          return (
            <div key={`legend-${day.day_number}`} className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
              <span className="font-medium text-slate-700 dark:text-neutral-200">Day {day.day_number}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
