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

const ScoreBar = ({ label, value }) => (
  <div className="flex items-center gap-2 text-xs">
    <span className="w-20 text-gray-400 flex-shrink-0 capitalize">{label}</span>
    <div className="flex-1 bg-gray-100 rounded-full h-1.5">
      <div
        className="bg-blue-400 h-1.5 rounded-full transition-all"
        style={{ width: `${Math.round((value || 0) * 100)}%` }}
      />
    </div>
    <span className="w-8 text-right text-gray-500">{Math.round((value || 0) * 100)}%</span>
  </div>
);

export const RouteDetails = ({ route }) => {
  if (!route) return null;

  const isSmartRoute = route.route_type === 'smart';
  const astarMs      = route.algorithm_time_ms ?? Math.round((route.calculation_time_s ?? 0) * 1000);
  const nodesExpl    = route.nodes_explored;

  // Constraint pills from extracted priorities/avoid/prefer
  const priorities = route.constraints?.priorities ?? [];
  const avoidList  = route.constraints?.avoid ?? [];
  const preferList = route.constraints?.prefer ?? [];

  const scoreKeys = ['speed', 'safety', 'scenic', 'comfort', 'fuel_access'];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 space-y-4">

      {/* Smart route label badge */}
      {isSmartRoute && route.label && (
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 bg-blue-50 text-blue-600 text-xs font-semibold px-3 py-1.5 rounded-full border border-blue-100">
            <Zap className="w-3 h-3" />
            {route.label}
          </span>
        </div>
      )}

      <div>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Route Result
        </h2>

        <div className="grid grid-cols-2 gap-3">
          <Stat icon={<Navigation className="w-4 h-4 text-blue-500" />}
                label="Distance" color="bg-blue-50"
                value={`${route.distance_km} km`}
                sub={`${route.distance_m?.toLocaleString()} m`} />

          <Stat icon={<Clock className="w-4 h-4 text-green-500" />}
                label="Est. travel time" color="bg-green-50"
                value={`${route.estimated_time_min} min`}
                sub={`by ${route.vehicle_type}`} />

          {!isSmartRoute && (
            <>
              <Stat icon={<Zap className="w-4 h-4 text-orange-500" />}
                    label="A* time" color="bg-orange-50"
                    value={`${astarMs} ms`}
                    sub="custom implementation" />

              <Stat icon={<Search className="w-4 h-4 text-purple-500" />}
                    label="Nodes explored" color="bg-purple-50"
                    value={nodesExpl?.toLocaleString() ?? route.path_nodes}
                    sub="A* nodes expanded" />
            </>
          )}
        </div>
      </div>

      {/* Cache badge */}
      {route.cache_hit !== undefined && !isSmartRoute && (
        <div className={`flex items-center gap-1.5 text-xs px-3 py-2 rounded-lg ${
          route.cache_hit
            ? 'bg-green-50 text-green-700 border border-green-100'
            : 'bg-gray-50 text-gray-500 border border-gray-100'
        }`}>
          <Database className="w-3.5 h-3.5" />
          {route.cache_hit ? 'Served from Redis cache' : 'Computed · stored in Redis'}
        </div>
      )}

      {/* AI explanation */}
      {isSmartRoute && route.explanation && (
        <div className="bg-blue-50/60 border border-blue-100 rounded-lg px-3 py-2.5 text-xs text-blue-800 leading-relaxed">
          {route.explanation}
        </div>
      )}

      {/* Detected constraints */}
      {isSmartRoute && (priorities.length > 0 || avoidList.length > 0 || preferList.length > 0) && (
        <div>
          <p className="text-xs font-medium text-gray-400 mb-2">Detected preferences</p>
          <div className="flex flex-wrap gap-1.5">
            {priorities.map(p => (
              <span key={p} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full capitalize">
                {p}
              </span>
            ))}
            {avoidList.map(a => (
              <span key={a} className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded-full capitalize">
                avoid {a.replace(/_/g, ' ')}
              </span>
            ))}
            {preferList.map(p => (
              <span key={p} className="text-xs bg-green-50 text-green-600 px-2 py-0.5 rounded-full capitalize">
                prefer {p.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Score bars for smart route */}
      {isSmartRoute && route.scores && (
        <div>
          <p className="text-xs font-medium text-gray-400 mb-2">Route scores</p>
          <div className="space-y-2">
            {scoreKeys.map(k => (
              <ScoreBar key={k} label={k.replace('_', ' ')} value={route.scores[k]} />
            ))}
          </div>
        </div>
      )}

      <div className="border-t pt-3.5 space-y-2.5 text-sm">
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
          <span className="font-medium text-gray-800 capitalize">
            {isSmartRoute ? route.label : route.route_type?.replace('_', ' ')}
          </span>
        </div>
        {isSmartRoute && route.cost_formula && (
          <div className="flex justify-between items-start">
            <span className="text-gray-400 flex-shrink-0">Cost weights</span>
            <span className="font-mono text-xs text-gray-500 text-right max-w-[60%] leading-relaxed">
              {route.cost_formula}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
