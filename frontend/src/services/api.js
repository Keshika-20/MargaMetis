import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5050/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(cfg => {
  const u = localStorage.getItem('mm_user');
  if (u) cfg.headers['X-Username'] = u;
  return cfg;
});

export const routeService = {
  /** Standard mode: fixed route type + vehicle */
  calculateRoute: async (
    origin, destination,
    originCoords = null, destCoords = null,
    routeType = 'shortest',
    timeOfDay = new Date().getHours(),
    vehicleType = 'car'
  ) => {
    const res = await api.post('/route/calculate', {
      origin, destination,
      origin_coords: originCoords,
      dest_coords: destCoords,
      route_type: routeType,
      time_of_day: timeOfDay,
      vehicle_type: vehicleType,
    });
    return res.data;
  },

  /** Smart mode: natural-language query → K ranked routes */
  smartRoute: async ({ query, origin, destination, vehicle_type, time_of_day }) => {
    const res = await api.post('/route/smart', {
      query: query || '',
      origin,
      destination,
      vehicle_type,
      time_of_day,
    });
    return res.data;
  },

  /** Benchmark: time all 4 algorithms side-by-side */
  benchmark: async (origin, destination) => {
    const res = await api.post('/route/benchmark', { origin, destination });
    return res.data;
  },

  geocodeLocation: async (location) => {
    const res = await api.post('/route/geocode', { location });
    return res.data;
  },

  healthCheck: async () => {
    const res = await api.get('/health');
    return res.data;
  },
};

export default api;
