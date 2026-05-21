import React from 'react';
import { Clock, Navigation, Zap, Search, Database } from 'lucide-react';

const Stat = ({ icon, label, value, sub, color }) => (
  <div className={`rounded-xl p-4 ${color}`}>
    <div className="flex items-center gap-1.5 mb-2">
      {icon}
      <span className="text-xs font-medium text-gray-500">{label}</span>
    </div>
    <p className="text-2xl font-bold text-gray-900">{value}</p>
    {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
  </div>
);

export const RouteDetails = ({ route }) => {
  if (!route) return null;

  const astarMs   = route.algorithm_time_ms ?? Math.round((route.calculation_time_s ?? 0) * 1000);
  const nodesExpl = route.nodes_explored;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
        Route Result
      </h2>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <Stat icon={<Navigation className="w-4 h-4 text-blue-500" />}
              label="Distance" color="bg-blue-50"
              value={`${route.distance_km} km`}
              sub={`${route.distance_m?.toLocaleString()} m`} />

        <Stat icon={<Clock className="w-4 h-4 text-green-500" />}
              label="Est. travel time" color="bg-green-50"
              value={`${route.estimated_time_min} min`}
              sub={`by ${route.vehicle_type}`} />

        <Stat icon={<Zap className="w-4 h-4 text-orange-500" />}
              label="A* time" color="bg-orange-50"
              value={`${astarMs} ms`}
              sub="custom implementation" />

        <Stat icon={<Search className="w-4 h-4 text-purple-500" />}
              label="Nodes explored" color="bg-purple-50"
              value={nodesExpl?.toLocaleString() ?? route.path_nodes}
              sub="A* nodes expanded" />
      </div>

      {/* Cache badge */}
      {route.cache_hit !== undefined && (
        <div className={`flex items-center gap-1.5 text-xs px-3 py-2 rounded-lg mb-4 ${
          route.cache_hit
            ? 'bg-green-50 text-green-700 border border-green-100'
            : 'bg-gray-50 text-gray-500 border border-gray-100'
        }`}>
          <Database className="w-3.5 h-3.5" />
          {route.cache_hit ? 'Served from Redis cache' : 'Computed · stored in Redis'}
        </div>
      )}

      <div className="border-t pt-4 space-y-2.5 text-sm">
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Origin</span>
          <span className="font-medium text-gray-800 text-right max-w-[55%] truncate">{route.origin?.name}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Destination</span>
          <span className="font-medium text-gray-800 text-right max-w-[55%] truncate">{route.destination?.name}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Optimised for</span>
          <span className="font-medium text-gray-800 capitalize">{route.route_type?.replace('_', ' ')}</span>
        </div>
      </div>
    </div>
  );
};
