import { useState, useEffect } from "react";
import "./App.css";
import DashboardView from "./pages/DashboardView";
import ForecastingView from "./pages/ForecastingView";
import FlightPlanningView from "./pages/FlightPlanningView";
import axios from "axios";

function App() {
  const [activeRole, setActiveRole] = useState("predictor"); // "predictor" or "pilot"
  const [activeTab, setActiveTab] = useState("dashboard");
  const [timeStr, setTimeStr] = useState("");
  const [briefingsList, setBriefingsList] = useState([]);
  const [selectedBriefing, setSelectedBriefing] = useState(null);
  
  // Custom NOAA Map Explorer States
  const [explorerFL, setExplorerFL] = useState("340");
  const [explorerArea, setExplorerArea] = useState("d");
  const [explorerHour, setExplorerHour] = useState("06");

  // Live UTC and Colombo (SLST) Clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const utcTime = now.toISOString().substring(11, 19);
      
      const options = { timeZone: 'Asia/Colombo', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' };
      const slstTime = now.toLocaleTimeString('en-US', options);
      
      setTimeStr(`${utcTime} UTC | ${slstTime} SLST`);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchBriefings = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:5000/api/briefings");
      setBriefingsList(res.data || []);
      setSelectedBriefing(prev => {
        if (!prev && res.data && res.data.length > 0) {
          return res.data[0];
        }
        return prev;
      });
    } catch (e) {
      console.error("Error fetching briefings:", e);
    }
  };

  useEffect(() => {
    fetchBriefings();
    const interval = setInterval(fetchBriefings, 15000); // Auto refresh briefings list every 15 seconds
    return () => clearInterval(interval);
  }, []);

  const handleTriggerSync = async () => {
    try {
      await axios.post("http://127.0.0.1:5000/api/sync-now");
    } catch (e) {
      console.error("Error triggering sync:", e);
    }
  };

  const handleRoleChange = (role) => {
    setActiveRole(role);
    if (role === "predictor") {
      setActiveTab("dashboard");
    } else {
      setActiveTab("flight-planning");
    }
  };

  const formatRequestTime = (timeStr) => {
    if (!timeStr) return "N/A";
    return timeStr.replace("T", " ").replace("Z", " UTC");
  };

  const renderForecastMapsView = () => {
    const filename = `F${explorerHour}_wind_${explorerFL}_${explorerArea}.gif`;
    const noaaUrl = `https://aviationweather.gov/data/products/fax/${filename}`;

    return (
      <div className="dashboard-section-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "15px" }}>
          <div>
            <h3>Aviation Forecast Maps Explorer</h3>
            <p className="card-desc" style={{ margin: 0 }}>Select parameters to download Wind & Temp Aloft charts directly from NOAA AWC</p>
          </div>
          
          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            <div style={{ display: "flex", flexDirection: "column" }}>
              <label style={{ fontSize: "9px", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: "4px", fontWeight: "bold" }}>Flight Level</label>
              <select 
                value={explorerFL} 
                onChange={(e) => setExplorerFL(e.target.value)}
                style={{ background: "var(--bg-primary)", color: "var(--text-primary)", border: "1px solid var(--border-color)", borderRadius: "6px", padding: "8px", fontSize: "12px", outline: "none" }}
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

            <div style={{ display: "flex", flexDirection: "column" }}>
              <label style={{ fontSize: "9px", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: "4px", fontWeight: "bold" }}>Fax Chart Area</label>
              <select 
                value={explorerArea} 
                onChange={(e) => setExplorerArea(e.target.value)}
                style={{ background: "var(--bg-primary)", color: "var(--text-primary)", border: "1px solid var(--border-color)", borderRadius: "6px", padding: "8px", fontSize: "12px", outline: "none" }}
              >
                <option value="d">Area D (Asia / Sri Lanka)</option>
                <option value="c">Area C (Europe-Africa)</option>
                <option value="a">Area A (Americas)</option>
                <option value="b1">Area B1 (Americas-Africa)</option>
                <option value="e">Area E (Asia-Australia)</option>
                <option value="f">Area F (Pacific)</option>
              </select>
            </div>

            <div style={{ display: "flex", flexDirection: "column" }}>
              <label style={{ fontSize: "9px", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: "4px", fontWeight: "bold" }}>Forecast Lead Time</label>
              <select 
                value={explorerHour} 
                onChange={(e) => setExplorerHour(e.target.value)}
                style={{ background: "var(--bg-primary)", color: "var(--text-primary)", border: "1px solid var(--border-color)", borderRadius: "6px", padding: "8px", fontSize: "12px", outline: "none" }}
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
        </div>

        <div style={{ textAlign: "center", background: "#0b1120", padding: "20px", borderRadius: "10px", border: "1px solid var(--border-color)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-secondary)", fontSize: "12px", marginBottom: "12px" }}>
            <span>Aviation Chart: <b>{filename}</b></span>
            <span>Target Server: <b>aviationweather.gov</b></span>
          </div>
          
          <img 
            src={noaaUrl} 
            alt="NOAA Wind aloft Fax Weather Chart" 
            style={{ maxWidth: "100%", maxHeight: "550px", objectFit: "contain", borderRadius: "4px", border: "1px solid var(--border-color)", marginBottom: "15px" }} 
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = "http://127.0.0.1:5000/static/charts/fallback.gif";
            }}
          />
          
          <div style={{ display: "flex", gap: "10px", justifyContent: "center" }}>
            <a 
              href={noaaUrl} 
              target="_blank"
              rel="noreferrer"
              className="btn-secondary" 
              style={{ textDecoration: "none", display: "inline-block" }}
            >
              👁 View Map in New Tab
            </a>
            <a 
              href={noaaUrl} 
              download={filename}
              className="btn-primary" 
              style={{ textDecoration: "none", display: "inline-block" }}
            >
              📥 Download Fax Map
            </a>
          </div>
        </div>
      </div>
    );
  };

  // Render content depending on active role & tab
  const renderContentView = () => {
    if (activeRole === "predictor") {
      switch (activeTab) {
        case "dashboard":
          return <DashboardView onTriggerSync={handleTriggerSync} />;
        case "forecasting":
          return <ForecastingView />;
        case "maps":
          return renderForecastMapsView();
        case "approvals":
          return (
            <div className="dashboard-section-card">
              <h3>Forecast Approval Center</h3>
              <p className="card-desc">Approve generated research forecasts for flight dissemination</p>
              <p style={{ color: "#9ca3af" }}>No pending documents awaiting validation check.</p>
            </div>
          );
        case "logs":
          return (
            <div className="dashboard-section-card">
              <h3>System Activity Logs</h3>
              <p className="card-desc">Live log stream from automatic weather prediction scheduler</p>
              <div style={{ background: "#090e1a", padding: "15px", borderRadius: "6px", fontFamily: "monospace", fontSize: "11px", color: "#10b981", border: "1px solid #233152" }}>
                <p>[21:40:22 UTC] Initializing SQLite weather_data.db tables...</p>
                <p>[21:40:22 UTC] SQLite tables initialized successfully.</p>
                <p>[21:40:22 UTC] Background METAR sync thread started successfully.</p>
                <p>[21:40:23 UTC] Fetching observation history VCBI from AviationWeather API...</p>
                <p>[21:40:24 UTC] Successfully loaded 24 records. Cache populated.</p>
              </div>
            </div>
          );
        default:
          return <DashboardView onTriggerSync={handleTriggerSync} />;
      }
    } else {
      // Pilot Workspace (Flight Planning, Forecast Maps, Documents)
      switch (activeTab) {
        case "flight-planning":
          return (
            <FlightPlanningView 
              activeBriefing={selectedBriefing} 
              setActiveBriefing={setSelectedBriefing} 
              briefingsList={briefingsList} 
              onBriefingsUpdate={fetchBriefings} 
            />
          );
        case "maps":
          return renderForecastMapsView();
        case "documents":
          return (
            <div className="pilot-documents-tab">
              {/* BRIEFINGS LOG LIST FROM SQLITE */}
              <div className="dashboard-section-card">
                <h3>Aviation briefings package library</h3>
                <p className="card-desc">List of all requested briefing documents stored in SQLite weather_data.db</p>
                
                {briefingsList.length > 0 ? (
                  <div className="table-wrapper">
                    <table className="observation-table">
                      <thead>
                        <tr>
                          <th>Request Time</th>
                          <th>ICAO</th>
                          <th>Dep Time</th>
                          <th>Flight Level</th>
                          <th>Region</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {briefingsList.map((brief, idx) => (
                          <tr 
                            key={idx} 
                            className={selectedBriefing?.id === brief.id ? "active-row" : ""} 
                            style={{ cursor: "pointer", background: selectedBriefing?.id === brief.id ? "rgba(96,165,250,0.08)" : "" }}
                            onClick={() => setSelectedBriefing(brief)}
                          >
                            <td>{formatRequestTime(brief.request_time)}</td>
                            <td><b>{brief.airport_code}</b></td>
                            <td>{brief.departure_time} UTC</td>
                            <td>{brief.flight_level}</td>
                            <td>Area {brief.area}</td>
                            <td><span className="badge-status match">APPROVED</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p style={{ color: "var(--text-muted)" }}>No historical briefings requested yet.</p>
                )}
              </div>

              {/* DETAILED BRIEFING DOCUMENT PACK */}
              {selectedBriefing && (
                <div className="dashboard-section-card briefing-doc-card">
                  <div className="briefing-doc-header" style={{ marginBottom: "20px" }}>
                    <div>
                      <h3>Briefing Package Details (AIV-{selectedBriefing.id})</h3>
                      <p className="card-desc">Aviation document pack compiled on {formatRequestTime(selectedBriefing.request_time)}</p>
                    </div>
                    <button className="btn-sync" onClick={() => window.print()}>🖨 Print Document</button>
                  </div>

                  <div className="briefing-details-list" style={{ gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", background: "var(--bg-primary)" }}>
                    <div className="briefing-detail-col">
                      <span>AIRPORT CODE</span>
                      <p>{selectedBriefing.airport_code}</p>
                    </div>
                    <div className="briefing-detail-col">
                      <span>DEPARTURE TIME</span>
                      <p>{selectedBriefing.departure_time} UTC</p>
                    </div>
                    <div className="briefing-detail-col">
                      <span>FLIGHT LEVEL</span>
                      <p>{selectedBriefing.flight_level}</p>
                    </div>
                    <div className="briefing-detail-col">
                      <span>FLY HOURS</span>
                      <p>{selectedBriefing.fly_hours} hrs</p>
                    </div>
                  </div>

                  <div className="briefing-details-list" style={{ gridTemplateColumns: "1fr 1fr", gap: "20px", marginTop: "20px" }}>
                    <div className="briefing-detail-col" style={{ background: "#090e1a", padding: "15px", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                      <span className="b-lbl" style={{ color: "var(--color-accent)", marginBottom: "8px" }}>📁 RAW METAR TEXT</span>
                      <p style={{ fontFamily: "monospace", fontSize: "11px", fontWeight: "normal", whiteSpace: "pre-wrap", color: "var(--text-primary)" }}>
                        {selectedBriefing.metar_raw}
                      </p>
                    </div>
                    <div className="briefing-detail-col" style={{ background: "#090e1a", padding: "15px", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                      <span className="b-lbl" style={{ color: "var(--color-accent)", marginBottom: "8px" }}>📁 RAW TAF TEXT</span>
                      <p style={{ fontFamily: "monospace", fontSize: "11px", fontWeight: "normal", whiteSpace: "pre-wrap", color: "var(--text-primary)" }}>
                        {selectedBriefing.taf_raw}
                      </p>
                    </div>
                  </div>

                  <div style={{ marginTop: "20px", background: "var(--bg-primary)", padding: "15px", borderRadius: "8px", border: "1px solid var(--border-color)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <span className="b-lbl" style={{ color: "var(--color-accent)", marginBottom: "4px", display: "block" }}>🗺 ATTACHED FAX MAP</span>
                      <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>Filename: {selectedBriefing.chart_url.split("/").pop()}</span>
                    </div>
                    <div style={{ display: "flex", gap: "10px" }}>
                      <a href={`http://127.0.0.1:5000${selectedBriefing.chart_file_path}`} target="_blank" rel="noreferrer" className="btn-secondary" style={{ textDecoration: "none", fontSize: "12px" }}>
                        👁 View Map
                      </a>
                      <a href={`http://127.0.0.1:5000${selectedBriefing.chart_file_path}`} download={`Briefing_Map_${selectedBriefing.airport_code}_${selectedBriefing.flight_level}.gif`} className="btn-primary" style={{ textDecoration: "none", fontSize: "12px" }}>
                        📥 Download Map
                      </a>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        default:
          return <FlightPlanningView />;
      }
    }
  };

  return (
    <div className="app-container">
      {/* SIDEBAR */}
      <div className="sidebar">
        <div>
          <div className="logo-section">
            <span className="logo-icon">📡</span>
            <div className="logo-text">
              <h3>MET AVIATION</h3>
              <span>Bandaranaike Intl Airport</span>
            </div>
          </div>

          <div className="workspace-header">Operations workspace</div>
          <div className="workspace-title">
            {activeRole === "predictor" ? "Meteorological console" : "Pilot flight desk"}
          </div>

          <ul className="nav-menu">
            {activeRole === "predictor" ? (
              <>
                <li className={`nav-item ${activeTab === "dashboard" ? "active" : ""}`} onClick={() => setActiveTab("dashboard")}>
                  <span>📊</span> Dashboard
                </li>
                <li className={`nav-item ${activeTab === "forecasting" ? "active" : ""}`} onClick={() => setActiveTab("forecasting")}>
                  <span>🌤</span> Weather Forecasting
                </li>
                <li className={`nav-item ${activeTab === "maps" ? "active" : ""}`} onClick={() => setActiveTab("maps")}>
                  <span>🗺</span> Forecast Maps
                </li>
                <li className={`nav-item ${activeTab === "approvals" ? "active" : ""}`} onClick={() => setActiveTab("approvals")}>
                  <span>✔</span> Approval Center
                </li>
                <li className={`nav-item ${activeTab === "logs" ? "active" : ""}`} onClick={() => setActiveTab("logs")}>
                  <span>📜</span> Activity Logs
                </li>
              </>
            ) : (
              <>
                <li className={`nav-item ${activeTab === "flight-planning" ? "active" : ""}`} onClick={() => setActiveTab("flight-planning")}>
                  <span>✈</span> Flight Planning
                </li>
                <li className={`nav-item ${activeTab === "maps" ? "active" : ""}`} onClick={() => setActiveTab("maps")}>
                  <span>🗺</span> Forecast Maps
                </li>
                <li className={`nav-item ${activeTab === "documents" ? "active" : ""}`} onClick={() => setActiveTab("documents")}>
                  <span>📁</span> Documents
                </li>
              </>
            )}
          </ul>
        </div>

        <div className="sidebar-bottom">
          <div className="nav-item"><span>⚙</span> Settings</div>
          <div className="system-status">
            <div className="status-dot"></div>
            <div className="status-text">
              <h4>System operational</h4>
              <p>BIA Met data stream active</p>
            </div>
          </div>
        </div>
      </div>

      {/* CONTENT SHELL */}
      <div className="content-wrapper">
        <div className="topbar">
          <div className="station-info">
            <h2>VCCC - Colombo FIR</h2>
            <p>Bandaranaike International Airport / VCBI</p>
          </div>

          <div className="header-right">
            <div style={{ color: "#60a5fa", fontWeight: "bold", fontSize: "12px", background: "#10264a", padding: "6px 12px", borderRadius: "6px" }}>
              ⏱ {timeStr}
            </div>

            <div className="role-toggle-group">
              <button
                className={`role-btn ${activeRole === "pilot" ? "active" : ""}`}
                onClick={() => handleRoleChange("pilot")}
              >
                Pilot
              </button>
              <button
                className={`role-btn ${activeRole === "predictor" ? "active" : ""}`}
                onClick={() => handleRoleChange("predictor")}
              >
                Predictor
              </button>
            </div>

            <div className="user-profile">
              <div className="user-avatar">KS</div>
              <div className="user-name">
                K. Senanayake <span className="verified-badge">✔ Authorized user</span>
              </div>
            </div>
          </div>
        </div>

        <div className="main-viewport">
          {renderContentView()}
        </div>
      </div>
    </div>
  );
}

export default App;