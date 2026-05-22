import React, { useState, useEffect } from 'react';
import { SearchBar }    from '../components/SearchBar';
import { RouteMap }     from '../components/RouteMap';
import { RouteDetails } from '../components/RouteDetails';
import { ErrorAlert }   from '../components/ErrorAlert';
import { routeService } from '../services/api';
import { Navigation2 }  from 'lucide-react';

export const HomePage = () => {
  const [origin, setOrigin]           = useState('');
  const [destination, setDestination] = useState('');
  const [routeType, setRouteType]     = useState('shortest');
  const [vehicleType, setVehicleType] = useState('car');
  const [nlQuery, setNlQuery]         = useState('');
  const [route, setRoute]             = useState(null);
  const [isLoading, setIsLoading]     = useState(false);
  const [error, setError]             = useState(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem('selectedRoute');
      if (stored) {
        const p = JSON.parse(stored);
        if (p?.success) setRoute(p);
        localStorage.removeItem('selectedRoute');
      }
    } catch {}
  }, []);

  const handleSearch = async () => {
    if (!origin.trim() || !destination.trim()) {
      setError('Please enter both origin and destination');
      return;
    }
    setIsLoading(true);
    setError(null);
    setRoute(null);

    try {
      if (nlQuery.trim()) {
        // NL pipeline — Groq extracts constraints, A* runs with dynamic cost fn
        const res = await routeService.smartRoute({
          query: nlQuery,
          origin,
          destination,
          vehicle_type: vehicleType,
          time_of_day: new Date().getHours(),
        });

        if (!res.success || !res.routes?.length) {
          setError(res.error || 'No routes found');
          return;
        }

        const best = res.routes[0];
        setRoute({
          success: true,
          cache_hit: false,
          distance_km: parseFloat((best.distance_m / 1000).toFixed(2)),
          distance_m: best.distance_m,
          estimated_time_min: best.eta_min,
          algorithm_time_ms: null,
          nodes_explored: null,
          path_nodes: best.path_coordinates?.length,
          origin: res.origin,
          destination: res.destination,
          path_coordinates: best.path_coordinates,
          route_type: 'smart',
          vehicle_type: vehicleType,
          // smart-specific fields
          label: best.label,
          explanation: best.explanation,
          scores: best.score,
          constraints: res.constraints,
          cost_formula: res.cost_formula,
          calculation_time_s: res.calculation_time_s,
        });
      } else {
        const res = await routeService.calculateRoute(
          origin, destination, null, null, routeType, undefined, vehicleType
        );
        if (res.success) setRoute(res);
        else setError(res.error || 'Failed to calculate route');
      }
    } catch (err) {
      setError(err?.error || err?.message || 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full">

      {/* Sidebar */}
      <div className="w-80 flex-shrink-0 bg-white border-r border-gray-100 flex flex-col overflow-hidden shadow-sm z-10">

        <div className="p-4 border-b border-gray-100">
          <SearchBar
            origin={origin} destination={destination}
            routeType={routeType} vehicleType={vehicleType}
            nlQuery={nlQuery}
            onOriginChange={setOrigin} onDestinationChange={setDestination}
            onRouteTypeChange={setRouteType} onVehicleTypeChange={setVehicleType}
            onNlQueryChange={setNlQuery}
            onSearch={handleSearch} isLoading={isLoading}
          />
          {error && (
            <div className="mt-3">
              <ErrorAlert error={error} onClose={() => setError(null)} />
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto">
          {route ? (
            <div className="p-4">
              <RouteDetails route={route} />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-48 text-center px-6">
              <div className="w-12 h-12 rounded-full bg-gray-50 flex items-center justify-center mb-3">
                <Navigation2 className="w-5 h-5 text-gray-300" />
              </div>
              <p className="text-sm text-gray-400">Enter a route to get started</p>
            </div>
          )}
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        <RouteMap
          origin={route?.origin}
          destination={route?.destination}
          pathCoordinates={route?.path_coordinates}
        />
      </div>

    </div>
  );
};
