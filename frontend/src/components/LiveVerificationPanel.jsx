import React, { useState, useEffect } from "react";
import axios from "axios";

const LiveVerificationPanel = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLiveVerification = async () => {
    try {
      setLoading(true);
      const res = await axios.get("http://localhost:5000/api/live-verification");
      setData(res.data);
      setError(null);
    } catch (err) {
      console.error("Error fetching live verification:", err);
      setError("Failed to fetch live verification data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLiveVerification();
    // Auto refresh every 5 minutes
    const interval = setInterval(fetchLiveVerification, 300000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="dashboard-section-card" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '150px' }}>
        <p style={{ color: "#64748b" }}>Loading Live Verification...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-section-card" style={{ borderColor: 'rgba(239, 68, 68, 0.3)' }}>
        <h3 style={{ color: '#f87171' }}>Live Verification Error</h3>
        <p style={{ color: "#64748b" }}>{error}</p>
      </div>
    );
  }

  if (data?.status === "waiting") {
    return (
      <div className="dashboard-section-card">
        <h3>Live Forecast Verification</h3>
        <p className="card-desc">Current VCBI conditions versus our models predictions</p>
        <div style={{ background: "rgba(245, 158, 11, 0.1)", border: "1px solid rgba(245, 158, 11, 0.2)", padding: "15px", borderRadius: "8px", marginTop: "15px" }}>
          <p style={{ color: "#fbbf24", margin: 0, fontWeight: 500 }}>⚠️ {data.message}</p>
          <div style={{ marginTop: "10px", fontSize: "14px", color: "#94a3b8" }}>
            <span>Live Time: {data.live_time}</span> | <span>Live Temp: {data.live_temp}°C</span>
          </div>
        </div>
      </div>
    );
  }

  // Define color logic based on error magnitude
  const getErrorColor = (errVal) => {
    const absErr = Math.abs(errVal);
    if (absErr <= 1.0) return "#10b981"; // Green - Excellent
    if (absErr <= 2.5) return "#f59e0b"; // Yellow - Acceptable
    return "#ef4444"; // Red - High Error
  };

  return (
    <div className="dashboard-section-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3>Live Forecast Verification</h3>
          <p className="card-desc">Current VCBI conditions versus our models predictions</p>
        </div>
        <button 
          onClick={fetchLiveVerification} 
          style={{ background: '#2563eb', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}
        >
          Refresh Live
        </button>
      </div>

      {data && data.status === "success" && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginTop: '20px' }}>
          
          {/* Temperature Comparison */}
          <div style={{ background: '#0f172a', padding: '20px', borderRadius: '12px', border: '1px solid #1e293b' }}>
            <h4 style={{ color: '#94a3b8', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '15px', marginTop: 0 }}>Temperature</h4>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ color: '#cbd5e1' }}>Predicted (Model)</span>
              <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>{data.predicted_temp}°C</span>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px', paddingBottom: '15px', borderBottom: '1px solid #1e293b' }}>
              <span style={{ color: '#cbd5e1' }}>Live Reality (METAR)</span>
              <span style={{ color: '#f8fafc', fontWeight: 'bold' }}>{data.live_temp}°C</span>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#64748b', fontSize: '13px' }}>Absolute Error</span>
              <span style={{ 
                color: getErrorColor(data.temp_error), 
                fontWeight: 'bold', 
                background: `${getErrorColor(data.temp_error)}20`,
                padding: '4px 8px',
                borderRadius: '4px'
              }}>
                {data.temp_error > 0 ? '+' : ''}{data.temp_error}°C
              </span>
            </div>
          </div>

          {/* Pressure Comparison */}
          <div style={{ background: '#0f172a', padding: '20px', borderRadius: '12px', border: '1px solid #1e293b' }}>
            <h4 style={{ color: '#94a3b8', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '15px', marginTop: 0 }}>Atmospheric Pressure</h4>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ color: '#cbd5e1' }}>Predicted (Model)</span>
              <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>{data.predicted_press} hPa</span>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px', paddingBottom: '15px', borderBottom: '1px solid #1e293b' }}>
              <span style={{ color: '#cbd5e1' }}>Live Reality (METAR)</span>
              <span style={{ color: '#f8fafc', fontWeight: 'bold' }}>{data.live_press} hPa</span>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#64748b', fontSize: '13px' }}>Absolute Error</span>
              <span style={{ 
                color: getErrorColor(data.press_error), 
                fontWeight: 'bold', 
                background: `${getErrorColor(data.press_error)}20`,
                padding: '4px 8px',
                borderRadius: '4px'
              }}>
                {data.press_error > 0 ? '+' : ''}{data.press_error} hPa
              </span>
            </div>
          </div>

        </div>
      )}
      
      {data && (
         <div style={{ marginTop: '15px', textAlign: 'right', color: '#64748b', fontSize: '12px' }}>
           Live Data from AviationWeather (VCBI) • As of {data.live_time}
         </div>
      )}
    </div>
  );
};

export default LiveVerificationPanel;
