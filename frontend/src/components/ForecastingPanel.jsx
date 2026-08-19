import { useState } from 'react';
import axios from 'axios';
import { Activity } from 'lucide-react';

export default function ForecastingPanel({ liveData, apiBase, onForecastComplete }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handlePredict = async (timeframe) => {
    if (!liveData) return;
    
    setLoading(true);
    setError(null);
    setResult(null);

    const payload = {
      temperature: liveData.dry_temp_c || 28,
      dew_point: liveData.dew_point_c || 24,
      humidity: liveData.rh_percent || 80,
      wind_dir: liveData.wind_dir || 200,
      runway_heading: 40,
      time_utc: liveData.time_utc,
      qnh_hpa: liveData.qnh_hpa
    };

    try {
      const res = await axios.post(`${apiBase}/wind/predict/${timeframe}`, payload);
      setResult({ timeframe, ...res.data });
      onForecastComplete(res.data);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch prediction. Is the AI server running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel">
      <h2>AI Forecasting Module</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '24px', fontSize: '0.9rem' }}>
        Select a timeframe to predict runway wind conditions.
      </p>

      <div style={{ display: 'flex', gap: '12px' }}>
        <button onClick={() => handlePredict('1h')} disabled={loading || !liveData}>
          1-Hour Forecast
        </button>
        <button onClick={() => handlePredict('3h')} disabled={loading || !liveData}>
          3-Hour Forecast
        </button>
        <button onClick={() => handlePredict('hybrid_3h')} disabled={loading || !liveData} style={{ background: 'var(--primary)', color: '#000' }}>
          Hybrid 3-Hour Forecast
        </button>
      </div>

      {loading && <p style={{ marginTop: '20px' }}>Analyzing weather patterns...</p>}
      {error && <p style={{ marginTop: '20px', color: 'var(--danger)' }}>{error}</p>}

      {result && (
        <div style={{ marginTop: '24px', padding: '16px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
          <h3 style={{ marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '8px' }}>
            <Activity size={18} style={{verticalAlign: 'text-bottom', marginRight: '8px'}}/>
            Results for {result.timeframe.toUpperCase()} Ahead
          </h3>
          
          <div className="data-row">
            <span className="data-label">Suggested Runway</span>
            <span className="data-value" style={{fontWeight: 'bold', color: 'var(--primary)'}}>{result.runway}</span>
          </div>
          <div className="data-row">
            <span className="data-label">Predicted Wind Speed</span>
            <span className="data-value">{result.predicted_wind_speed_kts} Kts</span>
          </div>
          <div className="data-row">
            <span className="data-label">Crosswind</span>
            <span className="data-value">{result.crosswind_kts} Kts</span>
          </div>
          <div className="data-row">
            <span className="data-label">Headwind</span>
            <span className="data-value">{result.headwind_kts} Kts</span>
          </div>
          
          <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="data-label">Flight Safety Status:</span>
            <span className={`status-badge status-${result.status}`}>{result.status}</span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '8px', textAlign: 'right' }}>
            {result.message}
          </p>
        </div>
      )}
    </div>
  );
}
