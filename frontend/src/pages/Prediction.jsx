import { useState } from 'react';
import { BrainCircuit, Sparkles } from 'lucide-react';
import api from '../services/api';

export default function Prediction() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const run = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.post('/predict');
      if (data.success) {
        setResult(data.prediction);
      } else {
        setError('Prediction failed. Please try again.');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Could not reach the prediction service. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const probabilityDisplay = result ? `${Math.round(result.probability * 100)}%` : null;

  return (
    <section className="page">
      <span className="eyebrow">PATTERN SUPPORT</span>
      <h2>AI adherence prediction</h2>
      <p className="muted page-lead">
        A lightweight model trained on historical adherence patterns from the project dataset.
      </p>

      <div className="prediction-panel">
        <div className="prediction-orb">
          <BrainCircuit size={34} />
        </div>
        <div>
          <span>Predicted missed-dose probability</span>
          <strong>{loading ? '…' : probabilityDisplay ?? '—'}</strong>
          {result && (
            <div className={`risk risk-${result.risk?.toLowerCase()}`}>
              {result.risk}
            </div>
          )}
          {!result && !loading && (
            <div className="risk">Press &ldquo;Run prediction&rdquo; to start</div>
          )}
          {loading && (
            <div className="risk">Calculating…</div>
          )}
        </div>
        <button className="primary" onClick={run} disabled={loading}>
          {loading ? 'Updating…' : 'Run prediction'}
        </button>
      </div>

      {error && <div className="error-box" style={{ marginTop: 15 }}>{error}</div>}

      {result && (
        <div className="suggestion">
          <Sparkles size={18} />
          <div>
             <strong>{result.alert ? 'Missed-dose alert' : 'Suggested support'}</strong>
            <p>{result.alert || result.recommendation}</p>
          </div>
        </div>
      )}

      <div className="disclaimer">
        <strong>AI predictions are not medical advice.</strong>{' '}
        They estimate reminder support needs from historical patterns and should never replace your doctor&apos;s guidance.
      </div>
    </section>
  );
}
