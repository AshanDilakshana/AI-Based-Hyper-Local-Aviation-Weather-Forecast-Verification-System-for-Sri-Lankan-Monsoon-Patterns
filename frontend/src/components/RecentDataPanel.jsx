import { History } from 'lucide-react';

export default function RecentDataPanel({ recentData }) {
  if (!recentData || recentData.length === 0) {
    return (
      <div className="glass-panel" style={{ marginTop: '20px' }}>
        <h2><History size={20} style={{verticalAlign: 'text-bottom', marginRight: '8px'}}/> Recent Data (Last 10)</h2>
        <p>Loading recent data...</p>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ marginTop: '20px', overflowX: 'auto' }}>
      <h2><History size={20} style={{verticalAlign: 'text-bottom', marginRight: '8px'}}/> Recent Data (Last 10)</h2>
      
      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '15px', fontSize: '0.85rem', textAlign: 'left' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
            <th style={{ padding: '8px 4px' }}>Date/Time (UTC)</th>
            <th style={{ padding: '8px 4px' }}>Wind</th>
            <th style={{ padding: '8px 4px' }}>Temp</th>
            <th style={{ padding: '8px 4px' }}>QNH</th>
          </tr>
        </thead>
        <tbody>
          {recentData.map((record, index) => (
            <tr key={index} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <td style={{ padding: '8px 4px' }}>
                {record.year}-{String(record.month).padStart(2, '0')}-{String(record.date).padStart(2, '0')} {record.time_utc}
              </td>
              <td style={{ padding: '8px 4px' }}>{record.wind_dir}° / {record.wind_speed_kts}kt</td>
              <td style={{ padding: '8px 4px' }}>{record.dry_temp_c}°C</td>
              <td style={{ padding: '8px 4px' }}>{record.qnh_hpa}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
