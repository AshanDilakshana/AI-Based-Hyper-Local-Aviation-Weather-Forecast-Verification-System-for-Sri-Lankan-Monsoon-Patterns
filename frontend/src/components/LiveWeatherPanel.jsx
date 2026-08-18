import { Wind, Thermometer, Droplets, Gauge } from 'lucide-react';

export default function LiveWeatherPanel({ data, onRefresh }) {
  if (!data) {
    return (
      <div className="glass-panel">
        <h2>Live Station Data (Mock)</h2>
        <p>Connecting to BIA Metrology API...</p>
      </div>
    );
  }

  return (
    <div className="glass-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Live Station Data</h2>
        <button onClick={onRefresh} style={{ width: 'auto', margin: 0, padding: '8px 16px', fontSize: '0.9rem' }}>
          Sync Now
        </button>
      </div>
      
      <p style={{ color: 'var(--text-muted)', marginBottom: '24px', fontSize: '0.9rem' }}>
        Last Updated: {data.timestamp_simulated} (Simulating {data.year}-{data.month}-{data.date} {data.time_utc})
      </p>

      <div className="data-row">
        <span className="data-label"><Thermometer size={16} style={{verticalAlign: 'text-bottom'}}/> Temperature</span>
        <span className="data-value">{data.dry_temp_c}°C</span>
      </div>
      <div className="data-row">
        <span className="data-label"><Gauge size={16} style={{verticalAlign: 'text-bottom'}}/> QNH (Pressure)</span>
        <span className="data-value">{data.qnh_hpa} hPa</span>
      </div>
      <div className="data-row">
        <span className="data-label"><Droplets size={16} style={{verticalAlign: 'text-bottom'}}/> Humidity</span>
        <span className="data-value">{data.rh_percent}%</span>
      </div>
      <div className="data-row">
        <span className="data-label"><Wind size={16} style={{verticalAlign: 'text-bottom'}}/> Wind</span>
        <span className="data-value">{data.wind_dir}° at {data.wind_speed_kts} Kts</span>
      </div>
    </div>
  );
}
