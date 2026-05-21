import React, { useEffect, useState } from 'react';
import { userService } from '../services/user';
import { Clock, Navigation2, MapPin, ArrowRight, Loader } from 'lucide-react';

const ROUTE_TYPE_LABEL = {
  shortest:   'Shortest',
  fuel:       'Fuel efficient',
  green:      'Eco / Green',
  avoid_main: 'Avoid main roads',
};

export const UserDashboard = () => {
  const [history, setHistory]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);

  useEffect(() => {
    (async () => {
      const res = await userService.history(1, 50);
      if (res?.success) setHistory(res.items || []);
      else setError(res?.error || 'Could not load history');
      setLoading(false);
    })();
  }, []);

  const viewOnMap = async id => {
    const res = await userService.historyItem(id);
    if (res?.success) {
      localStorage.setItem('selectedRoute', JSON.stringify(res.result));
      window.location.href = '/';
    }
  };

  return (
    <div className="min-h-full bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">

        <div className="mb-6">
          <h1 className="text-xl font-semibold text-gray-900">Route History</h1>
          <p className="text-sm text-gray-500 mt-1">Your previous route searches</p>
        </div>

        {loading && (
          <div className="flex items-center justify-center h-40 text-gray-400">
            <Loader className="w-5 h-5 animate-spin mr-2" /> Loading...
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-100 rounded-xl p-4 text-sm text-red-600">
            {error}
          </div>
        )}

        {!loading && !error && history.length === 0 && (
          <div className="bg-white border border-gray-100 rounded-xl p-12 text-center">
            <Navigation2 className="w-8 h-8 text-gray-200 mx-auto mb-3" />
            <p className="text-sm text-gray-400">No routes yet — search for a route on the map</p>
          </div>
        )}

        {!loading && history.length > 0 && (
          <div className="space-y-2">
            {history.map(item => (
              <div key={item.id}
                className="bg-white border border-gray-100 rounded-xl px-5 py-4 flex items-center gap-4 hover:shadow-sm transition">

                {/* Origin → Destination */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 text-sm text-gray-800 font-medium truncate">
                    <MapPin className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                    <span className="truncate">{item.origin}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-gray-300 flex-shrink-0" />
                    <span className="truncate">{item.destination}</span>
                  </div>
                  <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-400">
                    <span>{ROUTE_TYPE_LABEL[item.route_type] || item.route_type}</span>
                    <span>·</span>
                    <span className="capitalize">{item.vehicle_type}</span>
                    <span>·</span>
                    <span>{(item.distance_m / 1000).toFixed(1)} km</span>
                    {item.estimated_time_min && (
                      <>
                        <span>·</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {Math.round(item.estimated_time_min)} min
                        </span>
                      </>
                    )}
                  </div>
                </div>

                {/* Date */}
                <span className="text-xs text-gray-300 flex-shrink-0 hidden sm:block">
                  {new Date(item.created_at).toLocaleDateString()}
                </span>

                {/* Action */}
                <button onClick={() => viewOnMap(item.id)}
                  className="flex-shrink-0 text-xs bg-blue-50 hover:bg-blue-100 text-blue-600 font-medium
                    px-3 py-1.5 rounded-lg transition">
                  View on map
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
