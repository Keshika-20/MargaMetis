import React, { useState } from 'react';
import { X, Loader, Navigation2 } from 'lucide-react';
import { authService } from '../services/auth';

export const AuthModal = ({ open, onClose, onSuccess }) => {
  const [tab, setTab]           = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState(null);
  const [loading, setLoading]   = useState(false);
  const [registered, setRegistered] = useState(false);

  if (!open) return null;

  const reset = () => { setUsername(''); setPassword(''); setError(null); setRegistered(false); };
  const switchTab = t => { setTab(t); reset(); };

  const handleLogin = async e => {
    e.preventDefault();
    setLoading(true); setError(null);
    const res = await authService.login(username, password);
    setLoading(false);
    if (res.success) { onSuccess({ username, role: res.role }); reset(); }
    else setError(res.error || 'Invalid credentials');
  };

  const handleRegister = async e => {
    e.preventDefault();
    if (password.length < 6) { setError('Password must be at least 6 characters'); return; }
    setLoading(true); setError(null);
    const res = await authService.register(username, password);
    setLoading(false);
    if (res.success) { setRegistered(true); setTimeout(() => switchTab('login'), 1500); }
    else setError(res.error || 'Registration failed');
  };

  const inputCls = "w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-100 transition";

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 overflow-hidden">

        <div className="flex items-center justify-between px-5 pt-5 pb-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-blue-600 rounded-md flex items-center justify-center">
              <Navigation2 className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-gray-900">MargaMetis</span>
          </div>
          <button onClick={() => { onClose(); reset(); }}
            className="w-7 h-7 flex items-center justify-center rounded-full hover:bg-gray-100 transition">
            <X className="w-4 h-4 text-gray-400" />
          </button>
        </div>

        <div className="flex mx-5 bg-gray-100 rounded-lg p-0.5 mb-5">
          {['login', 'register'].map(t => (
            <button key={t} onClick={() => switchTab(t)}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition capitalize ${
                tab === t ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'
              }`}>
              {t === 'login' ? 'Sign in' : 'Create account'}
            </button>
          ))}
        </div>

        <div className="px-5 pb-5">
          {registered ? (
            <div className="text-center py-4">
              <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-green-600 text-xl">✓</span>
              </div>
              <p className="text-sm font-medium text-gray-900">Account created!</p>
              <p className="text-xs text-gray-500 mt-1">Redirecting to sign in...</p>
            </div>
          ) : tab === 'login' ? (
            <form onSubmit={handleLogin} className="space-y-3">
              <input type="text" placeholder="Username" value={username}
                onChange={e => setUsername(e.target.value)} required className={inputCls} />
              <input type="password" placeholder="Password" value={password}
                onChange={e => setPassword(e.target.value)} required className={inputCls} />
              {error && <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>}
              <button type="submit" disabled={loading || !username || !password}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700
                  disabled:bg-gray-100 disabled:text-gray-400 text-white font-medium py-2.5 rounded-lg transition text-sm">
                {loading ? <><Loader className="w-4 h-4 animate-spin" />Signing in...</> : 'Sign in'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-3">
              <input type="text" placeholder="Username" value={username}
                onChange={e => setUsername(e.target.value)} required className={inputCls} />
              <input type="password" placeholder="Password (min 6 characters)" value={password}
                onChange={e => setPassword(e.target.value)} required className={inputCls} />
              {error && <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>}
              <button type="submit" disabled={loading || !username || !password}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700
                  disabled:bg-gray-100 disabled:text-gray-400 text-white font-medium py-2.5 rounded-lg transition text-sm">
                {loading ? <><Loader className="w-4 h-4 animate-spin" />Creating account...</> : 'Create account'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
