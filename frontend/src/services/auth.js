import axios from 'axios';

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || 'http://localhost:5050/api') + '/auth',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

export const authService = {
  register: async (username, password) => {
    try {
      const res = await api.post('/register', { username, password, role: 'user' });
      return res.data;
    } catch (err) {
      return err.response?.data || { error: 'Registration failed' };
    }
  },
  login: async (username, password) => {
    try {
      const res = await api.post('/login', { username, password });
      if (res.data?.success) localStorage.setItem('mm_user', username);
      return res.data;
    } catch (err) {
      return err.response?.data || { error: 'Invalid credentials' };
    }
  },
  logout: async () => {
    try {
      localStorage.removeItem('mm_user');
      const res = await api.post('/logout');
      return res.data;
    } catch (err) {
      localStorage.removeItem('mm_user');
      return { success: false };
    }
  },
  me: async () => {
    try {
      const res = await api.get('/me');
      return res.data;
    } catch {
      return { logged_in: false };
    }
  },
};
