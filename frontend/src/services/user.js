import axios from 'axios';

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || 'http://localhost:5050/api') + '/user',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(cfg => {
  const u = localStorage.getItem('mm_user');
  if (u) cfg.headers['X-Username'] = u;
  return cfg;
});

export const userService = {
  history: async (page = 1, pageSize = 20) => {
    try {
      const res = await api.get(`/history?page=${page}&page_size=${pageSize}`);
      return res.data;
    } catch (err) {
      return err.response?.data || { error: 'Failed to load history' };
    }
  },
  historyItem: async (id) => {
    try {
      const res = await api.get(`/history/${id}`);
      return res.data;
    } catch (err) {
      return err.response?.data || { error: 'Failed to load item' };
    }
  },
};
