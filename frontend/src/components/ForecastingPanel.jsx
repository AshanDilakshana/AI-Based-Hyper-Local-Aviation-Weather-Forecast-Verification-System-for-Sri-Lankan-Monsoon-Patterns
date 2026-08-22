import { useState } from 'react';
import { Activity, Gauge, Thermometer, Droplets } from 'lucide-react';

export default function ForecastingPanel() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handlePredict = () => {
    setLoading(true);
    // Simulate prediction delay since API endpoints are pending
    setTimeout(() => {
      setResult({
        qnh_hpa: 1010.5,
        dewpoint_c: 24.2,
        rh_percent: 82.5,
        status: "NORMAL",
        message: "Atmospheric pressure and humidity stable."
      });
      setLoading(false);
    }, 1500);
  };

  return (
    <div className="glass-panel">
      <h2>AI Forecasting Module</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '24px', fontSize: '0.9rem' }}>
        Generate a 3-Hour forecast for QNH, Dewpoint, and Relative Humidity.
      </p>

      <div style={{ display: 'flex', gap: '12px' }}>
        <button onClick={handlePredict} disabled={loading}>
          Run 3-Hour Forecast (LightGBM)
        </button>
      </div>

      {loading && <p style={{ marginTop: '20px' }}>Analyzing atmospheric trends...</p>}

      {result && (
        <div style={{ marginTop: '24px', padding: '16px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
          <h3 style={{ marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '8px' }}>
            <Activity size={18} style={{verticalAlign: 'text-bottom', marginRight: '8px'}}/>
            3-Hour Forecast Results
          </h3>
          
          <div className="data-row">
            <span className="data-label"><Gauge size={16} style={{verticalAlign: 'text-bottom'}}/> Predicted QNH</span>
            <span className="data-value">{result.qnh_hpa} hPa</span>
          </div>
          <div className="data-row">
            <span className="data-label"><Thermometer size={16} style={{verticalAlign: 'text-bottom'}}/> Predicted Dewpoint</span>
            <span className="data-value">{result.dewpoint_c} °C</span>
          </div>
          <div className="data-row">
            <span className="data-label"><Droplets size={16} style={{verticalAlign: 'text-bottom'}}/> Derived RH (Magnus)</span>
            <span className="data-value">{result.rh_percent} %</span>
          </div>
          
          <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="data-label">Stability Status:</span>
            <span className={`status-badge status-SAFE`}>{result.status}</span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '8px', textAlign: 'right' }}>
            {result.message}
          </p>
        </div>
      )}
    </div>
  );
}
