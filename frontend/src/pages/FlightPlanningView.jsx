import { useState } from "react";
import axios from "axios";

export default function FlightPlanningView({ activeBriefing, setActiveBriefing, briefingsList, onBriefingsUpdate }) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    departure_time: "12:00",
    airport_code: "VCBI",
    area: "d",
    flight_level: "340",
    fly_hours: 6,
    lead_time: "06"
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleCreateBriefing = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await axios.post("http://127.0.0.1:5000/api/create-briefing", {
        departure_time: formData.departure_time,
        airport_code: formData.airport_code,
        area: formData.area,
        flight_level: formData.flight_level,
        fly_hours: Number(formData.fly_hours),
        lead_time: formData.lead_time || "06"
      });
      setActiveBriefing(res.data);
      if (onBriefingsUpdate) {
        await onBriefingsUpdate();
      }
      alert("Briefing Document successfully compiled & stored in SQLite database!");
    } catch (err) {
      setError("Failed to compile flight weather brief. Check API connection.");
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const formatRequestTime = (timeStr) => {
    if (!timeStr) return "N/A";
    return timeStr.replace("T", " ").replace("Z", " UTC");
  };

  return (
    <div className="pilot-flight-desk">
      {/* HEADER */}
      <div className="view-header">
        <div>
          <span className="console-badge">Pilot operations</span>
          <h1>Flight Planning Request</h1>
          <p className="subtitle">Submit flight details to fetch Wind/Temp Aloft Fax charts, TAFs, and METARs from SQLite cache.</p>
        </div>
      </div>

      {error && <div style={{ color: "red", padding: "10px", background: "#fee2e2", borderRadius: "5px", marginBottom: "15px" }}>{error}</div>}

      <div className="forecasting-grid">
        {/* LEFT COLUMN: REQUEST FORM */}
        <form className="dashboard-section-card form-card" onSubmit={handleCreateBriefing}>
          <h3>New Briefing Request</h3>
          <p className="card-desc" style={{ marginBottom: "15px" }}>Enter flight criteria to fetch NOAA meteorological records</p>

          <div className="form-row-2">
            <div className="form-group">
              <label>Airport code (ICAO)</label>
              <input type="text" name="airport_code" value={formData.airport_code} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label>Departure time</label>
              <input type="time" name="departure_time" value={formData.departure_time} onChange={handleChange} required />
            </div>
          </div>

          <div className="form-row-2">
            <div className="form-group">
              <label>Fax Chart Area</label>
              <select 
                name="area" 
                value={formData.area} 
                onChange={handleChange}
                style={{
                  background: "var(--bg-primary)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "6px",
                  padding: "10px",
                  color: "var(--text-primary)",
                  outline: "none",
                  fontSize: "12px",
                  width: "100%"
                }}
              >
                <option value="d">Area D (Asia / Sri Lanka)</option>
                <option value="c">Area C (Europe-Africa)</option>
                <option value="a">Area A (Americas)</option>
                <option value="b1">Area B1 (Americas-Africa)</option>
                <option value="e">Area E (Asia-Australia)</option>
                <option value="f">Area F (Pacific)</option>
              </select>
            </div>
            <div className="form-group">
              <label>Flight Level</label>
              <select 
                name="flight_level" 
                value={formData.flight_level} 
                onChange={handleChange}
                style={{
                  background: "var(--bg-primary)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "6px",
                  padding: "10px",
                  color: "var(--text-primary)",
                  outline: "none",
                  fontSize: "12px",
                  width: "100%"
                }}
              >
                <option value="050">FL050</option>
                <option value="100">FL100</option>
                <option value="180">FL180</option>
                <option value="240">FL240</option>
                <option value="300">FL300</option>
                <option value="340">FL340</option>
                <option value="390">FL390</option>
                <option value="450">FL450</option>
                <option value="630">FL630</option>
              </select>
            </div>
          </div>

          <div className="form-row-2">
            <div className="form-group">
              <label>Estimated flight hours</label>
              <input type="number" name="fly_hours" value={formData.fly_hours} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label>Forecast lead time</label>
              <select 
                name="lead_time" 
                value={formData.lead_time || "06"} 
                onChange={handleChange}
                style={{
                  background: "var(--bg-primary)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "6px",
                  padding: "10px",
                  color: "var(--text-primary)",
                  outline: "none",
                  fontSize: "12px",
                  width: "100%"
                }}
              >
                <option value="06">+06 Hours (F06)</option>
                <option value="12">+12 Hours (F12)</option>
                <option value="18">+18 Hours (F18)</option>
                <option value="24">+24 Hours (F24)</option>
                <option value="30">+30 Hours (F30)</option>
                <option value="36">+36 Hours (F36)</option>
              </select>
            </div>
          </div>

          <button type="submit" className="btn-primary" style={{ marginTop: "15px" }} disabled={submitting}>
            {submitting ? "Generating Briefing..." : "Generate Briefing Document"}
          </button>
        </form>

        {/* RIGHT COLUMN: ACTIVE BRIEFING DETAILS */}
        <div className="dashboard-section-card corridor-panel" style={{ minHeight: "410px" }}>
          {activeBriefing ? (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "15px" }}>
                <div>
                  <h3 style={{ margin: 0 }}>Active Flight Weather Briefing</h3>
                  <p className="card-desc" style={{ margin: 0 }}>Airport Code: <b>{activeBriefing.airport_code}</b> &middot; Region: <b>Area {activeBriefing.area}</b></p>
                </div>
                <span className="badge-safe" style={{ background: "rgba(16, 185, 129, 0.15)", color: "var(--color-safe)" }}>CACHED SQLITE</span>
              </div>

              <div className="flight-route-visual" style={{ padding: "16px", marginBottom: "15px" }}>
                <div className="route-endpoint">
                  <div className="endpoint-dot"></div>
                  <b>{activeBriefing.airport_code}</b>
                  <span>Departure</span>
                </div>
                <div className="route-line-dashed">
                  <div className="airplane-icon">✈</div>
                </div>
                <div className="route-endpoint">
                  <div className="endpoint-dot" style={{ background: "var(--text-muted)" }}></div>
                  <b>FLIGHT PATH</b>
                  <span>Destination</span>
                </div>
              </div>

              <div className="briefing-parameters-grid" style={{ gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                <div className="briefing-item" style={{ textAlign: "left", padding: "10px" }}>
                  <span className="b-lbl">🛫 Departure Time</span>
                  <b>{activeBriefing.departure_time} UTC</b>
                </div>
                <div className="briefing-item" style={{ textAlign: "left", padding: "10px" }}>
                  <span className="b-lbl">✈ Flight Level</span>
                  <b>{activeBriefing.flight_level}</b>
                </div>
                <div className="briefing-item" style={{ textAlign: "left", padding: "10px" }}>
                  <span className="b-lbl">⏱ Flight Duration</span>
                  <b>{activeBriefing.fly_hours} hrs</b>
                </div>
                <div className="briefing-item" style={{ textAlign: "left", padding: "10px" }}>
                  <span className="b-lbl">📥 Request Logged</span>
                  <b style={{ fontSize: "10px" }}>{formatRequestTime(activeBriefing.request_time)}</b>
                </div>
              </div>
            </div>
          ) : (
            <div className="ready-placeholder" style={{ paddingTop: "80px" }}>
              <div className="placeholder-icon">🗺</div>
              <h4>No Briefing Loaded</h4>
              <p>Submit a request on the left, or select a document in the Documents tab, to view maps and raw data.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
