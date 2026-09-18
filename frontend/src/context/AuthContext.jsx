import { createContext, useContext, useState } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem('smr_user') || 'null'));
  const login = async (credentials) => { const { data } = await api.post('/auth/login', credentials); localStorage.setItem('smr_token', data.token); localStorage.setItem('smr_user', JSON.stringify(data.user)); setUser(data.user); return data.user; };
  const register = async (payload) => { const { data } = await api.post('/auth/register', payload); localStorage.setItem('smr_token', data.token); localStorage.setItem('smr_user', JSON.stringify(data.user)); setUser(data.user); return data.user; };
  const logout = () => { localStorage.clear(); setUser(null); };
  return <AuthContext.Provider value={{ user, login, register, logout }}>{children}</AuthContext.Provider>;
}
export const useAuth = () => useContext(AuthContext);
