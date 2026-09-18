import axios from 'axios';

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api' });

api.interceptors.request.use((config) => { 
  const token = localStorage.getItem('smr_token'); 
  if (token) config.headers.Authorization = `Bearer ${token}`; 
  return config; 
});

api.interceptors.response.use(
  (response) => response, 
  (error) => { 
    if (error.response?.status === 401) {
      localStorage.removeItem('smr_token'); 
      localStorage.removeItem('smr_user');
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
        window.location.href = '/login';
      }
    } 
    return Promise.reject(error); 
  }
);

export default api;
