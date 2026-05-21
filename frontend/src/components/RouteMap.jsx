import React from 'react';
import { MapContainer, TileLayer, Popup, Marker, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const ROUTE_COLORS = ['#3b82f6', '#22c55e', '#a855f7', '#f97316', '#ef4444'];


function MapBoundsEffect({ points, mapRef }) {
  React.useEffect(() => {
    if (mapRef.current && points.length > 0) {
      const bounds = L.latLngBounds(points);
      mapRef.current.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [JSON.stringify(points)]);
  return null;
}

export const RouteMap = ({
  origin,
  destination,
  pathCoordinates,  // standard mode
  routes,           // smart mode (K routes)
  activeRouteIndex,
}) => {
  const mapRef = React.useRef();
  // Default: world view — auto-fits to route on first result
  const center = [20.0, 78.0];  // India centre, zooms out for global use

  // Determine which set of points to use for fitting bounds
  const allPoints = React.useMemo(() => {
    if (routes && routes.length > 0 && routes[0].path_coordinates?.length > 0) {
      return routes[0].path_coordinates.map(c => [c.lat, c.lon]);
    }
    if (pathCoordinates?.length > 0) {
      return pathCoordinates.map(c => [c.lat, c.lon]);
    }
    return [];
  }, [routes, pathCoordinates]);

  return (
    <div className="w-full h-full">
      <MapContainer
        center={center}
        zoom={allPoints.length > 0 ? 12 : 5}
        style={{ height: '100%', width: '100%' }}
        whenCreated={map => (mapRef.current = map)}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />

        {/* Auto-fit bounds */}
        {allPoints.length > 0 && (
          <MapBoundsEffect points={allPoints} mapRef={mapRef} />
        )}

        {/* ── Origin marker ── */}
        {origin && (
          <Marker position={[origin.lat, origin.lon]}>
            <Popup>
              <strong>{origin.name}</strong>
              <div className="text-xs text-gray-500">Origin</div>
            </Popup>
          </Marker>
        )}

        {/* ── Destination marker ── */}
        {destination && (
          <Marker position={[destination.lat, destination.lon]}>
            <Popup>
              <strong>{destination.name}</strong>
              <div className="text-xs text-gray-500">Destination</div>
            </Popup>
          </Marker>
        )}

        {/* ── Multi-route polylines ── */}
        {routes && routes.map((route, idx) => {
          const coords = route.path_coordinates?.map(c => [c.lat, c.lon]) || [];
          if (coords.length === 0) return null;
          const isActive = idx === (activeRouteIndex ?? 0);
          const color = ROUTE_COLORS[idx % ROUTE_COLORS.length];
          return (
            <Polyline
              key={route.route_id || idx}
              positions={coords}
              color={color}
              weight={isActive ? 5 : 3}
              opacity={isActive ? 0.9 : 0.45}
            >
              <Popup>
                <strong>#{route.rank} {route.label}</strong>
                <div className="text-xs text-gray-500">
                  {route.eta_min} min · {route.semantic_class}
                </div>
                <div className="text-xs text-gray-400 italic mt-1">{route.explanation}</div>
              </Popup>
            </Polyline>
          );
        })}

        {/* ── Legacy single-route polyline ── */}
        {!routes && pathCoordinates?.length > 0 && (
          <Polyline
            positions={pathCoordinates.map(c => [c.lat, c.lon])}
            color="#3b82f6"
            weight={4}
            opacity={0.85}
          />
        )}

      </MapContainer>
    </div>
  );
};
