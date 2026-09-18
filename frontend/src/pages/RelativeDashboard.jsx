import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRight, HeartHandshake } from 'lucide-react';
import api from '../services/api';

export default function RelativeDashboard() {
  const [patients, setPatients] = useState([]);
  const [details, setDetails] = useState({});

  useEffect(() => {
    api.get('/relatives/patients').then(async ({ data }) => {
      setPatients(data.patients);
      const entries = await Promise.all(
        data.patients.map(async (patient) => {
          const [analytics, doses] = await Promise.all([
            api.get(`/analytics/weekly?patient_id=${patient.id}`),
            api.get(`/doses/today?patient_id=${patient.id}`)
          ]);
          return [
            patient.id,
            { analytics: analytics.data.summary, doses: doses.data.doses }
          ];
        })
      );
      setDetails(Object.fromEntries(entries));
    });
  }, []);

  return (
    <section className="page">
      <span className="eyebrow">YOUR CARE CIRCLE</span>
      <h2>Linked patients</h2>
      <p className="muted page-lead">A focused view of the people who have authorized you.</p>
      {patients.map((patient) => {
        const detail = details[patient.id];
        return (
          <article className="patient-card" key={patient.id}>
            <div className="patient-head">
              <div className="avatar large">{patient.full_name.slice(0, 1)}</div>
              <div>
                <h3>{patient.full_name}</h3>
                <span>{patient.email}</span>
              </div>
              <HeartHandshake className="patient-heart" />
            </div>
            <div className="patient-stats">
              <div>
                <span>Weekly adherence</span>
                <strong>{detail?.analytics?.adherence ?? 0}%</strong>
              </div>
              <div>
                <span>Today's doses</span>
                <strong>{detail?.doses?.filter((dose) => dose.status === 'taken').length ?? 0} / {detail?.doses?.length ?? 0}</strong>
              </div>
              <div>
                <span>Needs attention</span>
                <strong>{detail?.analytics?.missed ?? 0} missed</strong>
              </div>
            </div>
            <Link className="text-link" to={`/analytics?patient_id=${patient.id}`}>
              View adherence <ArrowUpRight size={15} />
            </Link>
          </article>
        );
      })}
      {!patients.length && (
        <div className="empty-state">
          No patients are linked yet. A patient can approve your access after you register.
        </div>
      )}
    </section>
  );
}

