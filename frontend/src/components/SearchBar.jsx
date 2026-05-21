import React from 'react';
import { MapPin, Loader, Navigation2 } from 'lucide-react';

const Field = ({ label, value, onChange, placeholder }) => (
  <div>
    <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
    <div className="relative">
      <MapPin className="absolute left-3 top-2.5 w-3.5 h-3.5 text-gray-300 pointer-events-none" />
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg
          focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-100
          transition placeholder-gray-300 text-gray-800"
      />
    </div>
  </div>
);

export const SearchBar = ({
  origin, destination, routeType, vehicleType,
  onOriginChange, onDestinationChange, onRouteTypeChange, onVehicleTypeChange,
  onSearch, isLoading,
}) => {
  const handleSubmit = e => { e.preventDefault(); onSearch(); };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <Field label="From" value={origin}      onChange={onOriginChange}
             placeholder="e.g. T Nagar, Chennai" />
      <Field label="To"   value={destination} onChange={onDestinationChange}
             placeholder="e.g. Marina Beach, Chennai" />

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Optimise for</label>
          <select value={routeType} onChange={e => onRouteTypeChange(e.target.value)}
            className="w-full px-2.5 py-2 text-sm border border-gray-200 rounded-lg
              focus:outline-none focus:border-blue-400 transition text-gray-700 bg-white">
            <option value="shortest">Shortest distance</option>
            <option value="fuel">Fuel efficient</option>
            <option value="green">Eco / Green</option>
            <option value="avoid_main">Avoid main roads</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Vehicle</label>
          <select value={vehicleType} onChange={e => onVehicleTypeChange(e.target.value)}
            className="w-full px-2.5 py-2 text-sm border border-gray-200 rounded-lg
              focus:outline-none focus:border-blue-400 transition text-gray-700 bg-white">
            <option value="car">Car</option>
            <option value="bike">Bike</option>
            <option value="bus">Bus</option>
            <option value="truck">Truck</option>
            <option value="auto">Auto</option>
          </select>
        </div>
      </div>

      <button type="submit" disabled={isLoading || !origin || !destination}
        className="w-full flex items-center justify-center gap-2 bg-blue-600
          hover:bg-blue-700 disabled:bg-gray-100 disabled:text-gray-400
          text-white font-medium py-2.5 rounded-lg transition text-sm">
        {isLoading
          ? <><Loader className="w-4 h-4 animate-spin" />Finding route...</>
          : <><Navigation2 className="w-4 h-4" />Get Route</>}
      </button>
    </form>
  );
};
