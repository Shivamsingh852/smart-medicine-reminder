import { useEffect, useState } from 'react';
import { ArrowUpRight, Check, Clock3, Plus, SkipForward, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../services/api';

function statusClass(status) {
  return status === 'taken'
    ? 'status-taken'
    : status === 'skipped'
    ? 'status-skipped'
    : status === 'missed'
    ? 'status-missed'
    : 'status-upcoming';
}

export default function Dashboard() {
  const [doses, setDoses] = useState([]);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const [doseRes, analyticsRes] = await Promise.all([
        api.get('/doses/today'),
        api.get('/analytics/weekly')
      ]);
      setDoses(doseRes.data.doses);
      setStats(analyticsRes.data.summary);
    } catch (err) {
      setError(err.response?.data?.message || 'Could not load your dashboard.');
    }
  };

  useEffect(() => {
    load();
  }, []);


  const mark = async (dose, action) => {
    try {
      await api.post(`/doses/${dose.schedule_id}/${action}`);
      load();
    } catch {
      setError('We could not update that dose. Please try again.');
    }
  };

  const next = doses.find((dose) => dose.status === 'upcoming');

  return (
    <section className="page">
      <div className="welcome-row">
        <div>
          <span className="eyebrow">TODAY'S ROUTINE</span>
          <h2>
            Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'}.
          </h2>
          <p className="muted">A steady routine is a powerful kind of self-care.</p>
        </div>
        <Link className="primary" to="/medicines">
          <Plus size={17} /> Add medicine
        </Link>
      </div>

      {error && <div className="error-box">{error}</div>}

      <div className="metric-grid">
        <div className="metric-card dark">
          <span>Next reminder</span>
          <strong>{next ? next.scheduled_time : 'All clear'}</strong>
          <small>
            {next ? `${next.medicine_name} · ${next.dosage} ${next.dosage_unit}` : 'No upcoming doses today'}
          </small>
          <Clock3 className="metric-icon" />
        </div>
        <div className="metric-card">
          <span>Weekly adherence</span>
          <strong>{stats?.adherence ?? 0}%</strong>
          <small>{stats?.taken ?? 0} of {stats?.total ?? 0} logged doses taken</small>
          <div className="progress"><i style={{ width: `${stats?.adherence ?? 0}%` }} /></div>
        </div>
        <div className="metric-card">
          <span>Care status</span>
          <strong className="good">On track</strong>
          <small>Keep your reminders close</small>
          <Sparkles className="metric-icon accent-icon" />
        </div>
      </div>

      <div className="section-heading">
        <div>
          <span className="eyebrow">DOSE CHECK-IN</span>
          <h3>Today's medicines</h3>
        </div>
        <Link to="/schedule" className="text-link">
          View schedule <ArrowUpRight size={15} />
        </Link>
      </div>

      <div className="dose-list">
        {doses.length ? (
          doses.map((dose) => (
            <div className="dose-row" key={`${dose.medicine_id}-${dose.schedule_id}`}>
              <div className={`dose-badge ${statusClass(dose.status)}`}>
                <Clock3 size={16} />
              </div>
              <div className="dose-info">
                <strong>{dose.medicine_name}</strong>
                <span>
                  {dose.dosage} {dose.dosage_unit} · {dose.scheduled_time}
                </span>
              </div>
              <span className={`pill ${statusClass(dose.status)}`}>{dose.status}</span>
              {dose.status === 'upcoming' && (
                <div className="dose-actions">
                  <button className="icon-action taken" title="Mark taken" onClick={() => mark(dose, 'taken')}>
                    <Check size={16} />
                  </button>
                  <button className="icon-action skipped" title="Skip dose" onClick={() => mark(dose, 'skipped')}>
                    <SkipForward size={16} />
                  </button>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="empty-state">No medicines scheduled yet. Add your first medicine to begin.</div>
        )}
      </div>

      <div className="disclaimer">
        <Sparkles size={16} />
        <span>
          <strong>AI support, not medical advice.</strong> Predictions use your reminder history to suggest helpful support. Always follow your clinician's prescription.
        </span>
      </div>
    </section>
  );
}

