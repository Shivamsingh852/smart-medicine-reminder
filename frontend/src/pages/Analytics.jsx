import { useEffect, useState } from 'react';
import { BarChart3, CheckCircle2, CircleAlert, SkipForward } from 'lucide-react';
import api from '../services/api';

export default function Analytics() {
  const [period, setPeriod] = useState('weekly');
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    api.get(`/analytics/${period}`).then(({ data }) => setSummary(data.summary));
  }, [period]);

  return (
    <section className="page">
      <div className="welcome-row">
        <div>
          <span className="eyebrow">PATTERNS, NOT PRESSURE</span>
          <h2>Adherence analytics</h2>
          <p className="muted">See what your routine is telling you.</p>
        </div>
        <div className="segmented">
          <button className={period === 'weekly' ? 'selected' : ''} onClick={() => setPeriod('weekly')}>7 days</button>
          <button className={period === 'monthly' ? 'selected' : ''} onClick={() => setPeriod('monthly')}>30 days</button>
        </div>
      </div>

      <div className="analytics-hero">
        <div>
          <span>Current adherence</span>
          <strong>{summary?.adherence ?? 0}%</strong>
          <div className="progress light-progress"><i style={{ width: `${summary?.adherence ?? 0}%` }} /></div>
        </div>
        <BarChart3 size={58} strokeWidth={1.2} />
      </div>

      <div className="metric-grid four">
        <div className="metric-card">
          <CheckCircle2 className="stat-icon green" />
          <span>Taken</span>
          <strong>{summary?.taken ?? 0}</strong>
        </div>
        <div className="metric-card">
          <CircleAlert className="stat-icon red" />
          <span>Missed</span>
          <strong>{summary?.missed ?? 0}</strong>
        </div>
        <div className="metric-card">
          <SkipForward className="stat-icon amber" />
          <span>Skipped</span>
          <strong>{summary?.skipped ?? 0}</strong>
        </div>
        <div className="metric-card">
          <span>Total logged</span>
          <strong>{summary?.total ?? 0}</strong>
          <small>dose check-ins</small>
        </div>
      </div>

      <div className="disclaimer">
        Adherence is calculated as taken doses divided by logged doses. It is a personal tracking aid, not a clinical assessment.
      </div>
    </section>
  );
}
