import { useEffect, useState } from 'react';
import { Pill, Plus, Trash2, X } from 'lucide-react';
import api from '../services/api';

const defaultForm = {
  medicine_name: '',
  dosage: '',
  dosage_unit: 'mg',
  frequency: 'Once daily',
  start_date: new Date().toISOString().slice(0, 10),
  timings: ['08:00'],
  instructions: '',
};

export default function Medicines() {
  const [medicines, setMedicines] = useState([]);
  const [show, setShow] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [formError, setFormError] = useState('');
  const [loadError, setLoadError] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(defaultForm);

  const load = async () => {
    setLoading(true);
    setLoadError('');
    try {
      const { data } = await api.get('/medicines');
      setMedicines(data.medicines || []);
    } catch (err) {
      setLoadError(err.response?.data?.message || 'Could not load medicines. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    setFormError('');
    try {
      await api.post('/medicines', form);
      setShow(false);
      setForm(defaultForm);
      setSuccessMsg('✓ Medicine added to your routine.');
      setTimeout(() => setSuccessMsg(''), 4000);
      load();
    } catch (err) {
      setFormError(err.response?.data?.message || 'Unable to add medicine. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id) => {
    try {
      await api.delete(`/medicines/${id}`);
      load();
    } catch {
      setLoadError('Could not remove medicine.');
    }
  };

  return (
    <section className="page">
      <div className="welcome-row">
        <div>
          <span className="eyebrow">YOUR LIBRARY</span>
          <h2>Medicines</h2>
          <p className="muted">Keep every prescription and timing in one calm place.</p>
        </div>
        <button className="primary" onClick={() => { setShow(true); setFormError(''); }}>
          <Plus size={17} /> Add medicine
        </button>
      </div>

      {successMsg && <div className="notice">{successMsg}</div>}
      {loadError && <div className="error-box">{loadError}</div>}

      {show && (
        <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) { setShow(false); setFormError(''); } }}>
          <div className="modal-panel">
            <div className="modal-header">
              <h3>Add a medicine</h3>
              <button className="quiet-button" onClick={() => { setShow(false); setFormError(''); }}><X size={18} /></button>
            </div>
            <form onSubmit={save}>
              <div className="form-grid">
                <label>
                  Medicine name
                  <input name="medicine_name" required value={form.medicine_name} onChange={update} placeholder="e.g. Paracetamol" />
                </label>
                <label>
                  Dose
                  <input name="dosage" required value={form.dosage} onChange={update} placeholder="500" />
                </label>
                <label>
                  Dose unit
                  <select name="dosage_unit" value={form.dosage_unit} onChange={update}>
                    <option>mg</option>
                    <option>ml</option>
                    <option>tablet</option>
                    <option>capsule</option>
                  </select>
                </label>
                <label>
                  Frequency
                  <select name="frequency" value={form.frequency} onChange={update}>
                    <option>Once daily</option>
                    <option>Twice daily</option>
                    <option>Three times daily</option>
                    <option>As needed</option>
                  </select>
                </label>
                <label>
                  Start date
                  <input name="start_date" type="date" value={form.start_date} onChange={update} />
                </label>
                <label>
                  Timing
                  <input type="time" value={form.timings[0]} onChange={(e) => setForm({ ...form, timings: [e.target.value] })} />
                </label>
                <label className="full">
                  Instructions
                  <input name="instructions" value={form.instructions} onChange={update} placeholder="After food, with water" />
                </label>
              </div>
              {formError && (
                <div className="error-box" style={{ marginTop: 16, marginBottom: 0 }}>
                  ⚠ {formError}
                </div>
              )}
              <div className="form-actions">
                <button type="button" className="secondary" onClick={() => { setShow(false); setFormError(''); }}>Cancel</button>
                <button className="primary" type="submit" disabled={saving}>
                  {saving ? 'Saving…' : 'Save medicine'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {loading ? (
        <div className="empty-state">Loading your medicines…</div>
      ) : (
        <>
          <div className="medicine-grid">
            {medicines.map((medicine) => (
              <article className="medicine-card" key={medicine.id}>
                <div className="medicine-card-top">
                  <div className="medicine-icon"><Pill size={19} /></div>
                  <button className="quiet-button" onClick={() => remove(medicine.id)} title="Remove medicine">
                    <Trash2 size={16} />
                  </button>
                </div>
                <h3>{medicine.medicine_name}</h3>
                <p className="dose-label">{medicine.dosage} {medicine.dosage_unit}</p>
                <div className="medicine-meta">
                  <span>{medicine.frequency}</span>
                  <span>{medicine.schedules?.map((s) => s.scheduled_time).join(' · ')}</span>
                </div>
                <p className="instruction">{medicine.instructions || 'No special instructions'}</p>
              </article>
            ))}
          </div>
          {!medicines.length && (
            <div className="empty-state">
              Your medicine shelf is empty. Click <strong>+ Add medicine</strong> to begin.
            </div>
          )}
        </>
      )}
    </section>
  );
}

