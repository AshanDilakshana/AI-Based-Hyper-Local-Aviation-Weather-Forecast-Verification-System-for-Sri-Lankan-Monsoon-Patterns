import { useState, useEffect } from "react";
import axios from "axios";
import LiveVerificationPanel from "../components/LiveVerificationPanel";

export default function DashboardView({ onTriggerSync }) {
  const [observations, setObservations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const fetchObservations = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:5000/api/recent-observations");
      // Sort oldest to newest for graphing, then reverse for display table
      setObservations(res.data || []);
    } catch (err) {
      console.error("Error fetching observations:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await onTriggerSync();
      await fetchObservations();
    } catch (e) {
      console.error(e);
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    fetchObservations();
    const interval = setInterval(fetchObservations, 15000); // Poll observations every 15 seconds
    return () => clearInterval(interval);
  }, []);

  // Use latest observation for top cards
  const latest = observations[observations.length - 1] || {
    temperature: 29.2,
    pressure: 1009.4,
    humidity: 78.0,
    wind_speed: 14,
    wind_direction: 240,
    visibility: 10000,
    raw_ob: "METAR VCBI 071510Z 24014KT 9999 BKN018 29/24 Q1009 NOSIG"
  };

  // Extract cloud text from raw METAR e.g. BKN018 -> BKN 1800 ft
  const getCloudBase = (rawOb) => {
    if (!rawOb) return "SCT 1800 ft";
    const match = rawOb.match(/(FEW|SCT|BKN|OVC)(\d{3})/);
    if (match) {
      const baseFeet = parseInt(match[2], 10) * 100;
      return `${match[1]} ${baseFeet} ft`;
    }
    return "CAVOK";
  };

  // Convert visibility meters to text
  const getVisibilityText = (visMeters) => {
    if (visMeters >= 9999) return "10 km";
    return `${(visMeters / 1000).toFixed(1)} km`;
  };

  // Format UTC times for table rows
  const formatTimeSLST = (timeStr) => {
    if (!timeStr) return "N/A";
    const parts = timeStr.split("T");
    if (parts.length === 2) {
      return parts[1].substring(0, 5);
    }
    return timeStr;
  };

  // Render SVG Sparkline
  const renderSvgLine = (data, key, strokeColor) => {
    if (data.length < 2) return null;
    const values = data.map(d => d[key]);
    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    const range = maxVal - minVal || 1;
    const width = 800;
    const height = 80;
    const points = data.map((d, idx) => {
      const x = (idx / (data.length - 1)) * width;
      const y = height - 10 - ((d[key] - minVal) / range) * (height - 20);
      return `${x},${y}`;
    });

    return (
      <svg width="100%" height="80" viewBox={`0 0 ${width} ${height}`} style={{ overflow: "visible" }}>
        <path
          d={`M ${points.join(" L ")}`}
          fill="none"
          stroke={strokeColor}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Draw data point handles */}
        {points.map((p, i) => {
          const [px, py] = p.split(",");
          return (
            <circle
              key={i}
              cx={px}
              cy={py}
              r="4"
              fill={strokeColor}
              stroke="#161e31"
              strokeWidth="1.5"
            />
          );
        })}
      </svg>
    );
  };

  // For table listing, display recent first
  const displayObs = [...observations].reverse();

  return (
    <div className="meteorological-console">
      {/* HEADER SECTION */}
      <div className="view-header">
        <div>
          <span className="console-badge">Meteorological operations</span>
          <h1>Forecast Dashboard</h1>
          <p className="subtitle">
            BIA/CMB hyper-local weather intelligence &middot; Live station feed
          </p>
        </div>

        <button className="btn-sync" onClick={handleSync} disabled={syncing}>
          {syncing ? "Synchronizing..." : "Sync Live METAR"}
        </button>
      </div>

      {/* LIVE VERIFICATION WIDGET */}
      <LiveVerificationPanel />

      {/* PARAMETER CARDS GRID */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="card-label">Temperature</div>
          <div className="card-val-row">
            <span className="card-number">{latest.temperature.toFixed(1)}</span>
            <span className="card-unit">°C</span>
          </div>
          <div className="card-trend positive">↑ 0.8° <span className="trend-lbl">last hour</span></div>
        </div>

        <div className="metric-card">
          <div className="card-label">Pressure</div>
          <div className="card-val-row">
            <span className="card-number">{latest.pressure.toFixed(1)}</span>
            <span className="card-unit">hPa</span>
          </div>
          <div className="card-trend negative">↓ 1.2 <span className="trend-lbl">last hour</span></div>
        </div>

        <div className="metric-card">
          <div className="card-label">Humidity</div>
          <div className="card-val-row">
            <span className="card-number">{latest.humidity.toFixed(0)}</span>
            <span className="card-unit">% RH</span>
          </div>
          <div className="card-trend negative">↓ 3% <span className="trend-lbl">last hour</span></div>
        </div>

        <div className="metric-card">
          <div className="card-label">Wind speed</div>
          <div className="card-val-row">
            <span className="card-number">{latest.wind_speed.toFixed(0)}</span>
            <span className="card-unit">kt</span>
          </div>
          <div className="card-trend neutral">{latest.wind_direction.toFixed(0)}° WSW</div>
        </div>

        <div className="metric-card">
          <div className="card-label">Cloud base</div>
          <div className="card-val-row">
            <span className="card-number" style={{ fontSize: "20px" }}>{getCloudBase(latest.raw_ob)}</span>
          </div>
          <div className="card-trend positive">BKN <span className="trend-lbl">scattered layers</span></div>
        </div>

        <div className="metric-card">
          <div className="card-label">Visibility</div>
          <div className="card-val-row">
            <span className="card-number">{getVisibilityText(latest.visibility)}</span>
          </div>
          <div className="card-trend positive">VMC <span className="trend-lbl">unrestricted visibility</span></div>
        </div>
      </div>

      {/* MODEL RETRAINING & DATA COLLECTOR CARD */}
      <div className="dashboard-section-card" style={{ borderLeft: "4px solid var(--color-safe)", background: "var(--bg-secondary)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h3 style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span>⚙</span> Model Retraining & Data Collector
            </h3>
            <p className="card-desc" style={{ margin: "4px 0 0 0" }}>
              Accumulating hourly meteorological observations to support periodic model retraining loops and improve forecasting accuracy.
            </p>
          </div>
          <div style={{ background: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.2)", color: "var(--color-safe)", padding: "6px 12px", borderRadius: "4px", fontSize: "11px", fontWeight: "bold" }}>
            🟢 COLLECTING FOR TRAINING
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", marginTop: "20px" }}>
          <div style={{ background: "var(--bg-primary)", padding: "12px 15px", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
            <span style={{ fontSize: "9px", color: "var(--text-muted)", display: "block", textTransform: "uppercase", fontWeight: "bold", marginBottom: "4px" }}>Accumulated Training Records</span>
            <b style={{ fontSize: "20px", color: "var(--color-accent)" }}>{observations.length} logs cached</b>
          </div>
          <div style={{ background: "var(--bg-primary)", padding: "12px 15px", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
            <span style={{ fontSize: "9px", color: "var(--text-muted)", display: "block", textTransform: "uppercase", fontWeight: "bold", marginBottom: "4px" }}>Retraining Interval</span>
            <b style={{ fontSize: "20px", color: "var(--text-primary)" }}>Monthly Cycle</b>
          </div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
            <button 
              className="btn-primary" 
              style={{ width: "100%", padding: "12px" }}
              onClick={() => {
                window.open("http://127.0.0.1:5000/api/export-training-data");
              }}
            >
              📥 Export CSV Dataset
            </button>
          </div>
        </div>
      </div>

      {/* RECENT OBSERVATIONS TABLE */}
      <div className="dashboard-section-card">
        <h3>Recent API weather observations</h3>
        <p className="card-desc">Cashed simulated feed for interface demonstration &middot; last updated 10-mins ago</p>

        {loading ? (
          <p className="loading-text">Loading weather logs...</p>
        ) : observations.length > 0 ? (
          <div className="table-wrapper">
            <table className="observation-table">
              <thead>
                <tr>
                  <th>Timestamp (UTC)</th>
                  <th>Temperature</th>
                  <th>Pressure</th>
                  <th>Humidity</th>
                  <th>Wind speed</th>
                  <th>Wind direction</th>
                  <th>Visibility</th>
                  <th>Cloud coverage</th>
                </tr>
              </thead>
              <tbody>
                {displayObs.map((obs, idx) => (
                  <tr key={idx}>
                    <td>{formatTimeSLST(obs.report_time)}</td>
                    <td>{obs.temperature.toFixed(1)}°C</td>
                    <td>{obs.pressure.toFixed(1)} hPa</td>
                    <td>{obs.humidity.toFixed(0)}%</td>
                    <td>{obs.wind_speed.toFixed(0)} kt</td>
                    <td>{obs.wind_direction.toFixed(0)}°</td>
                    <td>{getVisibilityText(obs.visibility)}</td>
                    <td>{getCloudBase(obs.raw_ob).split(" ")[0]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="empty-text">No records stored in local SQLite database yet.</p>
        )}
      </div>

      {/* LIVE TREND CHART */}
      <div className="dashboard-section-card chart-section">
        <h3>Live trend monitor</h3>
        <p className="card-desc">Last 6 hours &middot; Automatic station observations (VCBI)</p>

        {observations.length >= 2 ? (
          <div className="charts-container">
            <div className="chart-item">
              <div className="chart-header">
                <span>Temperature Trend (°C)</span>
                <b>{observations[observations.length-1].temperature.toFixed(1)}°C</b>
              </div>
              <div className="svg-container">
                {renderSvgLine(observations.slice(-6), "temperature", "#f59e0b")}
              </div>
            </div>

            <div className="chart-item">
              <div className="chart-header">
                <span>Pressure Trend (hPa)</span>
                <b>{observations[observations.length-1].pressure.toFixed(1)} hPa</b>
              </div>
              <div className="svg-container">
                {renderSvgLine(observations.slice(-6), "pressure", "#60a5fa")}
              </div>
            </div>

            <div className="chart-item">
              <div className="chart-header">
                <span>Humidity Trend (%)</span>
                <b>{observations[observations.length-1].humidity.toFixed(0)}%</b>
              </div>
              <div className="svg-container">
                {renderSvgLine(observations.slice(-6), "humidity", "#10b981")}
              </div>
            </div>
          </div>
        ) : (
          <p className="empty-text">Waiting for at least 2 database records to render trend graphs.</p>
        )}
      </div>
    </div>
  );
}
