import React, { useState } from 'react';
import { Plane, Cloud, Eye, Thermometer, Wind, Gauge, Calendar, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';

const WEATHER_OPTIONS = ['NONE', 'RA', 'TS', 'SHRA', 'BR', 'DZ', 'HZ'];

export default function App() {
  const [formData, setFormData] = useState({
    temp: 31.0,
    dew: 24.0,
    rh: 66.0,
    qnh: 1007.4,
    wind: 12.0,
    month: 6,
    metar_time: 1200,
    wind_dir: 180,
    selected_weather: 'NONE'
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'selected_weather' ? value : parseFloat(value) || value
    }));
  };

  const handlePredict = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const calculated_hour = Math.floor((formData.metar_time || 1200) / 100);
    const weather_encoded = WEATHER_OPTIONS.indexOf(formData.selected_weather);

    const payload = {
      temp: parseFloat(formData.temp),
      dew: parseFloat(formData.dew),
      rh: parseFloat(formData.rh),
      qnh: parseFloat(formData.qnh),
      wind: parseFloat(formData.wind),
      month: parseFloat(formData.month),
      hour: calculated_hour,
      wind_dir: parseFloat(formData.wind_dir),
      weather_encoded: weather_encoded >= 0 ? weather_encoded : 0
    };

    try {
      let res;
      try {
        res = await fetch('/api/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      } catch (e) {
        res = await fetch('http://127.0.0.1:5000/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }

      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`);
      }

      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setResult(data);
      }
    } catch (err) {
      setError('Cannot connect to Backend API. Please ensure python backend/app.py is running on port 5000.');
    } finally {
      setLoading(false);
    }
  };

  const explainCloud = (code) => {
    const str = String(code || '').toUpperCase();
    if (str.includes('CB')) return 'Cumulonimbus cloud reported - indicates potential severe thunderstorm activity.';
    if (str.startsWith('SKC') || str.startsWith('NSC')) return 'No significant cloud cover reported.';
    if (str.startsWith('FEW')) return 'Few clouds reported (1-2 octas coverage).';
    if (str.startsWith('SCT')) return 'Scattered clouds reported (3-4 octas coverage).';
    if (str.startsWith('BKN')) return 'Broken cloud cover reported (5-7 octas coverage).';
    if (str.startsWith('OVC')) return 'Overcast sky condition reported (8 octas full coverage).';
    return 'Cloud condition predicted from METAR observations.';
  };

  const explainVisibility = (vis) => {
    const v = parseInt(vis);
    if (v >= 9999) return 'Visibility is 10 kilometers or more (Optimal Flight Conditions).';
    return `Predicted horizontal visibility is ${v} meters.`;
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="glass-panel" style={{ marginBottom: '1.5rem' }}>
        <h1 className="header-title">
          <Plane className="w-8 h-8 text-cyan-400" />
          BIA Flight Takeoff Weather Verification System
        </h1>
        <p style={{ color: 'var(--text-muted)', marginTop: '0.25rem', fontSize: '0.95rem' }}>
          Hyper-Local AI Aviation Forecast Verification for Bandaranaike International Airport (CMB/VCBI)
        </p>
      </header>

      <div className="grid-layout">
        {/* Input Parameters Sidebar Form */}
        <form className="glass-panel" onSubmit={handlePredict}>
          <h2 className="card-title">
            <Thermometer size={20} color="#38bdf8" /> Weather Observations
          </h2>

          <div className="form-group">
            <label className="form-label">Dry Temperature (°C)</label>
            <input type="number" step="0.1" name="temp" value={formData.temp} onChange={handleChange} className="form-input" required />
          </div>

          <div className="form-group">
            <label className="form-label">Dew Point (°C)</label>
            <input type="number" step="0.1" name="dew" value={formData.dew} onChange={handleChange} className="form-input" required />
          </div>

          <div className="form-group">
            <label className="form-label">Relative Humidity (%)</label>
            <input type="number" step="0.1" name="rh" value={formData.rh} onChange={handleChange} className="form-input" required />
          </div>

          <div className="form-group">
            <label className="form-label">Pressure QNH (hPa)</label>
            <input type="number" step="0.1" name="qnh" value={formData.qnh} onChange={handleChange} className="form-input" required />
          </div>

          <div className="form-group">
            <label className="form-label">Wind Speed (Kts)</label>
            <input type="number" step="0.1" name="wind" value={formData.wind} onChange={handleChange} className="form-input" required />
          </div>

          <div className="form-group">
            <label className="form-label">Wind Direction (°)</label>
            <input type="number" step="1" name="wind_dir" value={formData.wind_dir} onChange={handleChange} className="form-input" required />
          </div>

          <div className="form-group">
            <label className="form-label">Month of Year (1 - 12)</label>
            <input type="number" min="1" max="12" name="month" value={formData.month} onChange={handleChange} className="form-input" required />
          </div>

          <div className="form-group">
            <label className="form-label">UTC Time (HHMM e.g., 1200)</label>
            <input type="number" name="metar_time" value={formData.metar_time} onChange={handleChange} className="form-input" required />
          </div>

          <div className="form-group">
            <label className="form-label">METAR Weather Condition</label>
            <select name="selected_weather" value={formData.selected_weather} onChange={handleChange} className="form-select">
              {WEATHER_OPTIONS.map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>

          <button type="submit" className="btn-primary" disabled={loading} style={{ marginTop: '1rem' }}>
            {loading ? 'Processing XGBoost Forecast...' : 'Generate Takeoff Verification'}
          </button>
        </form>

        {/* Results Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="glass-panel" style={{ flex: 1 }}>
            <h2 className="card-title">
              <CheckCircle2 size={20} color="#34d399" /> Verification Results
            </h2>

            {error && (
              <div className="result-card" style={{ borderColor: 'rgba(239, 68, 68, 0.4)', background: 'rgba(239, 68, 68, 0.1)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f87171', fontWeight: 600 }}>
                  <AlertTriangle size={20} /> Backend API Warning
                </div>
                <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#fca5a5' }}>{error}</p>
              </div>
            )}

            {!result && !error && (
              <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
                <Cloud size={48} style={{ margin: '0 auto 1rem', opacity: 0.4 }} />
                <p style={{ fontSize: '1.1rem', fontWeight: 500 }}>Ready to Generate Forecast</p>
                <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>Enter METAR weather parameters in the left panel and click Generate Takeoff Verification.</p>
              </div>
            )}

            {result && (
              <div>
                {/* Visibility Card */}
                <div className="result-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="badge badge-cyan">Horizontal Visibility</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>XGBoost Regressor</span>
                  </div>
                  <div className="value-highlight">
                    {result.visibility_prediction} <span style={{ fontSize: '1.2rem', fontWeight: 500 }}>m</span>
                  </div>
                  <p style={{ color: '#cbd5e1', fontSize: '0.9rem' }}>
                    <strong>Interpretation:</strong> {explainVisibility(result.visibility_prediction)}
                  </p>
                </div>

                {/* Cloud Card */}
                <div className="result-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="badge badge-emerald">Cloud Coverage & Layer</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>XGBoost Classifier</span>
                  </div>
                  <div className="value-highlight" style={{ color: '#34d399' }}>
                    {result.cloud_status}
                  </div>
                  <p style={{ color: '#cbd5e1', fontSize: '0.9rem' }}>
                    <strong>Interpretation:</strong> {explainCloud(result.cloud_status)}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
