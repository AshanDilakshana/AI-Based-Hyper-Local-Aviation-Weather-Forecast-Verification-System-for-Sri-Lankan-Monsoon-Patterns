import { useState, useEffect } from "react";
import "./Dashboard.css";
import { Link } from "react-router-dom";
import axios from "axios";

export default function Dashboard() {
  const [latestData, setLatestData] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);

  const fetchDashboardData = async () => {
    try {
      const latestRes = await axios.get("http://127.0.0.1:5000/api/latest-forecast");
      setLatestData(latestRes.data);
    } catch (err) {
      console.warn("No latest forecast data found yet.", err);
    }

    try {
      const historyRes = await axios.get("http://127.0.0.1:5000/api/verification-history");
      setHistoryData(historyRes.data);
    } catch (err) {
      console.error("Error fetching verification history", err);
    }
    setLoading(false);
  };

  const handleSync = async () => {
    setSyncing(true);
    setError(null);
    try {
      await axios.post("http://127.0.0.1:5000/api/sync-now");
      await fetchDashboardData();
    } catch (err) {
      setError("Failed to sync weather data. Make sure backend is running.");
      console.error(err);
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const formatReportTime = (timeStr) => {
    if (!timeStr) return "N/A";
    // input is ISO format e.g. "2026-08-07T15:10:00"
    // Extract HH:MM
    try {
      const parts = timeStr.split("T");
      if (parts.length === 2) {
        return parts[1].substring(0, 5) + " UTC";
      }
    } catch (e) {
      return timeStr;
    }
    return timeStr;
  };

  return (
    <div className="dashboard">
      <div className="navbar">
        <h2>AeroMet AI</h2>
        <div className="nav-links">
          <Link to="/" className="active">Dashboard</Link>
          <Link to="/forecast">Forecast Form</Link>
          <span>Verification</span>
          <span>Alerts</span>
          <span>Reports</span>
        </div>
      </div>

      <div className="container">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "15px" }}>
          <h2 className="title" style={{ margin: 0 }}>Aviation Weather Dashboard</h2>
          <button 
            onClick={handleSync} 
            disabled={syncing}
            style={{
              padding: "10px 18px",
              background: "#3e6589",
              color: "white",
              border: "none",
              borderRadius: "5px",
              cursor: "pointer",
              fontWeight: "bold",
              boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
            }}
          >
            {syncing ? "Syncing..." : "Sync Live METAR"}
          </button>
        </div>

        {error && <div style={{ color: "red", padding: "10px", background: "#fee2e2", borderRadius: "5px", marginBottom: "15px" }}>{error}</div>}

        <div className="grid">
          <div className="left">
            <div className="card">
              <h3>Latest METAR Parameters (VCBI)</h3>
              {latestData && latestData.observation ? (
                <div>
                  <p style={{ color: "#64748b", fontSize: "13px", marginTop: 0 }}>
                    Observation Time: <b>{formatReportTime(latestData.observation.report_time)}</b>
                  </p>
                  <div className="grid-3">
                    <div className="box">Temp<br /><b>{latestData.observation.temperature.toFixed(1)}°C</b></div>
                    <div className="box">Humidity<br /><b>{latestData.observation.humidity.toFixed(0)}%</b></div>
                    <div className="box">Pressure<br /><b>{latestData.observation.pressure.toFixed(0)} hPa</b></div>
                    <div className="box">Wind Speed<br /><b>{latestData.observation.wind_speed.toFixed(0)} kt</b></div>
                    <div className="box">Wind Dir<br /><b>{latestData.observation.wind_direction.toFixed(0)}°</b></div>
                    <div className="box">Visibility<br /><b>{(latestData.observation.visibility / 1000).toFixed(1)} km</b></div>
                  </div>
                </div>
              ) : (
                <p style={{ color: "#64748b" }}>No METAR data synced yet. Click "Sync Live METAR" to fetch.</p>
              )}
            </div>

            {latestData && latestData.prediction && (
              <div className="card" style={{ background: "#f0fdf4", border: "1px solid #bbf7d0" }}>
                <h3 style={{ color: "#166534", margin: "0 0 10px 0" }}>Active AI T+3 Forecast</h3>
                <p style={{ color: "#15803d", fontSize: "13px", marginTop: 0 }}>
                  Forecast for Target Time: <b>{formatReportTime(latestData.prediction.forecast_report_time || formatReportTime(new Date(latestData.prediction.forecast_time * 1000).toISOString()))}</b>
                </p>
                <div className="grid-3">
                  <div className="box" style={{ background: "white" }}>Predicted Temp<br /><b style={{ color: "#15803d", fontSize: "18px" }}>{latestData.prediction.predicted_temperature.toFixed(2)}°C</b></div>
                  <div className="box" style={{ background: "white" }}>Predicted Pressure<br /><b style={{ color: "#15803d", fontSize: "18px" }}>{latestData.prediction.predicted_pressure.toFixed(2)} hPa</b></div>
                  <div className="box" style={{ background: "white" }}>Source Observation<br /><b>{formatReportTime(latestData.prediction.input_report_time)}</b></div>
                </div>
              </div>
            )}

            <div className="card">
              <h3>Verification: AI Predictions vs METAR Actuals</h3>
              {loading ? (
                <p>Loading verification data...</p>
              ) : historyData.length > 0 ? (
                <div style={{ overflowX: "auto" }}>
                  <table>
                    <thead>
                      <tr>
                        <th>FORECAST TIME</th>
                        <th>PARAMETER</th>
                        <th>AI PREDICTED</th>
                        <th>METAR ACTUAL</th>
                        <th>ABS ERROR</th>
                        <th>STATUS</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historyData.flatMap((pred, idx) => [
                        <tr key={`${idx}-temp`}>
                          <td>{formatReportTime(pred.forecast_report_time)}</td>
                          <td>Dry Temp</td>
                          <td>{pred.predicted_temperature.toFixed(2)} °C</td>
                          <td>{pred.actual_temperature.toFixed(2)} °C</td>
                          <td>{pred.temp_error.toFixed(2)} °C</td>
                          <td className={pred.temp_status === "MATCH" ? "ok" : "bad"} style={{ fontWeight: "bold" }}>
                            {pred.temp_status === "MATCH" ? "✔ MATCH" : "✘ MISMATCH"}
                          </td>
                        </tr>,
                        <tr key={`${idx}-press`}>
                          <td>{formatReportTime(pred.forecast_report_time)}</td>
                          <td>QNH Pressure</td>
                          <td>{pred.predicted_pressure.toFixed(2)} hPa</td>
                          <td>{pred.actual_pressure.toFixed(2)} hPa</td>
                          <td>{pred.pressure_error.toFixed(2)} hPa</td>
                          <td className={pred.pressure_status === "MATCH" ? "ok" : "bad"} style={{ fontWeight: "bold" }}>
                            {pred.pressure_status === "MATCH" ? "✔ MATCH" : "✘ MISMATCH"}
                          </td>
                        </tr>
                      ])}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p style={{ color: "#64748b" }}>No verified predictions found in database yet. Predictions are made at 3-hour boundaries (UTC 00, 03, 06, etc.) and verified when the corresponding target observation arrives.</p>
              )}
            </div>
          </div>

          <div className="right">
            <div className="card">
              <h3>Monsoon Context</h3>
              <p>Southwest Monsoon - Active</p>
              <p>Northeast Monsoon - Inactive</p>
            </div>

            <div className="card alert">
              <h3>Active Alerts</h3>
              <p className="red">⚠ Runway Wind Shear Risk</p>
              <p className="yellow">⚠ Visibility Variation</p>
            </div>

            <div className="card center">
              <h3>Model Accuracy (R² Score)</h3>
              <div className="circle">53.3%</div>
              <p style={{ fontSize: "11px", color: "#64748b", marginTop: "10px" }}>Trained on historical BIA METAR dataset</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}