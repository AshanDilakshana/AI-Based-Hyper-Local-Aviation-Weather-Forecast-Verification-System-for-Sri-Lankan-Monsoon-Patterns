import { useState, useEffect } from "react";
import axios from "axios";

export default function ForecastingView() {
  const [latestObs, setLatestObs] = useState(null);
  const [latestForecast, setLatestForecast] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [runningPredict, setRunningPredict] = useState(false);

  const fetchObservations = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:5000/api/recent-observations");
      if (res.data && res.data.length > 0) {
        setLatestObs(res.data[res.data.length - 1]);
      }
    } catch (e) {
      console.error("Error fetching observations:", e);
    }
  };

  const fetchLatestForecast = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:5000/api/latest-forecast");
      setLatestForecast(res.data || null);
    } catch (e) {
      console.warn("No active prediction found in database yet.", e);
    }
  };

  const fetchVerificationHistory = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:5000/api/verification-history");
      setHistoryData(res.data || []);
    } catch (e) {
      console.error("Error fetching history:", e);
    }
  };

  const loadAllData = async () => {
    setLoading(true);
    await Promise.all([fetchObservations(), fetchLatestForecast(), fetchVerificationHistory()]);
    setLoading(false);
  };

  useEffect(() => {
    loadAllData();
    const interval = setInterval(() => {
      fetchObservations();
      fetchLatestForecast();
      fetchVerificationHistory();
    }, 15000); // Poll forecasting and verification tables every 15 seconds
    return () => clearInterval(interval);
  }, []);

  const handleRunModelPrediction = async () => {
    setRunningPredict(true);
    try {
      const res = await axios.post("http://127.0.0.1:5000/api/run-active-prediction");
      // Res contains the prediction dictionary
      setLatestForecast({
        prediction: res.data,
        observation: latestObs
      });
      await fetchVerificationHistory();
      alert("Local Random Forest Weather Model forecast successfully calculated & saved to SQLite!");
    } catch (err) {
      alert(err.response?.data?.error || "Model execution failed.");
    } finally {
      setRunningPredict(false);
    }
  };

  const formatReportTime = (timeStr) => {
    if (!timeStr) return "N/A";
    const parts = timeStr.split("T");
    if (parts.length === 2) {
      return parts[1].substring(0, 5) + " UTC";
    }
    return timeStr;
  };

  return (
    <div className="forecasting-console">
      {/* HEADER */}
      <div className="view-header">
        <div>
          <span className="console-badge">Meteorological operations</span>
          <h1>Weather Forecasting</h1>
          <p className="subtitle">Live observation context and AI-supported aviation forecast guidance.</p>
        </div>
      </div>

      <div className="forecasting-grid">
        {/* LEFT COLUMN: ACTIVE CONTEXT AND RUN TRIGGER */}
        <div className="dashboard-section-card form-card" style={{ minHeight: "410px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <h3>Random Forest Weather Model Predictor</h3>
            <p className="card-desc" style={{ marginBottom: "15px" }}>Uses active observation coordinates stored in SQLite database</p>

            {latestObs ? (
              <div style={{ background: "#0b1120", padding: "14px", borderRadius: "8px", border: "1px solid var(--border-color)", fontSize: "12px", display: "flex", flexDirection: "column", gap: "8px" }}>
                <span className="b-lbl" style={{ color: "var(--color-accent)", fontSize: "9px" }}>Input Live METAR Context</span>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--text-secondary)" }}>Report Time:</span>
                  <b>{formatReportTime(latestObs.report_time)}</b>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--text-secondary)" }}>Temperature:</span>
                  <b>{latestObs.temperature.toFixed(1)} °C</b>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--text-secondary)" }}>Pressure (QNH):</span>
                  <b>{latestObs.pressure.toFixed(1)} hPa</b>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--text-secondary)" }}>Humidity:</span>
                  <b>{latestObs.humidity.toFixed(0)} % RH</b>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--text-secondary)" }}>Wind Speed:</span>
                  <b>{latestObs.wind_speed.toFixed(0)} kt</b>
                </div>
              </div>
            ) : (
              <p style={{ color: "var(--text-muted)" }}>Loading observations context...</p>
            )}
          </div>

          <button 
            type="button" 
            className="btn-primary" 
            style={{ width: "100%", padding: "14px", fontSize: "13px", marginTop: "20px" }}
            onClick={handleRunModelPrediction}
            disabled={runningPredict || !latestObs}
          >
            {runningPredict ? "⚡ Executing Model..." : "⚡ Run Model Prediction"}
          </button>
        </div>

        {/* RIGHT COLUMN: ACTIVE PREDICTION VALUE */}
        <div className="dashboard-section-card result-panel" style={{ minHeight: "410px" }}>
          {latestForecast && latestForecast.prediction ? (
            <div className="latest-db-display">
              <div className="result-header-row">
                <h3>Active Weather Prediction (T+3)</h3>
                <span className="badge-safe">LIVE</span>
              </div>
              <p className="card-desc">Target Forecast Time: <b>{formatReportTime(latestForecast.prediction.forecast_report_time)}</b></p>
              
              <div className="result-values-grid">
                <div className="result-val-box">
                  <div className="val-lbl">Predicted Temp</div>
                  <div className="val-text" style={{ color: "#3b82f6" }}>{latestForecast.prediction.predicted_temperature.toFixed(2)} <span className="val-u">°C</span></div>
                </div>
                <div className="result-val-box">
                  <div className="val-lbl">Predicted Pressure</div>
                  <div className="val-text" style={{ color: "#3b82f6" }}>{latestForecast.prediction.predicted_pressure.toFixed(2)} <span className="val-u">hPa</span></div>
                </div>
              </div>

              <div className="forecast-details-card">
                <h4>Forecast details</h4>
                <div className="detail-row"><span>Forecast ID:</span> <b>AIV-{latestForecast.prediction.id}</b></div>
                <div className="detail-row"><span>Source input:</span> <b>METAR {formatReportTime(latestForecast.prediction.input_report_time)}</b></div>
                <div className="detail-row"><span>Lead time:</span> <b>Next 3 hours</b></div>
              </div>
            </div>
          ) : (
            <div className="ready-placeholder">
              <div className="placeholder-icon">🌤</div>
              <h4>Model Ready</h4>
              <p>Click "Run Model Prediction" on the left to compute and cache the T+3 weather outlook from SQLite parameters.</p>
            </div>
          )}
        </div>
      </div>

      {/* VERIFICATION COMPARISON SECTION */}
      <div className="dashboard-section-card verification-section">
        <h3>Observed weather vs research model predictions</h3>
        <p className="card-desc">Comparison validation parameters: displays the difference (absolute error) between model prediction and live observed values</p>

        {loading ? (
          <p className="loading-text">Loading verification history...</p>
        ) : historyData.length > 0 ? (
          <div className="table-wrapper">
            <table className="observation-table">
              <thead>
                <tr>
                  <th>Forecast Time</th>
                  <th>Parameter</th>
                  <th>AI Predicted</th>
                  <th>METAR Observed</th>
                  <th>Absolute Error (Diff)</th>
                  <th>Match Status</th>
                </tr>
              </thead>
              <tbody>
                {historyData.flatMap((pred, idx) => [
                  <tr key={`${idx}-temp`}>
                    <td>{formatReportTime(pred.forecast_report_time)}</td>
                    <td>Dry Temperature</td>
                    <td>{pred.predicted_temperature.toFixed(2)} °C</td>
                    <td>{pred.actual_temperature.toFixed(2)} °C</td>
                    <td style={{ fontWeight: "bold", color: pred.temp_status === "MATCH" ? "var(--color-safe)" : "var(--color-danger)" }}>
                      {pred.temp_error.toFixed(2)} °C
                    </td>
                    <td className="status-cell">
                      <span className={`status-pill ${pred.temp_status === "MATCH" ? "match" : "mismatch"}`}>
                        {pred.temp_status === "MATCH" ? "✔ MATCH" : "✘ MISMATCH"}
                      </span>
                    </td>
                  </tr>,
                  <tr key={`${idx}-press`}>
                    <td>{formatReportTime(pred.forecast_report_time)}</td>
                    <td>QNH Pressure</td>
                    <td>{pred.predicted_pressure.toFixed(2)} hPa</td>
                    <td>{pred.actual_pressure.toFixed(2)} hPa</td>
                    <td style={{ fontWeight: "bold", color: pred.pressure_status === "MATCH" ? "var(--color-safe)" : "var(--color-danger)" }}>
                      {pred.pressure_error.toFixed(2)} hPa
                    </td>
                    <td className="status-cell">
                      <span className={`status-pill ${pred.pressure_status === "MATCH" ? "match" : "mismatch"}`}>
                        {pred.pressure_status === "MATCH" ? "✔ MATCH" : "✘ MISMATCH"}
                      </span>
                    </td>
                  </tr>
                ])}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="empty-text">No verified predictions cached in database yet.</p>
        )}
      </div>
    </div>
  );
}
