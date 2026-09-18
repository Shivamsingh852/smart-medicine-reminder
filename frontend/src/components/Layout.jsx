import { useEffect, useRef, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Activity, BarChart3, Bot, CalendarDays, ClipboardList, LogOut, Pill, Settings, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { playMedicineRingtone, unlockRingtone } from '../services/ringtone';

function localDateKey() {
    const now = new Date();
    return `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`;
}

function isDueDuringGracePeriod(scheduledTime) {
    const [hours, minutes] = String(scheduledTime).split(':').map(Number);
    if (!Number.isFinite(hours) || !Number.isFinite(minutes)) return false;
    const now = new Date();
    const due = new Date(now);
    due.setHours(hours, minutes, 0, 0);
    const elapsed = now.getTime() - due.getTime();
    return elapsed >= 0 && elapsed < 5 * 60 * 1000;
}

function ReminderOverlay({ dose, onClose, onMark }) {
    const [saving, setSaving] = useState(false);

    const mark = async (action) => {
        setSaving(true);
        await onMark(dose, action);
        setSaving(false);
    };

    return <div className="reminder-overlay" role="dialog" aria-modal="true" aria-label="Medicine reminder">
        <div className="reminder-card">
            <div className="reminder-ring">♪</div>
            <span className="eyebrow">MEDICINE TIME</span>
            <h2>Time to take your medicine</h2>
            <strong className="reminder-medicine">{dose.medicine_name}</strong>
            <p className="reminder-details">{dose.dosage} {dose.dosage_unit} · scheduled for {dose.scheduled_time}</p>
            <p className="reminder-window">You have 5 minutes to mark this dose.</p>
            <div className="reminder-actions">
                <button className="primary" type="button" disabled={saving} onClick={() => mark('taken')}>Mark taken</button>
                <button className="secondary" type="button" disabled={saving} onClick={() => mark('skipped')}>Skip dose</button>
                <button className="reminder-dismiss" type="button" disabled={saving} onClick={onClose}>Remind me later</button>
            </div>
        </div>
    </div>;
}

export default function Layout() {
    const { user, logout } = useAuth();
    const [reminder, setReminder] = useState(null);
    const alertedDoses = useRef(new Set());
    const links = user.role === 'relative' ? [{ to: '/relative', label: 'Overview', icon: Activity }] : [{ to: '/', label: 'Dashboard', icon: Activity }, { to: '/medicines', label: 'Medicines', icon: Pill }, { to: '/schedule', label: 'Schedule', icon: CalendarDays }, { to: '/history', label: 'History', icon: ClipboardList }, { to: '/analytics', label: 'Analytics', icon: BarChart3 }, { to: '/prediction', label: 'AI Prediction', icon: Sparkles }, { to: '/chatbot', label: 'Ask assistant', icon: Bot }];

    useEffect(() => {
        if (user.role !== 'patient') return undefined;
        const unlock = () => {
            unlockRingtone();
            if ('Notification' in window && Notification.permission === 'default') Notification.requestPermission();
        };
        window.addEventListener('pointerdown', unlock, { once: true });
        return () => window.removeEventListener('pointerdown', unlock);
    }, [user.role]);

    useEffect(() => {
        if (user.role !== 'patient') return undefined;
        let active = true;
        const checkReminders = async () => {
            try {
                const { data } = await api.get('/doses/today');
                const dose = data.doses.find((item) => item.status === 'upcoming' && isDueDuringGracePeriod(item.scheduled_time));
                if (!active || !dose) return;
                const key = `${localDateKey()}-${dose.schedule_id}`;
                if (alertedDoses.current.has(key)) return;
                alertedDoses.current.add(key);
                setReminder(dose);
                playMedicineRingtone();
                if ('Notification' in window && Notification.permission === 'granted' && document.hidden) {
                    new Notification(`Medicine time: ${dose.medicine_name}`, { body: `${dose.dosage} ${dose.dosage_unit} · scheduled for ${dose.scheduled_time}` });
                }
            } catch {
                // Reminder polling should not interrupt normal navigation.
            }
        };
        checkReminders();
        const timer = window.setInterval(checkReminders, 10000);
        return () => { active = false; window.clearInterval(timer); };
    }, [user.role]);

    const markReminder = async (dose, action) => {
        try {
            await api.post(`/doses/${dose.schedule_id}/${action}`);
            setReminder(null);
        } catch {
            setReminder(null);
        }
    };

    return <div className="app-shell"><aside className="sidebar"><div className="brand"><span className="brand-mark"><Pill size={19} /></span><span>med<span className="accent">mate</span></span></div><div className="profile-mini"><div className="avatar">{user.full_name?.slice(0, 1)}</div><div><strong>{user.full_name}</strong><small>{user.role}</small></div></div><nav>{links.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} className={({ isActive }) => isActive ? 'active' : ''}><Icon size={17} />{label}</NavLink>)}</nav><div className="sidebar-bottom"><NavLink to="/profile"><Settings size={17} />Profile & settings</NavLink><button className="nav-button" onClick={logout}><LogOut size={17} />Sign out</button></div></aside><main className="main-content"><header className="topbar"><div><span className="eyebrow">PERSONAL CARE HUB</span><h1>{user.role === 'relative' ? 'Care circle' : 'Your care, in rhythm'}</h1></div><div className="header-date">{new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}</div></header><Outlet /></main>{reminder && <ReminderOverlay dose={reminder} onClose={() => setReminder(null)} onMark={markReminder} />}</div>;
}
