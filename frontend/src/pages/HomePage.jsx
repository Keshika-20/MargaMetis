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
      const res = await routeService.calculateRoute(
        origin, destination, null, null, routeType, undefined, vehicleType
      );
      if (res.success) setRoute(res);
      else setError(res.error || 'Failed to calculate route');
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
            onOriginChange={setOrigin} onDestinationChange={setDestination}
            onRouteTypeChange={setRouteType} onVehicleTypeChange={setVehicleType}
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
