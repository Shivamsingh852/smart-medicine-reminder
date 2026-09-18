import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import Medicines from './pages/Medicines';
import Schedule from './pages/Schedule';
import History from './pages/History';
import Analytics from './pages/Analytics';
import Prediction from './pages/Prediction';
import Chatbot from './pages/Chatbot';
import Profile from './pages/Profile';
import RelativeDashboard from './pages/RelativeDashboard';

export default function App() { const { user } = useAuth(); return <Routes><Route path="/login" element={<AuthPage mode="login" />} /><Route path="/register" element={<AuthPage mode="register" />} /><Route path="*" element={<ProtectedRoute><Layout /></ProtectedRoute>}><Route index element={user?.role === 'relative' ? <Navigate to="/relative" replace /> : <Dashboard />} /><Route path="relative" element={<RelativeDashboard />} /><Route path="medicines" element={<Medicines />} /><Route path="schedule" element={<Schedule />} /><Route path="history" element={<History />} /><Route path="analytics" element={<Analytics />} /><Route path="prediction" element={<Prediction />} /><Route path="chatbot" element={<Chatbot />} /><Route path="profile" element={<Profile />} /></Route></Routes>; }
